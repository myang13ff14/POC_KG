# Lenovo Accessory Compatibility Knowledge Graph — POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape 2-3 docks and 2-3 keyboards from Lenovo SmartFind, load them into a local Neo4j graph with COMPATIBLE_WITH relationships, so IT can run Cypher queries in the Neo4j browser to explore accessory compatibility.

**Architecture:** Playwright scrapes each product page (JS-rendered SPA), extracting product info and the compatibility device list. A loader script writes Product and Device nodes plus COMPATIBLE_WITH edges into Neo4j. A single `run.py` entry point orchestrates the whole pipeline.

**Tech Stack:** Python 3.11+, Playwright (async), neo4j Python driver, python-dotenv, Docker Compose (Neo4j 5)

---

## File Map

| File | Responsibility |
|------|---------------|
| `docker-compose.yml` | Neo4j 5 container, ports 7474 + 7687 |
| `.env` | `NEO4J_PASSWORD` (gitignored) |
| `.env.example` | Template for `.env` |
| `.gitignore` | Ignore `.env` |
| `requirements.txt` | Python dependencies |
| `seed_products.py` | Hardcoded list of product IDs + categories to scrape |
| `scraper.py` | Playwright: visit each SmartFind product page, return structured dict |
| `loader.py` | Neo4j: merge Product + Device nodes, create COMPATIBLE_WITH edges |
| `run.py` | Entry point: iterate seed list → scrape → load → print sample queries |

---

## Task 1: Project scaffold

**Files:**
- Create: `docker-compose.yml`
- Create: `.env`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `requirements.txt`

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
services:
  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
```

- [ ] **Step 2: Create `.env`**

```
NEO4J_PASSWORD=pocpassword
```

- [ ] **Step 3: Create `.env.example`**

```
NEO4J_PASSWORD=yourpasswordhere
```

- [ ] **Step 4: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.playwright/
```

- [ ] **Step 5: Create `requirements.txt`**

```
playwright==1.43.0
neo4j==5.19.0
python-dotenv==1.0.1
```

- [ ] **Step 6: Install dependencies**

```bash
pip install -r requirements.txt
playwright install chromium
```

Expected: Chromium browser binary downloaded, no errors.

- [ ] **Step 7: Start Neo4j**

```bash
docker-compose up -d
```

Expected output includes `Started`.  
Open `http://localhost:7474` in browser — Neo4j login page should appear.  
Login with username `neo4j`, password `pocpassword`.

- [ ] **Step 8: Commit**

```bash
git init
git add docker-compose.yml .env.example .gitignore requirements.txt
git commit -m "chore: project scaffold with Neo4j docker-compose"
```

---

## Task 2: Seed product list

**Files:**
- Create: `seed_products.py`

- [ ] **Step 1: Create `seed_products.py`**

```python
# Hardcoded SmartFind product IDs to scrape.
# id: part number as it appears in the SmartFind URL
# category: human-readable label used as Neo4j node property

PRODUCTS = [
    # Docks
    {"id": "40B90000US", "category": "Dock"},
    {"id": "40B00135US", "category": "Dock"},
    {"id": "40AS0090US", "category": "Dock"},
    # Keyboards
    {"id": "4Y40X49493", "category": "Keyboard"},
    {"id": "0B47190",    "category": "Keyboard"},
    {"id": "4X30M39458", "category": "Keyboard"},
]

BASE_URL = "https://smartfind.lenovo.com/accessories/#/products/"
```

- [ ] **Step 2: Commit**

```bash
git add seed_products.py
git commit -m "feat: add seed product list"
```

---

## Task 3: Playwright scraper

**Files:**
- Create: `scraper.py`

The SmartFind site is a JS-rendered SPA (hash router). Playwright navigates to each product URL, waits for the page to load, then extracts:
- Product name
- Part number (from the URL or page)
- Compatible devices list (the "Compatible Systems" or "Compatibility" section)

> **Note:** Exact CSS selectors depend on SmartFind's live DOM. The selectors below are based on inspection of the site at time of writing. If a selector returns empty, open the page in Chrome DevTools and update the selector accordingly.

- [ ] **Step 1: Create `scraper.py`**

```python
import asyncio
from playwright.async_api import async_playwright
from seed_products import BASE_URL


async def scrape_product(page, product_id: str, category: str) -> dict:
    """Scrape a single SmartFind product page. Returns a dict with product info and compat list."""
    url = f"{BASE_URL}{product_id}"
    await page.goto(url, wait_until="networkidle")

    # Product name — adjust selector if needed
    name_el = await page.query_selector("h1.product-name, h1, .product-title")
    name = (await name_el.inner_text()).strip() if name_el else product_id

    # Part number — often displayed near the title
    part_el = await page.query_selector(".part-number, [data-testid='part-number'], .sku")
    part_number = (await part_el.inner_text()).strip() if part_el else product_id

    # Navigate to the compatibility tab if it exists
    compat_tab = await page.query_selector("a[href*='compat'], button:has-text('Compatibility'), .tab:has-text('Compatible')")
    if compat_tab:
        await compat_tab.click()
        await page.wait_for_load_state("networkidle")

    # Grab all compatible device names from the list
    device_els = await page.query_selector_all(
        ".compatibility-list li, .compat-item, table.compat-table td:first-child, .compatible-systems li"
    )
    devices = []
    for el in device_els:
        text = (await el.inner_text()).strip()
        if text:
            devices.append(text)

    return {
        "id": product_id,
        "name": name,
        "part_number": part_number,
        "category": category,
        "url": url,
        "compatible_devices": devices,
    }


async def scrape_all(products: list[dict]) -> list[dict]:
    """Scrape all products. Returns list of product dicts."""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for product in products:
            print(f"Scraping {product['id']} ({product['category']})...")
            try:
                result = await scrape_product(page, product["id"], product["category"])
                print(f"  -> {result['name']}: {len(result['compatible_devices'])} compatible devices")
                results.append(result)
            except Exception as e:
                print(f"  -> ERROR scraping {product['id']}: {e}")
        await browser.close()
    return results
```

