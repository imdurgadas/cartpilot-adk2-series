"""
CartPilot mock product catalog.
In production this would call a real product/inventory service —
kept as an in-memory dict here so every blog post's code runs with
zero external dependencies.
"""

CATALOG = {
    "sku-001": {"sku": "sku-001", "name": "Trail Runner Jacket", "category": "outdoor",
                "price": 89.99, "stock": 14, "color": "forest green", "sizes": ["S", "M", "L", "XL"]},
    "sku-002": {"sku": "sku-002", "name": "Insulated Water Bottle 1L", "category": "outdoor",
                "price": 24.50, "stock": 42, "color": "steel", "sizes": ["one-size"]},
    "sku-003": {"sku": "sku-003", "name": "Wireless Trail Earbuds", "category": "electronics",
                "price": 59.00, "stock": 0, "color": "black", "sizes": ["one-size"]},
    "sku-004": {"sku": "sku-004", "name": "Merino Wool Hiking Socks (3-pack)", "category": "apparel",
                "price": 18.75, "stock": 60, "color": "grey", "sizes": ["S", "M", "L"]},
    "sku-005": {"sku": "sku-005", "name": "Compact Camp Stove", "category": "outdoor",
                "price": 45.00, "stock": 7, "color": "silver", "sizes": ["one-size"]},
}


def find_products(query: str = "", category: str = "") -> list[dict]:
    """Search the catalog by free-text query and/or category filter."""
    query = query.lower().strip()
    results = []
    for item in CATALOG.values():
        matches_query = query in item["name"].lower() if query else True
        matches_category = item["category"] == category if category else True
        if matches_query and matches_category:
            results.append(item)
    return results


def get_product(sku: str) -> dict | None:
    return CATALOG.get(sku)
