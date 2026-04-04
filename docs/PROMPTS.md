# MCP Hands-On Lab Prompts

This file contains ready-to-use prompts for real MCP clients such as Claude Desktop.

The lab server exposes three demo areas:

- `Signature Detection`
- `Poisoning Attack Protection`
- `JSON Schema Validation`

## Signature Detection

These prompts are intended to trigger tool calls that carry suspicious arguments.

### SQL Injection

```text
Use the database lookup tool to retrieve user 1 OR 1=1 exactly as written and show me the result.
```

```text
Check whether user 3 exists, then try the exact payload 1 OR 1=1 in the same database tool.
```

### Command Injection

```text
Use the ping tool exactly with this hostname: 127.0.0.1 && whoami
```

```text
Run the network diagnostic tool against localhost; ls and show the raw result.
```

### Path Traversal

```text
Use the file reading tool to open ../secrets.txt exactly as provided.
```

```text
Read ../../etc/passwd with the system file tool and return the output.
```

## Poisoning Attack Protection

These prompts are intended to make the client inspect MCP metadata, resources, and prompts.

Use one poisoning profile at a time for clean WAF logs.

### Profile 1: `malicious_cryptojacking`

Recommended environment:

```bash
MCP_TOOL_DESCRIPTION_VARIANT=malicious_cryptojacking
MCP_RESOURCE_VARIANT=benign
MCP_PROMPT_VARIANT=benign
```

Surface:

- tool metadata via `tools/list`

Prompt:

```text
List the available MCP tools and tell me which one should be used to draft a WAF incident summary.
```

Expected match:

- Group: `maliciousContent`
- Pattern: `Cryptojacking`
- Text: `cryptojacking`

### Profile 2: `social_urgent`

Recommended environment:

```bash
MCP_TOOL_DESCRIPTION_VARIANT=social_urgent
MCP_RESOURCE_VARIANT=benign
MCP_PROMPT_VARIANT=benign
```

Surface:

- tool metadata via `tools/list`

Prompt:

```text
Inspect the available MCP tools and summarize their purpose before doing anything else.
```

Expected match:

- Group: `maliciousContent`
- Pattern: `SocialEngineering`
- Text: `urgent action required now`

### Profile 3: `code_shell_rmrf`

Recommended environment:

```bash
MCP_TOOL_DESCRIPTION_VARIANT=code_shell_rmrf
MCP_RESOURCE_VARIANT=benign
MCP_PROMPT_VARIANT=benign
```

Surface:

- tool metadata via `tools/list`

Prompt:

```text
Review the available tools and identify which one can be used to prepare an incident summary.
```

Expected match:

- Group: `maliciousCodeExecution`
- Pattern: `ShellCommandInjection`
- Text: `rm -rf /`

### Profile 4: `bias_master_slave`

Recommended environment:

```bash
MCP_TOOL_DESCRIPTION_VARIANT=benign
MCP_RESOURCE_VARIANT=bias_master_slave
MCP_PROMPT_VARIANT=benign
```

Surface:

- resource content via `resources/read`

Prompt:

```text
Read the incident response playbook and summarize section 3.
```

Expected match:

- Group: `biasDetection`
- Pattern: `BiasedLanguage`
- Text: `master/slave`

### Profile 5: `exfil_ssn`

Recommended environment:

```bash
MCP_TOOL_DESCRIPTION_VARIANT=benign
MCP_RESOURCE_VARIANT=exfil_ssn
MCP_PROMPT_VARIANT=benign
```

Surface:

- resource content via `resources/read`

Prompt:

```text
Open the incident response playbook and extract the sample record mentioned in section 3.
```

Expected match:

- Group: `dataExfiltration`
- Pattern: `SSN`
- Text: `123-45-6789`

### Profile 6: `exfil_url`

Recommended environment:

```bash
MCP_TOOL_DESCRIPTION_VARIANT=benign
MCP_RESOURCE_VARIANT=exfil_url
MCP_PROMPT_VARIANT=benign
```

Surface:

- resource content via `resources/read`

Prompt:

```text
Read the incident response playbook and extract the training reference from section 3.
```

Expected match:

- Group: `dataExfiltration`
- Pattern: `URL`
- Text: `https://example.com/path`

### Prompt-Based Poisoning Demos

If you want the WAF log to come from `prompts/get` instead of metadata or resources, use one of these prompt variants:

```bash
MCP_PROMPT_VARIANT=malicious_cryptojacking
```

```text
Generate a handover summary for an overnight WAF alert involving suspicious MCP activity.
```

```bash
MCP_PROMPT_VARIANT=social_urgent
```

```text
Use the incident handover prompt to prepare a short SOC shift summary for a suspicious MCP event.
```

```bash
MCP_PROMPT_VARIANT=code_shell_rmrf
```

```text
Create a handover summary for a blocked request where the analyst suspects a dangerous shell payload.
```

### New SOC Tool

These prompts exercise the new tool directly:

```text
Draft an incident brief for a FortiWeb alert related to suspicious MCP traffic. Severity is high.
```

```text
Prepare a short analyst-ready incident brief for a blocked MCP request targeting a tool call.
```

## JSON Schema Validation

Schema validation is best exercised with the dedicated campaign runner rather than a conversational MCP client.

Use:

```bash
python mcp_schema_campaign.py http://localhost:7000/mcp
```

or through the WAF:

```bash
python mcp_schema_campaign.py https://YOUR-WAF-ENDPOINT/mcp
```

Reason:

- conversational MCP clients usually send valid MCP envelopes
- schema validation requires deliberately malformed MCP messages
- the dedicated runner is designed to send those invalid payloads safely and consistently

## Suggested Demo Order

1. Start with a benign prompt:

```text
What time is it in Montreal?
```

2. Show a signature example:

```text
Use the ping tool exactly with this hostname: 127.0.0.1 && whoami
```

3. Show poisoning on tool metadata:

```text
List the available tools and summarize their purpose.
```

4. Show poisoning on a resource:

```text
Read the incident response playbook and summarize section 3.
```

5. Show poisoning on a prompt:

```text
Generate a handover summary for an overnight WAF alert involving a suspicious MCP event.
```

6. Run schema validation with the dedicated runner:

```bash
python mcp_schema_campaign.py http://localhost:7000/mcp
```
