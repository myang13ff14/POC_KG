# Lenovo Accessory Compatibility Knowledge Graph

A POC that scrapes Lenovo SmartFind product pages, loads compatibility data into a Neo4j knowledge graph, and provides a conversational AI agent to query it.

## Graph Structure

```
(Product) -[:COMPATIBLE_WITH]-> (Device) -[:HAS_ID]-> (MachineType)
```

- **Product** — Lenovo accessory (dock, keyboard) identified by part number
- **Device** — Compatible machine model (e.g. "ThinkPad X1 Carbon Series")
- **MachineType** — Machine type ID (e.g. `83EQ`). One device can have multiple IDs.

## Prerequisites

- Python 3.11+
- Docker

## Setup

```bash
# 1. Clone and create virtual environment
python -m venv poc_kg
source poc_kg/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Start Neo4j
docker compose up -d

# 5. Scrape and load data
python run.py
```

## Usage

### Conversational Agent

```bash
python agent.py
```

Ask questions like:
- `what accessories are compatible with ThinkPad X1 Carbon?`
- `what machine type IDs does the IdeaPad Slim 3 14IAH8 have?`
- `what docks work with machine type 83EQ?`
- `list all products`

The agent uses OpenAI GPT-4o with tool calling to query the knowledge graph directly.

### Query CLI

```bash
# All compatibility data
python query_compatibility.py

# By product ID
python query_compatibility.py --product 40B90000US

# By category
python query_compatibility.py --category Dock

# List all products or devices
python query_compatibility.py --list-products
python query_compatibility.py --list-devices
```

### Visualize the Graph

```bash
# Compare 2 products — shared machine type IDs highlighted in yellow
python visualize_kg.py 40B90000US 40BE0135US
```

Opens `kg_graph.html` in your browser. On WSL, open via:
```
\\wsl$\Ubuntu\home\<username>\POC_KG\kg_graph.html
```

## Project Structure

| File | Purpose |
|---|---|
| `run.py` | Entry point — scrape + load pipeline |
| `scraper.py` | Playwright scraper for SmartFind product pages |
| `loader.py` | Neo4j loader — writes Product, Device, MachineType nodes |
| `seed_products.py` | List of product IDs to scrape |
| `agent.py` | Conversational CLI agent (GPT-4o + tool calling) |
| `query_compatibility.py` | Query functions for the knowledge graph |
| `visualize_kg.py` | Interactive graph visualization via pyvis |
| `docker-compose.yml` | Neo4j 5 container |

## Adding More Products

Edit `seed_products.py` and add entries:

```python
{"id": "YOUR_PART_NUMBER", "category": "Dock"},  # or "Keyboard"
```

Then re-run `python run.py`.
