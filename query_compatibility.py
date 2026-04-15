import argparse
from neo4j import GraphDatabase
from loader import URI, AUTH

_driver = GraphDatabase.driver(URI, auth=AUTH)


def run_query(cypher: str, params: dict | None = None) -> list[dict]:
    with _driver.session() as session:
        result = session.run(cypher, params or {})
        return [record.data() for record in result]


def get_all_compatibility() -> list[dict]:
    return run_query(
        """
        MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device)
        RETURN p.id AS product_id,
               p.name AS product_name,
               p.category AS product_category,
               collect(d.name) AS compatible_devices
        ORDER BY p.id
        """
    )


def get_product_compatibility(product_id: str) -> list[dict]:
    return run_query(
        """
        MATCH (p:Product {id: $product_id})-[:COMPATIBLE_WITH]->(d:Device)
        RETURN p.id AS product_id,
               p.name AS product_name,
               p.category AS product_category,
               collect(d.name) AS compatible_devices
        """,
        {"product_id": product_id},
    )


def get_category_compatibility(category: str) -> list[dict]:
    return run_query(
        """
        MATCH (p:Product {category: $category})-[:COMPATIBLE_WITH]->(d:Device)
        RETURN p.id AS product_id,
               p.name AS product_name,
               collect(d.name) AS compatible_devices
        ORDER BY p.id
        """,
        {"category": category},
    )


def list_products() -> list[dict]:
    return run_query(
        """
        MATCH (p:Product)
        RETURN p.id AS product_id,
               p.name AS product_name,
               p.part_number AS part_number,
               p.category AS product_category,
               p.url AS product_url
        ORDER BY p.id
        """
    )


def list_devices_with_ids() -> list[dict]:
    return run_query(
        """
        MATCH (d:Device)-[:HAS_ID]->(m:MachineType)
        RETURN d.name AS device_name, collect(m.id) AS machine_type_ids
        ORDER BY d.name
        """
    )


def get_compatibility_by_device(device_name: str) -> list[dict]:
    return run_query(
        """
        MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device)-[:HAS_ID]->(m:MachineType)
        WHERE toLower(d.name) CONTAINS toLower($device_name)
        RETURN d.name AS device_name,
               collect(DISTINCT m.id) AS machine_type_ids,
               collect(DISTINCT p.name) AS compatible_products
        ORDER BY d.name
        """,
        {"device_name": device_name},
    )


def get_products_by_machine_type(machine_type_id: str) -> list[dict]:
    return run_query(
        """
        MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device)-[:HAS_ID]->(m:MachineType {id: $machine_type_id})
        RETURN p.id AS product_id,
               p.name AS product_name,
               p.category AS product_category,
               d.name AS device_name
        ORDER BY p.category, p.name
        """,
        {"machine_type_id": machine_type_id},
    )


def list_devices() -> list[dict]:
    return run_query(
        """
        MATCH (d:Device)
        RETURN d.machine_type AS machine_type,
               d.name AS device_name,
               d.footnote AS footnote
        ORDER BY d.name
        """
    )


def print_rows(rows: list[dict]) -> None:
    if not rows:
        print("No results found.")
        return

    for row in rows:
        print("-" * 60)
        for key, value in row.items():
            print(f"{key}: {value}")
    print("-" * 60)
    print(f"Returned {len(rows)} row(s).")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query compatibility data from the Lenovo accessory KG."
    )
    parser.add_argument(
        "--product",
        help="Return compatible devices for the product id.",
    )
    parser.add_argument(
        "--category",
        help="Return products and their compatible devices for a category.",
    )
    parser.add_argument(
        "--list-products",
        action="store_true",
        help="List all Product nodes.",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List all Device nodes.",
    )
    args = parser.parse_args()

    if args.product:
        rows = get_product_compatibility(args.product)
    elif args.category:
        rows = get_category_compatibility(args.category)
    elif args.list_products:
        rows = list_products()
    elif args.list_devices:
        rows = list_devices()
    else:
        rows = get_all_compatibility()

    print_rows(rows)


if __name__ == "__main__":
    main()
