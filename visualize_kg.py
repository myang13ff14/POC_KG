import sys
from pyvis.network import Network
from neo4j import GraphDatabase
from loader import URI, AUTH

if len(sys.argv) < 3:
    print("Usage: python visualize_kg.py <product_id_1> <product_id_2>")
    print("Example: python visualize_kg.py 40B90000US 40BE0135US")
    sys.exit(1)

pid1, pid2 = sys.argv[1], sys.argv[2]

driver = GraphDatabase.driver(URI, auth=AUTH)
with driver.session() as session:
    rows = session.run(
        """
        MATCH (p:Product)-[:COMPATIBLE_WITH]->(d:Device)-[:HAS_ID]->(m:MachineType)
        WHERE p.id IN [$pid1, $pid2]
        RETURN p.name AS product, p.id AS product_id,
               d.name AS device, m.id AS machine_type
        """,
        pid1=pid1, pid2=pid2,
    ).data()
driver.close()

# Find machine type IDs that appear in both products
from collections import defaultdict
mt_to_products = defaultdict(set)
for row in rows:
    mt_to_products[row["machine_type"]].add(row["product_id"])
shared_ids = {mt for mt, prods in mt_to_products.items() if len(prods) > 1}

net = Network(height="900px", width="100%", bgcolor="#1a1a2e", font_color="white", directed=True)
net.barnes_hut(spring_length=180, spring_strength=0.05, damping=0.09)

added = set()

for row in rows:
    product = row["product"] or row["product_id"]
    device = row["device"]
    machine_type = row["machine_type"]

    if product not in added:
        net.add_node(product, label=product, color="#4C9BE8", size=30,
                     title=f"Product: {product}")
        added.add(product)

    if device not in added:
        net.add_node(device, label=device, color="#F4A261", size=15,
                     title=f"Device: {device}")
        added.add(device)

    if machine_type not in added:
        # Shared IDs glow in yellow
        color = "#FFD700" if machine_type in shared_ids else "#57CC99"
        size = 18 if machine_type in shared_ids else 10
        title = f"⭐ SHARED Machine Type: {machine_type}" if machine_type in shared_ids else f"Machine Type: {machine_type}"
        net.add_node(machine_type, label=machine_type, color=color, size=size, title=title)
        added.add(machine_type)

    net.add_edge(product, device, color="#555577")
    net.add_edge(device, machine_type, color="#557755")

net.show_buttons(filter_=["physics"])
net.save_graph("kg_graph.html")
print(f"Saved kg_graph.html — {len(rows)} rows, {len(added)} nodes, {len(shared_ids)} shared machine type IDs")
if shared_ids:
    print(f"Shared IDs (yellow): {sorted(shared_ids)}")
