# KG Agent — Design Spec

**Date:** 2026-04-15  
**Goal:** Add a conversational CLI agent on top of the Neo4j knowledge graph so the developer can ask natural language questions about Lenovo accessory compatibility and get answers backed by live graph data.

---

## Architecture

Single file `agent.py`. Wraps existing query functions from `query_compatibility.py` as OpenAI tool definitions. Runs a `while True` chat loop that maintains full conversation history. Each iteration:

1. Read user input (or exit on `quit` / `exit`)
2. Send history + tool definitions to GPT-4o
3. If model calls a tool — execute the matching function, append result to history, send back to model
4. Print final assistant message, append to history, loop

No frameworks. No new abstractions. Just `openai` + existing code.

---

## Tools

Five tools, each a thin wrapper around a function already in `query_compatibility.py`:

| Tool name | Function | Args |
|---|---|---|
| `get_all_compatibility` | `get_all_compatibility()` | none |
| `get_product_compatibility` | `get_product_compatibility(product_id)` | `product_id: str` |
| `get_category_compatibility` | `get_category_compatibility(category)` | `category: str` |
| `list_products` | `list_products()` | none |
| `list_devices` | `list_devices()` | none |

Tool definitions are passed as the `tools` parameter in the OpenAI chat completion call. Tool results are appended as `role: tool` messages.

---

## System Prompt

Short and direct:

> You are a Lenovo accessory compatibility assistant. You have access to a Neo4j knowledge graph containing Lenovo products (docks, keyboards) and the devices they are compatible with. Use the available tools to answer questions. Always use a tool to look up data — do not guess compatibility.

---

## Configuration

- `OPENAI_API_KEY` added to `.env` (already gitignored)
- Model: `gpt-4o`
- No streaming (keep it simple)

---

## Files Changed

| File | Change |
|---|---|
| `agent.py` | New file — the agent |
| `.env` | Add `OPENAI_API_KEY=...` |
| `.env.example` | Add `OPENAI_API_KEY=your-key-here` |
| `requirements.txt` | Add `openai` |

---

## Out of Scope

- Web UI or API server
- Streaming responses
- Conversation persistence across sessions
- Text-to-Cypher fallback
