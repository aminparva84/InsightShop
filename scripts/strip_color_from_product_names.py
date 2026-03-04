"""
One-off script: Remove color from product names in the database.
Run after pulling the seed change so existing products show names without color.
Usage: python -m scripts.strip_color_from_product_names
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.product import Product


def product_name_without_color(name, color):
    """Remove leading color from product name."""
    if not name or not color:
        return name or ""
    name_str = name.strip()
    color_str = color.strip()
    if not color_str:
        return name_str
    lower_name = name_str.lower()
    lower_color = color_str.lower()
    if lower_name.startswith(lower_color):
        rest = name_str[len(color_str):].strip()
        if rest.startswith("-"):
            rest = rest.lstrip("-").strip()
        return rest if rest else name_str
    return name_str


def main():
    with app.app_context():
        updated = 0
        for p in Product.query.all():
            new_name = product_name_without_color(p.name, p.color)
            if new_name != p.name:
                p.name = new_name
                updated += 1
        if updated:
            db.session.commit()
            print(f"Updated {updated} product name(s) to remove color.")
        else:
            print("No product names needed updating.")


if __name__ == "__main__":
    main()
