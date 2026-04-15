import os
from neo4j import GraphDatabase, basic_auth
from dotenv import load_dotenv

load_dotenv()

URI = "bolt://localhost:7687"
AUTH = basic_auth("neo4j", "")


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

    # Upsert each compatible Device and its MachineType IDs
    for device in product["compatible_devices"]:
        tx.run(
            """
            MATCH (p:Product {id: $product_id})
            MERGE (d:Device {name: $name})
            MERGE (p)-[:COMPATIBLE_WITH]->(d)
            MERGE (m:MachineType {id: $machine_type})
            SET m.footnote = $footnote
            MERGE (d)-[:HAS_ID]->(m)
            """,
            product_id=product["id"],
            name=device["name"],
            machine_type=device["machine_type"],
            footnote=device["footnote"],
        )
