# Hardcoded SmartFind product IDs to scrape.
# id: part number as it appears in the SmartFind URL
# category: human-readable label used as Neo4j node property

PRODUCTS = [
    # Docks
    {"id": "40B90000US", "category": "Dock"},
    {"id": "40BD0065US", "category": "Dock"},
    {"id": "40BE0135US", "category": "Dock"},
    # Keyboards
    {"id": "4Y41C33748", "category": "Keyboard"},
    {"id": "4Y41S04682", "category": "Keyboard"},
    {"id": "4Y41R64633", "category": "Keyboard"},
    {"id": "4X31R64400", "category": "Keyboard"},
    {"id": "4X31R64453", "category": "Keyboard"},
]

BASE_URL = "https://smartfind.lenovo.com/accessories/#/products/"
