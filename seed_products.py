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
