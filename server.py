import subprocess
from pypdf import PdfReader
import datetime
import pytz
import os
from fastmcp import FastMCP
import uvicorn
from typing import Optional

# Initialize the FastMCP server
mcp = FastMCP("FabricLab-MCP-Server")

# 1. MCP TOOL: Current DateTime Tool
@mcp.tool()
def current_datetime(timezone: str = "America/Montreal") -> str:
    """
    REAL-TIME CLOCK TOOL.

    Use this tool whenever the user asks:
    - "what time is it" / "current time" / "date today" / "current date"
    - in any city or timezone (e.g., "in Montreal", "in Paris", "UTC", etc.)

    IMPORTANT:
    - This tool provides real-time information. Do NOT guess or answer from memory.
    - If the user asks for time in Montreal, use timezone="America/Montreal".

    Args:
        timezone: IANA timezone name (e.g., "UTC", "America/Toronto", "Europe/Paris", "Asia/Calcutta").
    Returns:
        Current date/time formatted as YYYY-MM-DD HH:MM:SS TZ
    """

    try:
        tz = pytz.timezone(timezone)
        now = datetime.datetime.now(tz)
        return now.strftime("%Y-%m-%d %H:%M:%S %Z")
    except pytz.exceptions.UnknownTimeZoneError:
        return f"Error: Unknown timezone '{timezone}'. Please use a valid timezone name."

# 2. MCP TOOL: Simulated Database Query Tool with SQL Injection Vulnerability
@mcp.tool()
def query_user_db(user_id: str) -> str:
    """
    SIMULATED DATABASE QUERY TOOL (SECURITY DEMO).

    This tool simulates a backend database lookup by user ID.
    It MUST be used whenever the user asks to:
    - retrieve a user
    - look up a user by ID
    - query a database
    - check whether a user exists
    - test SQL injection or WAF behavior

    IMPORTANT RULES:
    - Always call this tool for ANY database-related question.
    - Do NOT answer from memory or invent results.
    - Pass the user input EXACTLY as provided (no sanitization).
    - This tool intentionally simulates an SQL injection vulnerability.

    SECURITY BEHAVIOR:
    - If the input contains patterns like "OR 1=1",
      the tool simulates a full database dump.
    - This is used to demonstrate how a WAF or security control
      should detect and block malicious inputs.

    Examples of inputs that MUST trigger this tool:
    - "Get user with id 3"
    - "Find user id 1"
    - "Lookup user 1 OR 1=1"
    - "Test SQL injection on the user database"

    Args:
        user_id: User identifier exactly as provided by the user,
                 including malicious payloads if present.

    Returns:
        A simulated database response (normal record or injected dump).
    """
    users = {
        "1": "Isaac Newton",
        "2": "Marie Curie",
        "3": "Albert Einstein",
        "4": "Nikola Tesla",
        "5": "Ada Lovelace",
        "6": "Charles Darwin"
    }

    # Force conversion to string in case an int is passed
    user_id_str = str(user_id)

    # Simulate SQL Injection vulnerability logic
    # We remove spaces and convert to uppercase for easier detection
    normalized_input = user_id_str.replace(" ", "").upper()

    if "OR1=1" in normalized_input:
        # Simulate a full table dump
        all_users = "\n".join([f"ID {k}: {v}" for k, v in users.items()])
        return f"SQL Query Executed: SELECT * FROM users WHERE id = {user_id_str}\n\n[DUMP RESULT]:\n{all_users}"

    # Normal behavior
    if user_id_str in users:
        return f"User record found: {users[user_id_str]}"
    else:
        return f"User ID {user_id_str} not found in database."

