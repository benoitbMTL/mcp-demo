#!/bin/sh
set -eu

python /app/server/server.py &
MCP_PID=$!

python /app/apps/web/run_web_ui.py &
WEB_UI_PID=$!

cleanup() {
  kill "$MCP_PID" "$WEB_UI_PID" 2>/dev/null || true
}

trap cleanup INT TERM

EXIT_CODE=0

while kill -0 "$MCP_PID" 2>/dev/null && kill -0 "$WEB_UI_PID" 2>/dev/null; do
  sleep 1
done

if ! kill -0 "$MCP_PID" 2>/dev/null; then
  wait "$MCP_PID" || EXIT_CODE=$?
fi

if ! kill -0 "$WEB_UI_PID" 2>/dev/null; then
  wait "$WEB_UI_PID" || EXIT_CODE=$?
fi

cleanup
wait "$MCP_PID" 2>/dev/null || true
wait "$WEB_UI_PID" 2>/dev/null || true

exit "$EXIT_CODE"
