#!/usr/bin/env bash
set -euo pipefail

MCP_URL="http://localhost:7000/mcp"
ACCEPT_HEADER="application/json, text/event-stream"

print_step() {
  echo
  echo "============================================================"
  echo "$1"
  echo "============================================================"
}

print_info()  { echo "[INFO] $1"; }
print_error() { echo "[ERROR] $1" >&2; }

get_host_header_value() {
  # Extract host:port from MCP_URL (no path)
  echo "$MCP_URL" | sed -E 's#^https?://##; s#/.*$##'
}

print_step "STEP 0 - Pre-flight checks"
echo
command -v curl >/dev/null 2>&1 || { print_error "curl is required but not found."; exit 1; }
command -v jq   >/dev/null 2>&1 || { print_error "jq is required but not found."; exit 1; }
print_info "Using MCP endpoint: $MCP_URL"
print_info "Using Accept: $ACCEPT_HEADER"

print_step "STEP 1 - JSON-RPC initialize (show request headers + JSON body)"
echo
INIT_JSON='{
  "jsonrpc":"2.0",
  "id":0,
  "method":"initialize",
  "params":{
    "protocolVersion":"2025-11-25",
    "capabilities":{},
    "clientInfo":{"name":"bash","version":"1.0"}
  }
}'

print_info "Request headers (initialize):"
echo "POST /mcp HTTP/1.1"
echo "Host: $(get_host_header_value)"
echo "Content-Type: application/json"
echo "Accept: $ACCEPT_HEADER"
echo

print_info "Request body (initialize):"
echo "$INIT_JSON" | jq .
echo

print_step "STEP 2 - Send initialize, capture response headers, extract Mcp-Session-Id"
echo
# Capture headers+body, then extract the session id from headers (case-insensitive)
INIT_RESPONSE="$(curl -sS -D - \
  -H "Content-Type: application/json" \
  -H "Accept: $ACCEPT_HEADER" \
  "$MCP_URL" \
  -d "$INIT_JSON")"

SID="$(printf '%s' "$INIT_RESPONSE" \
  | tr -d '\r' \
  | awk -F': ' 'tolower($1)=="mcp-session-id"{print $2; exit}')"

if [[ -z "${SID}" ]]; then
  print_error "Failed to extract Mcp-Session-Id from initialize response headers."
  print_error "Full initialize response (headers+body) below:"
  echo "$INIT_RESPONSE" >&2
  exit 1
fi

print_info "Session established."
print_info "Mcp-Session-Id: $SID"
echo

print_step "STEP 3 - JSON-RPC tools/list (show request headers + JSON body)"
echo
TOOLS_LIST_JSON='{
  "jsonrpc":"2.0",
  "id":1,
  "method":"tools/list"
}'

print_info "Request headers (tools/list):"
echo "POST /mcp HTTP/1.1"
echo "Host: $(get_host_header_value)"
echo "Content-Type: application/json"
echo "Accept: $ACCEPT_HEADER"
echo "Mcp-Session-Id: $SID"
echo

print_info "Request body (tools/list):"
echo "$TOOLS_LIST_JSON" | jq .
echo

print_step "STEP 4 - Send tools/list and print ONLY tool names"
echo

TMP_HEADERS="$(mktemp)"
TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_HEADERS" "$TMP_BODY"' EXIT

curl -sS -N -D "$TMP_HEADERS" -o "$TMP_BODY" \
  -H "Content-Type: application/json" \
  -H "Accept: $ACCEPT_HEADER" \
  -H "Mcp-Session-Id: $SID" \
  "$MCP_URL" \
  -d "$TOOLS_LIST_JSON"

CT="$(grep -i '^Content-Type:' "$TMP_HEADERS" | head -n1 | tr -d '\r' || true)"
print_info "Response $CT"
echo

# Prints tool names from JSON on stdin.
# If the server returned an error object, print it to stderr and exit non-zero.
print_tool_names_from_json() {
  jq -r '
    if .error then
      "ERROR: " + (.error.message // (.error|tostring))
    elif (.result.tools? != null) then
      .result.tools[].name
    elif (.tools? != null) then
      .tools[].name
    else
      "ERROR: Unexpected JSON shape"
    end
  '
}

highlight_tool_list() {
  # Reads tool names from stdin and prints a highlighted list.
  # If stdin is empty, prints a warning-like message.
  local tools
  tools="$(cat)"

  if [[ -z "$tools" ]]; then
    print_error "No tool names found in response."
    return 1
  fi

  local count
  count="$(printf '%s\n' "$tools" | grep -c '.*' || true)"

  echo
  echo "==================== TOOLS LIST (${count}) ===================="
  # Numbered list
  printf '%s\n' "$tools" | nl -w2 -s'. '
  echo "==============================================================="
  echo
}

# If the response is SSE, extract data lines; otherwise parse body as JSON.
if head -n 1 "$TMP_BODY" | grep -qE '^(event:|data:)\s'; then
  print_info "Detected SSE response; extracting JSON from 'data:' lines."
  set +e
  OUT="$(sed -n 's/^data: //p' "$TMP_BODY" | print_tool_names_from_json)"
  STATUS=$?
  set -e

  if [[ $STATUS -ne 0 ]]; then
    print_error "jq failed to parse JSON from SSE data lines."
    print_error "Raw SSE body saved at: $TMP_BODY"
    exit 1
  fi

  if echo "$OUT" | grep -q '^ERROR:'; then
    print_error "$OUT"
    exit 1
  fi

  # Highlighted output
  printf '%s\n' "$OUT" | highlight_tool_list

else
  print_info "Detected JSON response; parsing directly."
  set +e
  OUT="$(cat "$TMP_BODY" | print_tool_names_from_json)"
  STATUS=$?
  set -e

  if [[ $STATUS -ne 0 ]]; then
    print_error "jq failed to parse JSON response."
    print_error "Raw body saved at: $TMP_BODY"
    exit 1
  fi

  if echo "$OUT" | grep -q '^ERROR:'; then
    print_error "$OUT"
    exit 1
  fi

  # Highlighted output
  printf '%s\n' "$OUT" | highlight_tool_list
fi
