"""Seed the database with 20 detailed clothing products (inspired by curated outfit imagery)."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.product import Product
from models.cart import CartItem
from models.order import OrderItem
from models.review import Review
from models.product_relation import ProductRelation
import random

# 20 products with distinct details and colors; each uses one of 6 outfit images
PRODUCTS = [
    {
        "name": "Cropped Plaid Button-Up Shirt with Raw Hem",
        "description": "Long-sleeve button-up with a classic plaid in dark olive and tan. Features a raw, unfinished hem for a deconstructed look, contrast dark collar (velvet-style), light beige buttons, and an oversized relaxed fit. Cotton or flannel weave.",
        "price": 68,
        "category": "women",
        "color": "Dark Olive & Tan Plaid",
        "size": "M",
        "fabric": "Cotton Flannel",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual,date_night",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 1,
    },
    {
        "name": "High-Waisted Pleated Trousers",
        "description": "Tailored high-waist trousers in warm sienna brown. Double front pleats, relaxed wide-leg fit, smooth cotton twill or suiting blend. Single brown button and hidden hook closure, side pockets, clean crease.",
        "price": 89,
        "category": "women",
        "color": "Sienna Brown",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 1,
    },
    {
        "name": "Ribbed Mock-Neck Sweater",
        "description": "Light beige ribbed turtleneck with vertical knit texture. Slim fit, ideal for layering under shirts or alone. Soft cotton or cotton-blend knit.",
        "price": 45,
        "category": "women",
        "color": "Light Beige",
        "size": "S",
        "fabric": "Cotton Knit",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 2,
    },
    {
        "name": "Cropped Plaid Flannel Shirt",
        "description": "Rich brown base with thin orange-brown and rust grid lines. Cropped hem, worn open as a layer. Small rust-toned buttons, relaxed sleeves and body. Lightweight cotton or flannel.",
        "price": 62,
        "category": "women",
        "color": "Brown & Rust Plaid",
        "size": "L",
        "fabric": "Cotton Flannel",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 2,
    },
    {
        "name": "Pleated Wide-Leg Trousers in Camel",
        "description": "High-waisted trousers in solid camel. Prominent front pleats, relaxed leg, smooth drape. Wool, linen blend, or suiting fabric. Button closure at waist.",
        "price": 95,
        "category": "women",
        "color": "Camel",
        "size": "M",
        "fabric": "Wool Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 2,
    },
    {
        "name": "Gold Locket Pendant Necklace",
        "description": "Delicate gold-toned chain with a circular locket-style pendant. Resin or glass encased design with floral or miniature artwork. Statement layering piece.",
        "price": 38,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Metal & Resin",
        "clothing_type": "Blouse",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 2,
    },
    {
        "name": "Short-Sleeve Plaid Linen Shirt",
        "description": "Light beige and oatmeal base with subtle plaid in light blue and faint reddish-brown. Camp collar, half-placket with single mother-of-pearl button. Linen or linen-blend, relaxed fit.",
        "price": 58,
        "category": "men",
        "color": "Oatmeal & Light Blue Plaid",
        "size": "L",
        "fabric": "Linen Blend",
        "clothing_type": "Polo Shirt",
        "clothing_category": "shirts",
        "occasion": "casual,summer",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 3,
    },
    {
        "name": "High-Waisted Pleated Olive Trousers",
        "description": "Olive green or khaki high-waisted trousers. Front pleats, wide-leg, linen or linen-blend. Side pockets, relaxed drape. Earthy, minimalist look.",
        "price": 82,
        "category": "men",
        "color": "Olive Khaki",
        "size": "M",
        "fabric": "Linen Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 3,
    },
    {
        "name": "Leather Belt with Brass Buckle",
        "description": "Dark brown leather belt with a substantial rectangular brass or gold-toned buckle. Classic waist accent for high-waisted trousers or jeans.",
        "price": 42,
        "category": "men",
        "color": "Dark Brown",
        "size": "32",
        "fabric": "Leather",
        "clothing_type": "Suit",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 3,
    },
    {
        "name": "Olive Cross-Body Bag",
        "description": "Soft unstructured cross-body bag in olive green or khaki. Wide fabric webbing strap, matches earth-tone outfits. Roomy and casual.",
        "price": 55,
        "category": "women",
        "color": "Olive Green",
        "size": "One Size",
        "fabric": "Canvas / Fabric",
        "clothing_type": "Blouse",
        "clothing_category": "other",
        "occasion": "casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 3,
    },
    {
        "name": "Light Blue Button-Up Shirt",
        "description": "Soft pastel light blue collared shirt with two chest pockets and flaps. Lightweight cotton or linen-like fabric, relaxed drape. Wear open over a turtleneck or buttoned. Sleeves roll to elbow.",
        "price": 52,
        "category": "women",
        "color": "Light Blue",
        "size": "M",
        "fabric": "Cotton Blend",
        "clothing_type": "Dress Shirt",
        "clothing_category": "shirts",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 4,
    },
    {
        "name": "Ribbed Cream Turtleneck",
        "description": "Cream or off-white ribbed turtleneck with a close fit. Vertical rib knit, long sleeves. Perfect under blazers or open shirts. Cotton or stretch blend.",
        "price": 44,
        "category": "women",
        "color": "Cream White",
        "size": "S",
        "fabric": "Cotton-Spandex Blend",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 4,
    },
    {
        "name": "Tailored Chocolate Brown Trousers",
        "description": "Rich chocolate or caramel brown high-waisted trousers. Straight or wide leg, smooth suiting or wool blend. Belt loops, clean finish. Smart casual staple.",
        "price": 88,
        "category": "women",
        "color": "Chocolate Brown",
        "size": "M",
        "fabric": "Wool Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 4,
    },
    {
        "name": "Black Belt with Gold Buckle",
        "description": "Classic black leather strap with a simple rectangular gold or brass buckle. Thin profile, pairs with tailored trousers or jeans.",
        "price": 35,
        "category": "women",
        "color": "Black",
        "size": "28",
        "fabric": "Leather",
        "clothing_type": "Suit",
        "clothing_category": "other",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 4,
    },
    {
        "name": "Cropped Micro-Check Short-Sleeve Shirt",
        "description": "Beige and light brown base with fine black or dark brown grid. Short sleeves, cropped length, raw or unfinished hem. Relaxed fit, collared, full button front. Deconstructed casual look.",
        "price": 56,
        "category": "women",
        "color": "Beige & Black Micro-Check",
        "size": "M",
        "fabric": "Cotton",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "spring,summer",
        "image_index": 5,
    },
    {
        "name": "Black Fitted Turtleneck",
        "description": "Solid black close-fitting turtleneck. Long sleeves, smooth knit or jersey. Ideal base layer under cropped shirts or blazers.",
        "price": 40,
        "category": "women",
        "color": "Black",
        "size": "S",
        "fabric": "Cotton Jersey",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 5,
    },
    {
        "name": "High-Waisted Pleated Trousers in Rust",
        "description": "Warm reddish-brown (rust or camel) high-waisted trousers. Front pleats, relaxed fit through hip and thigh, slight taper. Neat waistband with button closure. Side pockets.",
        "price": 86,
        "category": "women",
        "color": "Rust Brown",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "fall",
        "image_index": 5,
    },
    {
        "name": "Gold Circular Pendant Necklace",
        "description": "Long gold chain with a large circular pendant—locket or artistic medallion with intricate design. Statement accessory for layered looks.",
        "price": 48,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Metal",
        "clothing_type": "Blouse",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 5,
    },
    {
        "name": "Oversized Cropped Plaid Shirt",
        "description": "Dark olive or forest green base with subtle plaid in light brown and tan. Oversized fit, cropped hem, long sleeves, single chest pocket. Lightweight cotton or flannel. Unbuttoned layering piece.",
        "price": 64,
        "category": "women",
        "color": "Dark Olive & Tan Plaid",
        "size": "L",
        "fabric": "Cotton Flannel",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 6,
    },
    {
        "name": "Tan Ribbed Turtleneck",
        "description": "Warm tan or camel ribbed turtleneck. Fitted, vertical knit texture. Pairs with plaid shirts and high-waisted trousers. Soft cotton or blend.",
        "price": 46,
        "category": "women",
        "color": "Tan Camel",
        "size": "M",
        "fabric": "Cotton Knit",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 6,
    },
]


def generate_slug(name, index):
    """Generate a unique URL-friendly slug."""
    slug = name.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    return f"{slug}-{index}"


def get_image_filename(image_index):
    """Return the image filename for this product (1–6)."""
    return f"product-{image_index}.png"


def seed_products():
    """Seed the database with 20 detailed products. Replaces any existing products."""
    with app.app_context():
        print("Starting to seed products...")

        # Remove dependent rows first (foreign keys to products)
        for model, label in [
            (CartItem, "cart items"),
            (OrderItem, "order items"),
            (Review, "reviews"),
            (ProductRelation, "product relations"),
        ]:
            try:
                n = model.query.delete()
                if n:
                    print(f"Removed {n} {label}.")
            except Exception as e:
                print(f"Note: could not clear {label}: {e}")
        db.session.commit()

        # Remove existing products so we have exactly these 20
        deleted = Product.query.delete()
        if deleted:
            print(f"Removed {deleted} existing product(s).")
        db.session.commit()

        static_images_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "static",
            "images",
        )
        for i in range(1, 7):
            path = os.path.join(static_images_dir, get_image_filename(i))
            if not os.path.exists(path):
                print(
                    f"Note: {get_image_filename(i)} not found in static/images. Add product images there for correct display."
                )

        for idx, p in enumerate(PRODUCTS, start=1):
            slug = generate_slug(p["name"], idx)
            image_url = f"/api/images/{get_image_filename(p['image_index'])}"

            product = Product(
                name=p["name"],
                description=p["description"],
                price=p["price"],
                category=p["category"],
                color=p["color"],
                size=p["size"],
                fabric=p["fabric"],
                clothing_type=p["clothing_type"],
                clothing_category=p["clothing_category"],
                occasion=p["occasion"],
                age_group=p["age_group"],
                season=p["season"],
                image_url=image_url,
                stock_quantity=random.randint(8, 40),
                is_active=True,
                slug=slug,
                meta_title=f"{p['name']} - InsightShop",
                meta_description=f"Shop {p['name']} at InsightShop. {p['description'][:150]}...",
            )
            db.session.add(product)

        db.session.commit()
        print(f"Successfully created {len(PRODUCTS)} products.")
        print("Product seeding completed! (Vector DB will sync in background.)")


if __name__ == "__main__":
    seed_products()
