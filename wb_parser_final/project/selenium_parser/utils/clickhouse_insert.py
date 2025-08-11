import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from db import client


def parse_category_levels(category_raw: str):
    parts = category_raw.split('_')
    category = parts[-1]  # last part as the main category

    # L1 = last part, L2 = second last, etc.
    levels = [None, None, None, None]  # L1, L2, L3, L4

    # Fill levels in reverse order
    for i, part in enumerate(reversed(parts)):
        if i < 4:
            levels[i] = part

    return category, levels

def insert_product_if_new(data: dict):
    # Get data with fallback values
    article = data.get("article", "")
    product_url = data.get("link", "")
    category_raw = data.get("category", "")

    # Skip only if there's no article (main identifier)
    if not article:
        print("⚠️ Skipped: no article", data)
        return

    try:
        result = client.query(
            "SELECT count() FROM wildberries_products_parsed WHERE article = %(article)s",
            parameters={'article': article}
        )
        existing = result.result_rows[0][0] if result.result_rows else 0

        if existing > 0:
            print(f"⏭ Already exists: {article}")
            return
    except Exception as check_e:
        print(f"⚠️ Error checking existence of {article}: {check_e}")
        # Continue with insertion if we couldn't check

    # Process category (even if empty)
    if category_raw:
        category, (category_l1, category_l2, category_l3, category_l4) = parse_category_levels(category_raw)
    else:
        category = ""
        category_l1 = ""
        category_l2 = ""
        category_l3 = ""
        category_l4 = ""

    # Match the actual table structure (8 columns)
    insert_data = (
        article or "",           # article
        product_url or "",      # product_url
        category_raw or "",     # category_raw
        category or "",         # category
        category_l1 or "",      # category_l1
        category_l2 or "",      # category_l2
        category_l3 or "",      # category_l3
        category_l4 or ""       # category_l4
    )

    try:
        result = client.insert(
            table='wildberries_products_parsed',
            data=[insert_data],
            column_names=['article', 'product_url', 'category_raw', 'category', 'category_l1', 'category_l2', 'category_l3', 'category_l4']
        )
        print(f"✅ Added: {article}")
    except Exception as e:
        error_msg = str(e) if str(e) != '0' else 'Unknown ClickHouse error'
        print(f"❌ Error inserting product {article}: {error_msg}")
        print(f"🧾 Error type: {type(e).__name__}")
        print(f"🧾 Data: {insert_data}")
