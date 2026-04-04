# MCP Protocol Versions 📐

This note explains the practical differences between the protocol versions supported by this repo:

- `2024-11-05`
- `2025-03-26`
- `2025-06-18`
- `2025-11-25`

Default in this repo:

- `2025-11-25`

Official references:

- MCP releases: https://github.com/modelcontextprotocol/modelcontextprotocol/releases
- 2024-11-05 transports: https://modelcontextprotocol.io/specification/2024-11-05/basic/transports
- 2025-03-26 changelog: https://modelcontextprotocol.io/specification/2025-03-26/changelog
- 2025-06-18 changelog: https://modelcontextprotocol.io/specification/2025-06-18/changelog
- 2025-11-25 changelog: https://modelcontextprotocol.io/specification/2025-11-25/changelog

## Quick Summary

| Version | Main idea |
| --- | --- |
| `2024-11-05` | Early stable MCP with stdio and legacy HTTP+SSE transport |
| `2025-03-26` | Big revision: Streamable HTTP, OAuth authorization, batching, tool annotations, completions |
| `2025-06-18` | Tightening revision: no batching, structured tool output, elicitation, resource links, stronger HTTP header rules |
| `2025-11-25` | Latest version used here; continues the modern MCP model and is the default in this repo |

## Version By Version

### `2024-11-05`

This is the oldest stable version in the repo.

Key characteristics:

- supports `stdio`
- supports legacy `HTTP + SSE`
- predates the big 2025 transport and auth updates

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

This is the first major modern MCP revision.

What changed vs `2024-11-05`:

- replaces legacy `HTTP + SSE` with `Streamable HTTP`
- adds OAuth 2.1 authorization framework
- adds JSON-RPC batching
- adds tool annotations
- adds completions capability
- adds progress `message`
- adds audio content support

Simple capability example:

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

This revision keeps the 2025 model but tightens important protocol details.

What changed vs `2025-03-26`:

- removes JSON-RPC batching
- adds structured tool output
- adds elicitation
- adds resource links in tool results
- strengthens OAuth and resource server rules
- requires `MCP-Protocol-Version` on subsequent HTTP requests
- adds more human-friendly `title` fields

Simple structured output example:

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

### `2025-11-25`

This is the default and latest version used by this repo.

Practical guidance:

- use this version by default
- prefer this version for new demos and interoperability tests
- downgrade only when you specifically need an older transport or behavior set

Simple initialize example:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-11-25",
    "capabilities": {},
    "clientInfo": {
      "name": "demo-client",
      "version": "1.0"
    }
  }
}
```

Simple header example:

```json
{
  "headers": {
    "MCP-Protocol-Version": "2025-11-25"
  }
}
```

## Practical Choice

If you are choosing one version for demos:

- use `2024-11-05` only when you want to demonstrate legacy SSE-style behavior
- use `2025-03-26` when you want to show the first big modern MCP revision
- use `2025-06-18` when you want a stable intermediate 2025 revision
- use `2025-11-25` by default
