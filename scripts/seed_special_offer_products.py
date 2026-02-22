"""Seed 5 special-offer products with sale dates and percentages. Uses static/images/product-1.png through product-5.png."""
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.product import Product
import json

# 5 products for Special offers: names, descriptions, prices, image filenames, sale %
SPECIAL_OFFER_PRODUCTS = [
    {
        "name": "Autumn Plaid High-Waisted Shorts",
        "description": "Stylish high-waisted shorts in a classic plaid pattern with rich autumnal tones of forest green, earthy brown, and deep navy. Relaxed fit with pleated detailing and cuffed hems. Perfect for a casual, retro-inspired look. Pair with a simple tee and gold accents for an effortless outfit.",
        "price": 49.99,
        "category": "women",
        "color": "Forest Green, Brown, Navy",
        "size": "M",
        "available_colors": ["Forest Green", "Navy", "Brown"],
        "available_sizes": ["XS", "S", "M", "L", "XL"],
        "fabric": "Cotton Blend",
        "clothing_type": "Shorts",
        "clothing_category": "shorts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "fall",
        "image_filename": "product-1.png",
        "sale_percentage": 25.0,
    },
    {
        "name": "Sky Blue Ribbed Polo Sweater",
        "description": "Chic ribbed knit sweater in a soft sky blue with a polished polo collar and two-button placket. Relaxed, slightly oversized fit in a comfortable cotton blend. Ideal for smart-casual occasions—pair with white trousers and gold jewelry for a refined look.",
        "price": 59.99,
        "category": "women",
        "color": "Sky Blue",
        "size": "M",
        "available_colors": ["Sky Blue", "White", "Cream"],
        "available_sizes": ["XS", "S", "M", "L", "XL"],
        "fabric": "Cotton Knit",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_filename": "product-2.png",
        "sale_percentage": 20.0,
    },
    {
        "name": "Burgundy Relaxed Crewneck Tee",
        "description": "Effortless short-sleeve tee in a deep burgundy with a rounded neckline and relaxed fit. Soft, breathable cotton perfect for layering or wearing alone. A versatile staple that pairs beautifully with plaid shorts, jeans, or high-waisted trousers for a casual preppy or dark academia vibe.",
        "price": 29.99,
        "category": "women",
        "color": "Burgundy",
        "size": "M",
        "available_colors": ["Burgundy", "Black", "Navy"],
        "available_sizes": ["XS", "S", "M", "L", "XL"],
        "fabric": "100% Cotton",
        "clothing_type": "T-Shirt",
        "clothing_category": "t_shirts",
        "occasion": "casual",
        "age_group": "all",
        "season": "all_season",
        "image_filename": "product-3.png",
        "sale_percentage": 15.0,
    },
    {
        "name": "Warm Plaid Pleated Trousers",
        "description": "High-waisted trousers in a bold plaid of warm red, orange, and beige with thin black lines for a structured grid. Sturdy wool or wool-blend fabric with a relaxed, tapered fit. A statement piece that elevates any casual or indie-inspired outfit. Style with a light tee and belt for a put-together look.",
        "price": 69.99,
        "category": "women",
        "color": "Red, Orange, Beige",
        "size": "M",
        "available_colors": ["Plaid Red/Orange", "Navy", "Black"],
        "available_sizes": ["XS", "S", "M", "L", "XL"],
        "fabric": "Wool Blend",
        "clothing_type": "Trousers",
        "clothing_category": "pants",
        "occasion": "casual,date_night",
        "age_group": "young_adult",
        "season": "fall",
        "image_filename": "product-4.png",
        "sale_percentage": 20.0,
    },
    {
        "name": "Sage Green Pleated Cuff Shorts",
        "description": "High-waisted shorts in a muted sage or olive green with a loose, pleated fit and cuffed hem for a relaxed, slightly utilitarian feel. Comfortable cotton blend in earthy tones. Layer with a pastel yellow or beige tee and a brown leather belt for a fresh, minimal outfit.",
        "price": 42.99,
        "category": "women",
        "color": "Sage Green",
        "size": "M",
        "available_colors": ["Sage Green", "Olive", "Beige"],
        "available_sizes": ["XS", "S", "M", "L", "XL"],
        "fabric": "Cotton Blend",
        "clothing_type": "Shorts",
        "clothing_category": "shorts",
        "occasion": "casual",
        "age_group": "all",
        "season": "summer,fall",
        "image_filename": "product-5.png",
        "sale_percentage": 30.0,
    },
]


def seed_special_offer_products():
    """Add 5 special-offer products with sale enabled. Does not remove existing products."""
    with app.app_context():
        today = date.today()
        sale_start = today - timedelta(days=1)  # started yesterday
        sale_end = today + timedelta(days=30)    # ends in 30 days

        static_images = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "static", "images"
        )
        created = 0
        for p in SPECIAL_OFFER_PRODUCTS:
            # Avoid duplicate by name
            if Product.query.filter_by(name=p["name"]).first():
                print(f"Product '{p['name']}' already exists, skipping.")
                continue
            image_path = os.path.join(static_images, p["image_filename"])
            if not os.path.isfile(image_path):
                print(f"Note: {p['image_filename']} not found in static/images. Product will still be created; set image_url in Admin if needed.")
            image_url = f"/api/images/{p['image_filename']}"

            product = Product(
                name=p["name"],
                description=p["description"],
                price=p["price"],
                category=p["category"],
                color=p["color"],
                size=p["size"],
                available_colors=json.dumps(p["available_colors"]),
                available_sizes=json.dumps(p["available_sizes"]),
                fabric=p["fabric"],
                clothing_type=p["clothing_type"],
                clothing_category=p["clothing_category"],
                occasion=p["occasion"],
                age_group=p["age_group"],
                season=p["season"],
                image_url=image_url,
                stock_quantity=50,
                is_active=True,
                sale_enabled=True,
                sale_start=sale_start,
                sale_end=sale_end,
                sale_percentage=p["sale_percentage"],
            )
            db.session.add(product)
            created += 1
            print(f"Added: {p['name']} at ${p['price']} with {p['sale_percentage']}% off until {sale_end}.")

        db.session.commit()
        print(f"Done. Created {created} special-offer product(s).")
        return created


if __name__ == "__main__":
    seed_special_offer_products()
