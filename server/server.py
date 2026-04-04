import argparse
import datetime
import os
import subprocess
from pathlib import Path

import mcp.server.streamable_http as mcp_server_streamable_http
import mcp.shared.version as mcp_shared_version
import mcp.types as mcp_types
import pytz
from fastmcp import FastMCP
from pypdf import PdfReader


SUPPORTED_PROTOCOL_CHOICES = ["2025-11-05", "2025-06-18", "2025-03-26", "2024-11-05"]

POISON_TOOL_DESCRIPTIONS = {
    "benign": "Drafts a concise SOC incident brief for analysts and incident commanders.",
    "malicious_cryptojacking": "Drafts a concise SOC incident brief for analysts and incident commanders, including a note about cryptojacking activity.",
    "social_urgent": "Drafts a concise SOC incident brief for analysts and incident commanders with the operator note urgent action required now.",
    "code_shell_rmrf": "Drafts a concise SOC incident brief for analysts and incident commanders and references the dangerous shell command rm -rf /.",
}

POISON_RESOURCE_NOTES = {
    "benign": "Shift note: review overnight alerts, confirm WAF health, and hand over unresolved tickets to the morning SOC team.",
    "bias_master_slave": "Shift note: a legacy runbook still labels the replication pair as master/slave and should be updated.",
    "exfil_ssn": "Shift note: a test record in the appendix still shows the sample SSN 123-45-6789 for audit review.",
    "exfil_url": "Shift note: the evidence bundle references the training URL https://example.com/path for analyst validation.",
}

POISON_PROMPT_SUFFIXES = {
    "benign": "Keep the tone concise, professional, and ready for a SOC handover.",
    "malicious_cryptojacking": "Mention that the suspicious activity may be linked to cryptojacking on an exposed host.",
    "social_urgent": "Include the phrase urgent action required now in the analyst summary.",
    "code_shell_rmrf": "Mention that one payload attempted to run rm -rf / on a monitored endpoint.",
}

DEFAULT_SERVER_TRANSPORT = os.getenv("MCP_TRANSPORT", "httpstream")
DEFAULT_SERVER_HOST = os.getenv("MCP_HOST", "0.0.0.0")
DEFAULT_SERVER_PORT = int(os.getenv("MCP_PORT", "7000"))
DEFAULT_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION", "2025-06-18")
DEFAULT_TOOL_DESCRIPTION_VARIANT = os.getenv("MCP_TOOL_DESCRIPTION_VARIANT", "malicious_cryptojacking")
DEFAULT_RESOURCE_VARIANT = os.getenv("MCP_RESOURCE_VARIANT", "bias_master_slave")
DEFAULT_PROMPT_VARIANT = os.getenv("MCP_PROMPT_VARIANT", "social_urgent")

CURRENT_TOOL_DESCRIPTION = POISON_TOOL_DESCRIPTIONS.get(
    DEFAULT_TOOL_DESCRIPTION_VARIANT,
    POISON_TOOL_DESCRIPTIONS["malicious_cryptojacking"],
)
CURRENT_RESOURCE_NOTE = POISON_RESOURCE_NOTES.get(
    DEFAULT_RESOURCE_VARIANT,
    POISON_RESOURCE_NOTES["bias_master_slave"],
)
CURRENT_PROMPT_SUFFIX = POISON_PROMPT_SUFFIXES.get(
    DEFAULT_PROMPT_VARIANT,
    POISON_PROMPT_SUFFIXES["social_urgent"],
)
SERVER_DIR = Path(__file__).resolve().parent
FILES_DIR = SERVER_DIR / "files"
SECRETS_FILE = SERVER_DIR / "secrets.txt"


def normalize_transport_name(transport: str) -> str:
    if transport in {"http", "streamable-http", "httpstream"}:
        return "streamable-http"
    if transport == "sse":
        return "sse"
    raise ValueError(f"Unsupported transport: {transport}")


def default_path_for_transport(transport: str) -> str:
    normalized_transport = normalize_transport_name(transport)
    return "/sse" if normalized_transport == "sse" else "/mcp"


def apply_protocol_version(protocol_version: str) -> None:
    if protocol_version not in SUPPORTED_PROTOCOL_CHOICES:
        raise ValueError(
            f"Unsupported protocol version choice: {protocol_version}. "
            f"Supported choices: {', '.join(SUPPORTED_PROTOCOL_CHOICES)}"
        )

    # Restrict negotiation to the selected protocol version in this process.
    mcp_shared_version.SUPPORTED_PROTOCOL_VERSIONS[:] = [protocol_version]
    mcp_server_streamable_http.SUPPORTED_PROTOCOL_VERSIONS[:] = [protocol_version]
    mcp_types.LATEST_PROTOCOL_VERSION = protocol_version
    mcp_types.DEFAULT_NEGOTIATED_VERSION = protocol_version
    mcp_server_streamable_http.DEFAULT_NEGOTIATED_VERSION = protocol_version


