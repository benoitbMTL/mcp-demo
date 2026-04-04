from __future__ import annotations

from copy import deepcopy


REQUEST_TEMPLATES = [
    {
        "id": "discovery_tools_list",
        "label": "List tools",
        "category": "Discovery",
        "description": "Retrieve the tool catalog exposed by the MCP server.",
        "request": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
        },
    },
    {
        "id": "discovery_prompts_list",
        "label": "List prompts",
        "category": "Discovery",
        "description": "Retrieve the prompts exposed by the MCP server.",
        "request": {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "prompts/list",
        },
    },
    {
        "id": "discovery_resources_list",
        "label": "List resources",
        "category": "Discovery",
        "description": "Retrieve the resource catalog exposed by the MCP server.",
        "request": {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "resources/list",
        },
    },
    {
        "id": "discovery_resource_read",
        "label": "Read resource",
        "category": "Discovery",
        "description": "Read the incident response playbook resource from the lab server.",
        "request": {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {
                "uri": "resource://incident-response-playbook",
            },
        },
    },
    {
        "id": "discovery_prompt_get",
        "label": "Get prompt",
        "category": "Discovery",
        "description": "Request a prompt-generated SOC handover summary.",
        "request": {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "prompts/get",
            "params": {
                "name": "summarize_incident_handover",
                "arguments": {
                    "incident_title": "Suspicious MCP request blocked by the WAF",
                },
            },
        },
    },
    {
        "id": "tool_current_datetime",
        "label": "Call time tool",
        "category": "Discovery",
        "description": "Call a benign tool that returns real-time clock data.",
        "request": {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "current_datetime",
                "arguments": {
                    "timezone": "America/Montreal",
                },
            },
        },
    },
    {
        "id": "tool_incident_brief",
        "label": "Call incident brief tool",
        "category": "Discovery",
        "description": "Call the SOC/WAF demo tool with a realistic incident title.",
        "request": {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "draft_incident_brief",
                "arguments": {
                    "incident_title": "FortiWeb blocked a suspicious tools/call request",
                    "severity": "high",
                },
            },
        },
    },
    {
        "id": "signature_db_normal",
        "label": "Signature: database lookup",
        "category": "Signature Detection",
        "description": "Normal database lookup request for comparison with the injection payload.",
        "request": {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "tools/call",
            "params": {
                "name": "query_user_db",
                "arguments": {
                    "user_id": "3",
                },
            },
        },
    },
    {
        "id": "signature_db_sqli",
        "label": "Signature: SQL injection",
        "category": "Signature Detection",
        "description": "SQL injection probe carried through a tool argument.",
        "request": {
            "jsonrpc": "2.0",
            "id": 21,
            "method": "tools/call",
            "params": {
                "name": "query_user_db",
                "arguments": {
                    "user_id": "1 OR 1=1",
                },
            },
        },
    },
    {
        "id": "signature_ping_normal",
        "label": "Signature: ping normal",
        "category": "Signature Detection",
        "description": "Normal network diagnostic request for comparison with the command injection payload.",
        "request": {
            "jsonrpc": "2.0",
            "id": 22,
            "method": "tools/call",
            "params": {
                "name": "execute_ping",
                "arguments": {
                    "hostname": "8.8.8.8",
                },
            },
        },
    },
    {
        "id": "signature_ping_injection",
        "label": "Signature: command injection",
        "category": "Signature Detection",
        "description": "Command injection payload sent to the ping tool.",
        "request": {
            "jsonrpc": "2.0",
            "id": 23,
            "method": "tools/call",
            "params": {
                "name": "execute_ping",
                "arguments": {
                    "hostname": "127.0.0.1 && whoami",
                },
            },
        },
    },
    {
        "id": "signature_file_normal",
        "label": "Signature: file read normal",
        "category": "Signature Detection",
        "description": "Normal file access for comparison with the path traversal payload.",
        "request": {
            "jsonrpc": "2.0",
            "id": 24,
            "method": "tools/call",
            "params": {
                "name": "read_system_file",
                "arguments": {
                    "filename": "app.log",
                },
            },
        },
    },
    {
        "id": "signature_file_traversal",
        "label": "Signature: path traversal",
        "category": "Signature Detection",
        "description": "Path traversal payload sent to the file tool.",
        "request": {
            "jsonrpc": "2.0",
            "id": 25,
            "method": "tools/call",
            "params": {
                "name": "read_system_file",
                "arguments": {
                    "filename": "../secrets.txt",
                },
            },
        },
    },
    {
        "id": "poison_tool_metadata",
        "label": "Poisoning: tool metadata",
        "category": "Poisoning",
        "description": "Trigger poisoning inspection on tool descriptions via tools/list.",
        "request": {
            "jsonrpc": "2.0",
            "id": 40,
            "method": "tools/list",
        },
    },
    {
        "id": "poison_resource_content",
        "label": "Poisoning: resource content",
        "category": "Poisoning",
        "description": "Trigger poisoning inspection on resource content via resources/read.",
        "request": {
            "jsonrpc": "2.0",
            "id": 41,
            "method": "resources/read",
            "params": {
                "uri": "resource://incident-response-playbook",
            },
        },
    },
    {
        "id": "poison_prompt_content",
        "label": "Poisoning: prompt content",
        "category": "Poisoning",
        "description": "Trigger poisoning inspection on prompt text via prompts/get.",
        "request": {
            "jsonrpc": "2.0",
            "id": 42,
            "method": "prompts/get",
            "params": {
                "name": "summarize_incident_handover",
                "arguments": {
                    "incident_title": "Overnight WAF alert involving suspicious MCP activity",
                },
            },
        },
    },
    {
        "id": "schema_valid_baseline",
        "label": "Schema: valid baseline",
        "category": "Schema Validation",
        "description": "Valid baseline request to confirm the MCP flow before sending invalid envelopes.",
        "request": {
            "jsonrpc": "2.0",
            "id": 60,
            "method": "tools/call",
            "params": {
                "name": "current_datetime",
                "arguments": {
                    "timezone": "UTC",
                },
            },
        },
    },
    {
        "id": "schema_missing_method",
        "label": "Schema: missing method",
        "category": "Schema Validation",
        "description": "Invalid MCP request missing the required method field.",
        "request": {
            "jsonrpc": "2.0",
            "id": 61,
            "params": {
                "name": "current_datetime",
                "arguments": {
                    "timezone": "UTC",
                },
            },
        },
    },
    {
        "id": "schema_wrong_method_const",
        "label": "Schema: wrong method value",
        "category": "Schema Validation",
        "description": "Invalid MCP request using tool/call instead of tools/call.",
        "request": {
            "jsonrpc": "2.0",
            "id": 62,
            "method": "tool/call",
            "params": {
                "name": "current_datetime",
                "arguments": {
                    "timezone": "UTC",
                },
            },
        },
    },
    {
        "id": "schema_method_wrong_type",
        "label": "Schema: method wrong type",
        "category": "Schema Validation",
        "description": "Invalid MCP request where method is not a string.",
        "request": {
            "jsonrpc": "2.0",
            "id": 63,
            "method": 123,
            "params": {
                "name": "current_datetime",
                "arguments": {
                    "timezone": "UTC",
                },
            },
        },
    },
    {
        "id": "schema_missing_params",
        "label": "Schema: missing params",
        "category": "Schema Validation",
        "description": "Invalid MCP request missing the params object.",
        "request": {
            "jsonrpc": "2.0",
            "id": 64,
            "method": "tools/call",
        },
    },
    {
        "id": "schema_params_wrong_type",
        "label": "Schema: params wrong type",
        "category": "Schema Validation",
        "description": "Invalid MCP request where params is a string instead of an object.",
        "request": {
            "jsonrpc": "2.0",
            "id": 65,
            "method": "tools/call",
            "params": "boom",
        },
    },
    {
        "id": "schema_missing_name",
        "label": "Schema: missing params.name",
        "category": "Schema Validation",
        "description": "Invalid MCP request missing the params.name field.",
        "request": {
            "jsonrpc": "2.0",
            "id": 66,
            "method": "tools/call",
            "params": {
                "arguments": {},
            },
        },
    },
    {
        "id": "schema_name_wrong_type",
        "label": "Schema: name wrong type",
        "category": "Schema Validation",
        "description": "Invalid MCP request where params.name is not a string.",
        "request": {
            "jsonrpc": "2.0",
            "id": 67,
            "method": "tools/call",
            "params": {
                "name": 99,
                "arguments": {},
            },
        },
    },
    {
        "id": "schema_arguments_wrong_type",
        "label": "Schema: arguments wrong type",
        "category": "Schema Validation",
        "description": "Invalid MCP request where params.arguments is not an object.",
        "request": {
            "jsonrpc": "2.0",
            "id": 68,
            "method": "tools/call",
            "params": {
                "name": "current_datetime",
                "arguments": "not-an-object",
            },
        },
    },
    {
        "id": "schema_top_level_array",
        "label": "Schema: top-level array",
        "category": "Schema Validation",
        "description": "Invalid MCP payload shaped as an array instead of an object.",
        "request": [
            {
                "jsonrpc": "2.0",
                "id": 69,
                "method": "tools/call",
                "params": {
                    "name": "current_datetime",
                    "arguments": {
                        "timezone": "UTC",
                    },
                },
            }
        ],
    },
]


DEFAULT_TEMPLATE_ID = "discovery_tools_list"


def list_templates() -> list[dict]:
    return deepcopy(REQUEST_TEMPLATES)


def get_default_request() -> dict:
    for template in REQUEST_TEMPLATES:
        if template["id"] == DEFAULT_TEMPLATE_ID:
            return deepcopy(template["request"])
    return deepcopy(REQUEST_TEMPLATES[0]["request"])
