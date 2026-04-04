from __future__ import annotations

import argparse
import asyncio
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.web.webapp.mcp_gateway import MCPGatewayError, MCPGatewayErrorWithPayload, send_request
from apps.web.webapp.request_templates import list_templates


DEFAULT_TARGET_URL = "http://mcp-xperts.labsec.ca/mcp"
DEFAULT_TRANSPORT = "mcp"
CATEGORY_ORDER = [
    "Discovery",
    "Signature Detection",
    "Poisoning",
    "Schema Validation",
]


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def print_json_block(title: str, payload: Any) -> None:
    print(f"\n=== {title} ===")
    print(json.dumps(to_jsonable(payload), indent=2, ensure_ascii=False))


def print_header(target_url: str, transport: str) -> None:
    print("\n=== MCP Demo CLI ===")
    print(f"Target URL: {target_url}")
    print(f"Transport: {transport}")
    print("Note: the target URL must include the full MCP endpoint path such as /mcp or /sse.")


def group_templates_by_category() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {category: [] for category in CATEGORY_ORDER}
    for template in list_templates():
        grouped.setdefault(template["category"], []).append(template)
    return grouped


def assign_request_ids(payload: Any, start_id: int) -> tuple[Any, int]:
    next_id = start_id
    copied = deepcopy(payload)

    def update_ids(node: Any) -> Any:
        nonlocal next_id
        if isinstance(node, dict):
            updated = {}
            for key, value in node.items():
                if key == "id":
                    updated[key] = next_id
                    next_id += 1
                else:
                    updated[key] = update_ids(value)
            return updated
        if isinstance(node, list):
            return [update_ids(item) for item in node]
        return node

    return update_ids(copied), next_id


def extract_response_payload(result: dict[str, Any]) -> Any:
    response = result.get("response", {})
    if response.get("event") is not None:
        return response["event"]
    if response.get("body") is not None:
        return response["body"]
    if response.get("request_http") is not None:
        return response["request_http"]
    return result


async def execute_template(
    template: dict[str, Any],
    *,
    target_url: str,
    transport: str,
    request_id_start: int,
) -> tuple[bool, int]:
    request_payload, next_id = assign_request_ids(template["request"], request_id_start)

    print(f"\n########## {template['category']} / {template['label']} ##########")
    print(f"Template ID: {template['id']}")
    print(f"Description: {template['description']}")
    print_json_block("JSON request", request_payload)

    try:
        result = await send_request(target_url, transport, request_payload)
        print_json_block("Connection details", result.get("connection"))
        print_json_block("JSON response", extract_response_payload(result))
        return True, next_id
    except MCPGatewayErrorWithPayload as exc:
        print_json_block(
            "MCP request error",
            {
                "error_type": exc.__class__.__name__,
                "message": str(exc),
                "payload": exc.payload,
            },
        )
        return False, next_id
    except MCPGatewayError as exc:
        print_json_block(
            "MCP request error",
            {
                "error_type": exc.__class__.__name__,
                "message": str(exc),
            },
        )
        return False, next_id
    except Exception as exc:
        print_json_block(
            "Unexpected error",
            {
                "error_type": exc.__class__.__name__,
                "message": str(exc),
            },
        )
        return False, next_id


async def run_template_batch(
    templates: list[dict[str, Any]],
    *,
    target_url: str,
    transport: str,
    title: str,
) -> None:
    print(f"\n=== {title} ===")
    success_count = 0
    next_request_id = 1

    for template in templates:
        succeeded, next_request_id = await execute_template(
            template,
            target_url=target_url,
            transport=transport,
            request_id_start=next_request_id,
        )
        if succeeded:
            success_count += 1

    print_json_block(
        "Batch summary",
        {
            "title": title,
            "total": len(templates),
            "successful": success_count,
            "failed": len(templates) - success_count,
        },
    )


def print_main_menu() -> None:
    print("\n=== Main Menu ===")
    print("1. Discovery")
    print("2. Signature Detection")
    print("3. Poisoning")
    print("4. Schema Validation")
    print("5. Run All")
    print("0. Quit")


def print_submenu(category: str, templates: list[dict[str, Any]]) -> None:
    print(f"\n=== {category} ===")
    for index, template in enumerate(templates, start=1):
        print(f"{index}. {template['label']} - {template['description']}")
    print("A. Run all actions in this section")
    print("0. Back")


async def run_submenu(category: str, templates: list[dict[str, Any]], *, target_url: str, transport: str) -> None:
    while True:
        print_submenu(category, templates)
        choice = input("\nSelect an action: ").strip()

        if choice == "0":
            return
        if choice.lower() == "a":
            await run_template_batch(
                templates,
                target_url=target_url,
                transport=transport,
                title=f"Run all actions in {category}",
            )
            continue
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(templates):
                await run_template_batch(
                    [templates[index]],
                    target_url=target_url,
                    transport=transport,
                    title=f"Run action: {templates[index]['label']}",
                )
                continue

        print("Unknown choice.")


async def run_menu(target_url: str, transport: str) -> None:
    grouped = group_templates_by_category()
    ordered_sections = [(category, grouped.get(category, [])) for category in CATEGORY_ORDER]

    while True:
        print_header(target_url, transport)
        print_main_menu()
        choice = input("\nSelect a section: ").strip()

        if choice == "0":
            return
        if choice == "5":
            all_templates = [template for _, items in ordered_sections for template in items]
            await run_template_batch(
                all_templates,
                target_url=target_url,
                transport=transport,
                title="Run all MCP actions",
            )
            continue
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(ordered_sections):
                category, templates = ordered_sections[index]
                await run_submenu(
                    category,
                    templates,
                    target_url=target_url,
                    transport=transport,
                )
                continue

        print("Unknown choice.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the MCP Demo CLI.")
    parser.add_argument(
        "--target-url",
        default=DEFAULT_TARGET_URL,
        help="Full MCP endpoint URL, including /mcp or /sse.",
    )
    parser.add_argument(
        "--transport",
        choices=["mcp", "sse"],
        default=DEFAULT_TRANSPORT,
        help="Transport mode used for MCP requests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(run_menu(args.target_url, args.transport))


if __name__ == "__main__":
    main()