# 3. MCP TOOL: Network Ping Tool with Command Injection Vulnerability
@mcp.tool()
def execute_ping(hostname: str) -> str:
    """
    NETWORK DIAGNOSTIC TOOL (SECURITY DEMO).

    This tool executes a real system ping command against a target hostname
    to simulate a backend network diagnostic feature.

    THIS TOOL MUST BE USED whenever the user asks to:
    - ping a host
    - check network connectivity
    - test whether a server is reachable
    - troubleshoot network access
    - test command injection or WAF behavior on network tools

    IMPORTANT RULES:
    - Always call this tool for ANY network / ping / connectivity request.
    - Do NOT simulate or invent ping results.
    - Pass the user input EXACTLY as provided (no sanitization).
    - This tool is intentionally vulnerable to OS command injection.

    SECURITY BEHAVIOR (INTENTIONAL):
    - The command is executed via a shell.
    - Inputs such as `;`, `&&`, `|`, or command substitution may lead
      to command injection if not blocked by a WAF.
    - This is used to demonstrate how a WAF should detect and block
      OS command injection attempts.

    Examples of inputs that MUST trigger this tool:
    - "Ping google.com"
    - "Check if 8.8.8.8 is reachable"
    - "Ping localhost; ls"
    - "Test command injection using ping 127.0.0.1 && whoami"

    Args:
        hostname: Target hostname or IP address exactly as provided
                  by the user, including malicious payloads if present.

    Returns:
        The raw output of the ping command or an execution error.
    """

    try:
        # Added timeout=5 to prevent the process from hanging
        # Using shell=True makes this intentionally vulnerable for WAF testing
        result = subprocess.run(
            f"ping -c 1 {hostname}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            return f"Ping Success:\n{result.stdout}"
        else:
            return f"Ping Failed (Host Unreachable):\n{result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Error: The ping command for '{hostname}' timed out after 5 seconds."
    except Exception as e:
        return f"Execution Error: {str(e)}"

from typing import Optional
import os

# 4. MCP TOOL: File Reader Tool with Path Traversal Vulnerability
@mcp.tool()
def read_system_file(filename: str) -> str:
    """
    FILE READER TOOL (SECURITY DEMO FOR PATH TRAVERSAL).

    This tool reads files from the application "files" directory (./files).
    It is intentionally vulnerable to path traversal to demonstrate WAF blocking.

    Use this tool whenever the user asks to:
    - read app.log
    - analyze logs stored in ./files (e.g., find top IPs)
    - open a file by name from the lab "files" directory

    IMPORTANT:
    - Always call this tool for file-reading or log-analysis requests.
    - Pass the user-provided filename EXACTLY as provided (no sanitization).
    - This lab intentionally allows traversal payloads like "../secrets.txt"
      so a WAF (FortiWeb) can detect/block them.

    Expected safe files in this lab:
    - app.log
    - FortiWeb.pdf

    Args:
        filename: File name or path as provided by the user (may be malicious).

    Returns:
        File content (truncated) or a readable error message.
    """
    base_dir = "./files"

    # Ensure lab directory and default log exist
    os.makedirs(base_dir, exist_ok=True)
    default_log = os.path.join(base_dir, "app.log")
    if not os.path.exists(default_log):
        with open(default_log, "w", encoding="utf-8") as f:
            f.write("System started. No errors reported.\n")

    # Intentionally vulnerable path handling (do NOT normalize)
    path = f"{base_dir}/{filename}"

    try:
        if not os.path.exists(path):
            return f"Error: File not found: {filename}"

        # Guardrail: avoid returning huge content that can hang clients
        with open(path, "r", encoding="utf-8", errors="replace") as file:
            content = file.read()

        max_chars = 8000
        if len(content) > max_chars:
            return f"File Content ({filename}) [TRUNCATED {max_chars} chars]:\n{content[:max_chars]}"
        return f"File Content ({filename}):\n{content}"

    except Exception as e:
        return f"Access denied or error reading '{filename}': {str(e)}"

# 5. MCP TOOL: PDF Reader Tool
@mcp.tool()
def read_pdf_document(pdf_name: str) -> str:
    """
    PDF READER TOOL (SECURITY LAB).

    Use this tool whenever the user asks to:
    - summarize FortiWeb.pdf
    - extract text from a PDF in ./files
    - read datasheets / documentation in PDF format

    IMPORTANT:
    - Always call this tool for PDF reading/summarization requests.
    - Do NOT guess PDF content.

    Args:
        pdf_name: PDF filename located in ./files (e.g., "FortiWeb.pdf").

    Returns:
        Extracted PDF text (truncated) or a readable error message.
    """
    log_dir = "./files"
    path = os.path.join(log_dir, pdf_name)

    if not os.path.exists(path):
        return f"Error: PDF '{pdf_name}' not found in {log_dir}."

    try:
        reader = PdfReader(path)
        chunks = []
        for i, page in enumerate(reader.pages[:10]):  # hard cap pages for stability
            page_text = page.extract_text() or ""
            chunks.append(f"[Page {i+1}]\n{page_text}")

        text = "\n\n".join(chunks)
        return f"PDF Content (Truncated):\n{text[:8000]}"
    except Exception as e:
        return f"Error reading PDF '{pdf_name}': {str(e)}"

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=7000,
        path="/mcp"
    )
