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
