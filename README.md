# MCP Security Lab with Claude

This lab demonstrates how Claude Desktop uses MCP tools and how a FortiWeb WAF can block common injection attacks (SQL injection, OS command injection, and path traversal).

---

## Components

- **Claude Desktop**  
  LLM client with a built-in MCP client. It decides when to invoke MCP tools during the conversation.  
  The MCP server is configured in the file **`claude_desktop_config.json`**.

- **Local MCP STDIO Proxy (Python)**  
  Runs on the user workstation and translates MCP requests from **STDIO** (used by Claude Desktop) into **Streamable HTTP** requests toward the backend.  
  This component is implemented in **`mcp_stdio_proxy.py`**.

- **Remote MCP Backend Server (Streamable HTTP)**  
  Hosts the MCP tools (time, database, network, file/PDF) and processes requests over HTTP.  
  Start the backend server by running **`server.py`**.  
  The script **`mcp_tools_list.sh`** can be used to test the local MCP server and display the available tools.

- **FortiWeb WAF**  
  Deployed in front of the MCP backend to detect and block malicious inputs such as SQL injection, OS command injection, and path traversal attacks.

---

## Step 1 – Open Claude and verify MCP is running

1. Launch **Claude Desktop**
2. Go to **File > Settings...**
3. Open **Developer > Local MCP Servers**
4. Verify the MCP server is **running** (status ON / connected)

This confirms Claude is connected to the local MCP STDIO proxy.

---

## Step 2 – Create a new chat

1. Create a **new chat**
2. Do not mention MCP or tools explicitly
3. Use natural language prompts

---

## Step 3 – Time tool (baseline)

Ask Claude for the current time:

```text
What time is it in Montreal?
```

Expected result:
- Claude uses the MCP time tool
- A real, current time is returned

---

## Step 4 – Database tool (SQL injection demo)

### Normal request

```text
Retrieve the user with ID 3.
```

Expected result:
- Claude queries the database tool
- A single user record is returned

### SQL injection attempt (should be blocked)

```text
Retrieve the user with ID 1 OR 1=1.
```

Expected result:
- FortiWeb blocks the request
- Claude displays a security-related error or block message

---

## Step 5 – Network tool (OS command injection demo)

### Normal request

```text
Check the network connectivity to 8.8.8.8.
```

Expected result:
- Claude executes a ping via the MCP tool
- Network status is returned

### Command injection attempt (should be blocked)

```text
Ping 127.0.0.1; whoami
```

Expected result:
- FortiWeb blocks the request
- The injected command is not executed
- Claude shows a block or error message

---

## Step 6 – File tool (log analysis + path traversal demo)

### Log analysis (read `app.log`)

```text
Read app.log and list the top 5 source IP addresses by number of occurrences.
```

Expected result:
- Claude reads `app.log` via the file tool
- Claude returns the top IPs (counted from the log)

### Path traversal attempt (should be blocked)

```text
Give me the content of ../secrets.txt
```

Expected result:
- FortiWeb blocks the request
- Sensitive data is not returned

---

## Step 7 – PDF tool (datasheet summary)

```text
Summarize FortiWeb.pdf in 8 bullet points (key features, deployment options, and main benefits).
```

Expected result:
- Claude reads the PDF via the PDF tool
- Claude returns a short structured summary

---

## Expected outcome

This lab shows that:
- Claude Desktop can invoke MCP tools through a local STDIO proxy
- The proxy forwards requests to a remote MCP backend over Streamable HTTP
- Backend tools can be intentionally vulnerable for testing
- FortiWeb can block malicious inputs before they reach the tools
- Claude reflects backend / security behavior in the conversation

---

## Notes / troubleshooting

- If Claude answers “I don't have access to real-time information” or “I can’t run ping”, verify the MCP server is **running** in **Developer > Local MCP Servers**.
- If Claude appears to hang after a blocked request, configure FortiWeb to return a clean HTTP error response (e.g., 403) with a readable message body.