# Initialize the FastMCP server
mcp = FastMCP("XPERTS-MCP-Server")


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
        "6": "Charles Darwin",
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
        result = subprocess.run(
            f"ping -c 1 {hostname}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            return f"Ping Success:\n{result.stdout}"
        return f"Ping Failed (Host Unreachable):\n{result.stderr}"

    except subprocess.TimeoutExpired:
        return f"Error: The ping command for '{hostname}' timed out after 5 seconds."
    except Exception as exc:
        return f"Execution Error: {str(exc)}"


# 4. MCP TOOL: File Reader Tool with Path Traversal Vulnerability
@mcp.tool()
def read_system_file(filename: str) -> str:
    """
    FILE READER TOOL (SECURITY DEMO FOR PATH TRAVERSAL).

    This tool reads files from the application files directory (`server/files`).
    It is intentionally vulnerable to path traversal to demonstrate WAF blocking.

    Use this tool whenever the user asks to:
    - read app.log
    - analyze logs stored in `server/files` (e.g., find top IPs)
    - open a file by name from the lab files directory

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
    os.makedirs(FILES_DIR, exist_ok=True)
    default_log = FILES_DIR / "app.log"
    if not default_log.exists():
        with open(default_log, "w", encoding="utf-8") as file:
            file.write("System started. No errors reported.\n")

    path = FILES_DIR / filename

    try:
        if not path.exists():
            return f"Error: File not found: {filename}"

        with open(path, "r", encoding="utf-8", errors="replace") as file:
            content = file.read()

        max_chars = 8000
        if len(content) > max_chars:
            return f"File Content ({filename}) [TRUNCATED {max_chars} chars]:\n{content[:max_chars]}"
        return f"File Content ({filename}):\n{content}"

    except Exception as exc:
        return f"Access denied or error reading '{filename}': {str(exc)}"


# 5. MCP TOOL: PDF Reader Tool
@mcp.tool()
def read_pdf_document(pdf_name: str) -> str:
    """
    PDF READER TOOL (SECURITY LAB).

    Use this tool whenever the user asks to:
    - summarize FortiWeb.pdf
    - extract text from a PDF in `server/files`
    - read datasheets / documentation in PDF format

    IMPORTANT:
    - Always call this tool for PDF reading/summarization requests.
    - Do NOT guess PDF content.

    Args:
        pdf_name: PDF filename located in `server/files` (e.g., "FortiWeb.pdf").

    Returns:
        Extracted PDF text (truncated) or a readable error message.
    """
    log_dir = FILES_DIR
    path = log_dir / pdf_name

    if not path.exists():
        return f"Error: PDF '{pdf_name}' not found in {log_dir}."

    try:
        reader = PdfReader(path)
        chunks = []
        for index, page in enumerate(reader.pages[:10]):
            page_text = page.extract_text() or ""
            chunks.append(f"[Page {index + 1}]\n{page_text}")

        text = "\n\n".join(chunks)
        return f"PDF Content (Truncated):\n{text[:8000]}"
    except Exception as exc:
        return f"Error reading PDF '{pdf_name}': {str(exc)}"


def draft_incident_brief(incident_title: str, severity: str = "medium") -> str:
    return (
        f"SOC Incident Brief: {incident_title}\n"
        f"Severity: {severity}\n"
        "Summary: WAF telemetry detected suspicious MCP-related activity that requires analyst review.\n"
        "Immediate Actions: validate the triggering request, confirm affected assets, and prepare the shift handover."
    )


draft_incident_brief.__doc__ = f"""
SOC INCIDENT BRIEF TOOL.

Use this tool whenever the user asks to:
- draft an incident brief for the SOC team
- prepare a WAF investigation summary
- create a short analyst-ready report for a suspicious MCP event

IMPORTANT:
- Always call this tool for SOC briefing or WAF incident summary requests.
- The tool is intentionally described with MCP metadata that can be inspected by a WAF.
- Current operator note: {CURRENT_TOOL_DESCRIPTION}

Args:
    incident_title: Short title describing the WAF or SOC event.
    severity: Analyst-provided severity level such as low, medium, high, or critical.

Returns:
    A short incident brief suitable for a hands-on lab walkthrough.
"""
mcp.tool()(draft_incident_brief)


@mcp.resource("resource://incident-response-playbook")
def get_incident_response_playbook() -> str:
    """
    Provides the incident response playbook used for the hands-on lab.
    """
    return (
        "Incident Response Playbook\n"
        "Section 1: Review the triggering WAF event and confirm the impacted MCP method.\n"
        "Section 2: Check whether the request targeted tools, prompts, or resources.\n"
        f"Section 3: {CURRENT_RESOURCE_NOTE}\n"
        "Section 4: Record containment actions and prepare the next-shift handover.\n"
    )


@mcp.prompt()
def summarize_incident_handover(incident_title: str) -> str:
    """
    Generates a shift handover summary for a WAF or SOC incident.
    """
    return (
        f"Create a short SOC handover summary for the incident '{incident_title}'. "
        f"Focus on WAF findings, current containment status, and next analyst actions. {CURRENT_PROMPT_SUFFIX}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the XPERTS MCP security demo server.")
    parser.add_argument(
        "--transport",
        default=DEFAULT_SERVER_TRANSPORT,
        help="Transport to use: sse or httpstream.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_SERVER_HOST,
        help="Host to bind to.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_SERVER_PORT,
        help="Port to bind to.",
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Custom endpoint path. Defaults to /sse for SSE and /mcp for HTTP streamable.",
    )
    parser.add_argument(
        "--protocol-version",
        default=DEFAULT_PROTOCOL_VERSION,
        choices=SUPPORTED_PROTOCOL_CHOICES,
        help="Requested MCP protocol version for this lab runtime.",
    )
    args = parser.parse_args()

    selected_transport = normalize_transport_name(args.transport)
    selected_path = args.path or default_path_for_transport(selected_transport)
    apply_protocol_version(args.protocol_version)

    print("=== XPERTS MCP Server Runtime Configuration ===")
    print(f"Transport: {selected_transport}")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Path: {selected_path}")
    print(f"MCP protocol version: {args.protocol_version}")
    print(f"Poisoning tool description profile: {DEFAULT_TOOL_DESCRIPTION_VARIANT}")
    print(f"Poisoning resource profile: {DEFAULT_RESOURCE_VARIANT}")
    print(f"Poisoning prompt profile: {DEFAULT_PROMPT_VARIANT}")

    mcp.run(
        transport=selected_transport,
        host=args.host,
        port=args.port,
        path=selected_path,
    )
