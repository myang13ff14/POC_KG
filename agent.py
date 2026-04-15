import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from query_compatibility import (
    get_all_compatibility,
    get_category_compatibility,
    get_compatibility_by_device,
    get_product_compatibility,
    get_products_by_machine_type,
    list_devices,
    list_devices_with_ids,
    list_products,
)

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = (
    "You are a Lenovo accessory compatibility assistant. "
    "You have access to a Neo4j knowledge graph containing Lenovo products "
    "(docks, keyboards) and the devices they are compatible with. "
    "Use the available tools to answer questions. "
    "Always use a tool to look up data — do not guess compatibility."
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_products",
            "description": "List all Product nodes in the knowledge graph.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_devices",
            "description": "List all Device nodes in the knowledge graph.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_compatibility",
            "description": "Return every product and its list of compatible devices.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_compatibility",
            "description": "Return compatible devices for a single product by its product ID (e.g. '40B90000US').",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "The product ID as stored in the graph, e.g. '40B90000US'.",
                    }
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_devices_with_ids",
            "description": "List all devices in the knowledge graph along with their machine type IDs.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_compatibility_by_device",
            "description": "Search by device model name (partial match). Returns the device's machine type IDs and all compatible products/accessories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "Full or partial device name, e.g. 'ThinkPad X1 Carbon' or 'IdeaPad'.",
                    }
                },
                "required": ["device_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_products_by_machine_type",
            "description": "Find all products (accessories) compatible with a specific machine type ID (e.g. '82QY', '83LN').",
            "parameters": {
                "type": "object",
                "properties": {
                    "machine_type_id": {
                        "type": "string",
                        "description": "The machine type ID, e.g. '82QY'.",
                    }
                },
                "required": ["machine_type_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_compatibility",
            "description": "Return all products in a category and their compatible devices. Category is 'Dock' or 'Keyboard'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Product category, either 'Dock' or 'Keyboard'.",
                    }
                },
                "required": ["category"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "list_products": lambda args: list_products(),
    "list_devices": lambda args: list_devices(),
    "get_all_compatibility": lambda args: get_all_compatibility(),
    "get_product_compatibility": lambda args: get_product_compatibility(args["product_id"]),
    "list_devices_with_ids": lambda args: list_devices_with_ids(),
    "get_compatibility_by_device": lambda args: get_compatibility_by_device(args["device_name"]),
    "get_products_by_machine_type": lambda args: get_products_by_machine_type(args["machine_type_id"]),
    "get_category_compatibility": lambda args: get_category_compatibility(args["category"]),
}


def run_tool(name: str, args: dict) -> str:
    result = TOOL_FUNCTIONS[name](args)
    return json.dumps(result)


def chat():
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print("Lenovo Accessory KG Agent — type 'exit' to quit\n")

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        while True:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg)
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = run_tool(tc.function.name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            else:
                messages.append({"role": "assistant", "content": msg.content})
                print(f"\nAssistant: {msg.content}\n")
                break


if __name__ == "__main__":
    chat()
