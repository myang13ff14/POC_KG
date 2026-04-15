# Lenovo Accessory Compatibility Knowledge Graph — POC Design

**Date:** 2026-04-15  
**Goal:** Informal demo for IT staff showing that accessory compatibility data can be loaded into a graph database (Neo4j) and traversed with simple queries.

---

## Overview

Scrape a small set of Lenovo accessory product pages from SmartFind (2-3 docks, 2-3 keyboards), extract their compatibility device lists, and load everything into a local Neo4j instance. IT staff can then open the Neo4j browser and run Cypher queries to explore what accessories work with which devices.

---

## Graph Data Model

**Nodes:**

| Label | Properties |
|-------|-----------|
| `Product` | `id`, `name`, `category` (Dock / Keyboard), `part_number`, `url` |
| `Device` | `id`, `name`, `series` |

**Relationships:**

```
(:Product)-[:COMPATIBLE_WITH]->(:Device)
```

**Example query:**
```cypher
MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device)
WHERE d.name CONTAINS 'ThinkPad X1 Carbon'
RETURN p.name, p.category, d.name
```

---

## Components

```
docker-compose.yml   — Neo4j container (port 7474 browser, 7687 bolt)
seed_products.py     — hardcoded list of SmartFind product IDs to scrape
scraper.py           — Playwright: visits each product page, returns product info + compat list
loader.py            — writes scraped data into Neo4j as nodes + relationships
run.py               — entry point: scrape → load → print sample Cypher queries
requirements.txt     — playwright, neo4j, python-dotenv
.env                 — NEO4J_PASSWORD (gitignored)
```

---

## Flow

1. `docker-compose up -d` — starts Neo4j locally
2. `python run.py` — scrapes SmartFind, loads graph
3. Open `http://localhost:7474` — Neo4j browser, run queries, see graph visually

---

## Seed Products

Manually picked from SmartFind:

**Docks (3):**
- ThinkPad Universal USB-C Dock — `40B90000US`
- ThinkPad Thunderbolt 4 Dock — `40B00135US`
- ThinkPad USB-C Dock Gen 2 — `40AS0090US`

**Keyboards (3):**
- ThinkPad TrackPoint Keyboard II — `4Y40X49493`
- ThinkPad Compact USB Keyboard — `0B47190`
- Lenovo Wireless Keyboard and Mouse Combo — `4X30M39458`

*(IDs can be adjusted during implementation if any product page structure differs.)*

---

## Constraints

- Minimal code, no over-engineering
- No auth layer, no tests, no CI
- Single `.env` for Neo4j password, not committed
- Playwright handles JS-rendered pages on SmartFind
