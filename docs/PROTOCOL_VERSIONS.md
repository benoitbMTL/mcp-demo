# MCP Protocol Versions 📐

This note explains the practical differences between the protocol versions exposed by this repo:

- `2025-11-05`
- `2025-06-18`
- `2025-03-26`
- `2024-11-05`

## Important Note

As of April 4, 2026, the public upstream MCP releases documented by the official project are:

- `2024-11-05`
- `2025-03-26`
- `2025-06-18`
- `2025-11-25`

I did not find an official public specification page for `2025-11-05`. In this repo, `2025-11-05` should therefore be treated as a local compatibility value, not as a documented upstream stable revision.

Official references:

- MCP releases: https://github.com/modelcontextprotocol/modelcontextprotocol/releases
- 2025-03-26 changelog: https://modelcontextprotocol.io/specification/2025-03-26/changelog
- 2025-06-18 changelog: https://modelcontextprotocol.io/specification/2025-06-18/changelog
- 2024-11-05 transports: https://modelcontextprotocol.io/specification/2024-11-05/basic/transports

## Quick Summary

| Version | Main idea |
| --- | --- |
| `2024-11-05` | Early stable MCP with stdio and legacy HTTP+SSE transport |
| `2025-03-26` | Big revision: OAuth-based authorization, Streamable HTTP, batching, tool annotations, completions |
| `2025-06-18` | Tightening revision: remove batching, add structured tool output, elicitation, resource links, stricter HTTP version headers |
| `2025-11-05` | No official public spec found; in this repo, treat it as a compatibility target newer than `2025-06-18` but not formally documented upstream |

## Version By Version

### `2024-11-05`

This is the oldest stable version used here.

Key characteristics:

- supports `stdio`
- supports legacy `HTTP + SSE`
- does not yet include the large 2025 transport and auth changes

Simple initialize example:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "demo-client",
      "version": "1.0"
    }
  }
}
```

Legacy transport shape:

```json
{
  "transport": "HTTP + SSE",
  "receive": "GET /sse",
  "send": "POST /messages"
}
```

### `2025-03-26`

This is the first major 2025 break.

What changed vs `2024-11-05`:

- adds OAuth 2.1 authorization framework
- replaces legacy `HTTP + SSE` with `Streamable HTTP`
- adds JSON-RPC batching
- adds tool annotations
- adds completions capability
- adds `message` in progress notifications
- adds audio content support

Simple capability example with completions:

```json
{
  "capabilities": {
    "completions": {}
  }
}
```

Simple tool annotation example:

```json
{
  "name": "read_file",
  "annotations": {
    "readOnlyHint": true
  }
}
```

Simple batch example:

```json
[
  { "jsonrpc": "2.0", "id": 1, "method": "tools/list" },
  { "jsonrpc": "2.0", "id": 2, "method": "resources/list" }
]
```

### `2025-06-18`

This revision keeps the general 2025 architecture but tightens several parts of the protocol.

What changed vs `2025-03-26`:

- removes JSON-RPC batching
- adds structured tool output
- adds elicitation
- adds resource links in tool results
- strengthens OAuth/resource server rules
- requires `MCP-Protocol-Version` on subsequent HTTP requests
- adds `title` fields in several places for human-friendly display

Simple structured tool output example:

```json
{
  "content": [
    {
      "type": "text",
      "text": "File read successfully"
    }
  ],
  "structuredContent": {
    "path": "/tmp/demo.txt",
    "size": 128
  }
}
```

Simple resource link example:

```json
{
  "content": [
    {
      "type": "resource_link",
      "uri": "file:///tmp/report.txt",
      "name": "report.txt"
    }
  ]
}
```

Simple HTTP header example:

```json
{
  "headers": {
    "MCP-Protocol-Version": "2025-06-18"
  }
}
```

Simple elicitation example:

```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "method": "elicitation/create",
  "params": {
    "message": "Which environment should I use?"
  }
}
```

### `2025-11-05`

This version is exposed by this repo, but I could not verify it in the official public MCP release pages.

Practical guidance:

- if you need an officially documented stable version, prefer `2025-06-18` or `2025-11-25`
- if you need to stay aligned with this repo's local server setting, `2025-11-05` may still be useful for testing
- do not assume upstream interoperability from `2025-11-05` without checking the exact server/client implementation

Minimal example in this repo:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "demo-client",
      "version": "1.0"
    }
  }
}
```

## Practical Choice

If you are choosing one version for demos:

- use `2024-11-05` only when you want to demonstrate legacy SSE-style behavior
- use `2025-03-26` when you want to show the first big modern MCP revision
- use `2025-06-18` when you want the best officially documented stable version among the values currently exposed by this repo
- use `2025-11-05` only if you specifically need to match this repo's local compatibility setting
