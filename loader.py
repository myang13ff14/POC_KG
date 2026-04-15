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