- [ ] **Step 2: Quick smoke test — run scraper on one product**

```bash
python -c "
import asyncio
from scraper import scrape_all
result = asyncio.run(scrape_all([{'id': '40B90000US', 'category': 'Dock'}]))
print(result)
"
```

Expected: prints a dict with `name`, `part_number`, and a non-empty `compatible_devices` list.  
If `compatible_devices` is empty, open `https://smartfind.lenovo.com/accessories/#/products/40B90000US` in Chrome DevTools, inspect the compatibility section, find the correct selector, and update `scraper.py`.

- [ ] **Step 3: Commit**

```bash
git add scraper.py
git commit -m "feat: playwright scraper for SmartFind product pages"
```

---

## Task 4: Neo4j loader

**Files:**
- Create: `loader.py`

- [ ] **Step 1: Create `loader.py`**

```python
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

URI = "bolt://localhost:7687"
AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD", "pocpassword"))


def load_products(products: list[dict]):
    """Write all products and their compatible devices into Neo4j."""
    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        for product in products:
            session.execute_write(_merge_product, product)
    driver.close()
    print(f"Loaded {len(products)} products into Neo4j.")


def _merge_product(tx, product: dict):
    # Upsert the Product node
    tx.run(
        """
        MERGE (p:Product {id: $id})
        SET p.name = $name,
            p.part_number = $part_number,
            p.category = $category,
            p.url = $url
        """,
        id=product["id"],
        name=product["name"],
        part_number=product["part_number"],
        category=product["category"],
        url=product["url"],
    )

    # Upsert each compatible Device and create the relationship
    for device_name in product["compatible_devices"]:
        device_id = device_name.lower().replace(" ", "-")
        tx.run(
            """
            MERGE (d:Device {id: $device_id})
            SET d.name = $device_name
            WITH d
            MATCH (p:Product {id: $product_id})
            MERGE (p)-[:COMPATIBLE_WITH]->(d)
            """,
            device_id=device_id,
            device_name=device_name,
            product_id=product["id"],
        )
```

- [ ] **Step 2: Smoke test loader with dummy data**

```bash
python -c "
from loader import load_products
load_products([{
    'id': 'TEST001',
    'name': 'Test Dock',
    'part_number': 'TEST001',
    'category': 'Dock',
    'url': 'http://example.com',
    'compatible_devices': ['ThinkPad X1 Carbon Gen 11', 'ThinkPad T14 Gen 3'],
}])
"
```

Expected: `Loaded 1 products into Neo4j.`  
Then in Neo4j browser (`http://localhost:7474`), run:
```cypher
MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device) RETURN p, d
```
You should see the test product and 2 device nodes connected by arrows.

- [ ] **Step 3: Commit**

```bash
git add loader.py
git commit -m "feat: neo4j loader for product and device nodes"
```

---

## Task 5: Orchestrator and demo queries

**Files:**
- Create: `run.py`

- [ ] **Step 1: Create `run.py`**

```python
import asyncio
from seed_products import PRODUCTS
from scraper import scrape_all
from loader import load_products

DEMO_QUERIES = """
=== DEMO CYPHER QUERIES (paste into http://localhost:7474) ===

1. Show the full graph:
   MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device) RETURN p, d

2. Find all accessories compatible with a specific device:
   MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device)
   WHERE d.name CONTAINS 'ThinkPad X1'
   RETURN p.name, p.category, d.name

3. Find all devices a specific dock works with:
   MATCH (p:Product {category: 'Dock'})-[:COMPATIBLE_WITH]->(d:Device)
   RETURN p.name, collect(d.name) AS compatible_devices

4. Count compatible devices per product:
   MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device)
   RETURN p.name, p.category, count(d) AS device_count
   ORDER BY device_count DESC
"""


async def main():
    print("=== Lenovo Accessory Compatibility KG POC ===\n")
    print(f"Scraping {len(PRODUCTS)} products from SmartFind...\n")
    products = await scrape_all(PRODUCTS)

    print(f"\nLoading {len(products)} products into Neo4j...")
    load_products(products)

    print(DEMO_QUERIES)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Run the full pipeline**

```bash
python run.py
```

Expected: scrapes all 6 products, prints progress, loads into Neo4j, then prints demo queries.

- [ ] **Step 3: Verify in Neo4j browser**

Open `http://localhost:7474`, login with `neo4j` / `pocpassword`, run:
```cypher
MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device) RETURN p, d
```
You should see a graph with Product nodes connected to Device nodes via COMPATIBLE_WITH arrows.

- [ ] **Step 4: Commit**

```bash
git add run.py
git commit -m "feat: orchestrator run.py with demo cypher queries"
```

---

## Selector Troubleshooting Guide

If `compatible_devices` comes back empty after Task 3 Step 2:

1. Open Chrome and go to `https://smartfind.lenovo.com/accessories/#/products/40B90000US`
2. Wait for the page to fully load, then click the "Compatibility" or "Compatible Systems" tab
3. Right-click on a device name in the list → Inspect
4. Note the element type and class (e.g., `<li class="compat-row">`)
5. Update the `device_els` selector in `scraper.py` to match
6. Re-run the smoke test from Task 3 Step 2

---

## Reset Neo4j (if you need a clean slate)

```cypher
MATCH (n) DETACH DELETE n
```

Run this in the Neo4j browser to wipe all nodes and start fresh before re-running `run.py`.
