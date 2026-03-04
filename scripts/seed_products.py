"""Seed the database with detailed clothing products from 6 + 9 outfit images (apparel, belts, jewelry, accessories)."""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.database import db
from models.product import Product
from models.cart import CartItem
from models.order import OrderItem
from models.review import Review
from models.product_relation import ProductRelation
from models.wishlist import WishlistItem
from models.product_variation import ProductVariation
from datetime import date, timedelta
import random

# Products from 6 outfit images (image_index 1-6) and 9 new images (image_index 7-15)
PRODUCTS = [
    # --- Image 1: Indie/vintage — black tee, plaid bermuda shorts, belt, layered gold necklaces ---
    {
        "name": "Black Crew Neck T-Shirt",
        "description": "Plain solid black short-sleeved t-shirt with a classic crew neck. Soft, loose-fitting fabric that drapes casually. Standard-length sleeves, versatile minimalist basic. Unisex casual style. Cotton, jersey, or rayon blend; relaxed fit.",
        "price": 32,
        "category": "women",
        "color": "Black",
        "size": "M",
        "fabric": "Cotton Jersey",
        "clothing_type": "T-Shirt",
        "clothing_category": "t_shirts",
        "occasion": "casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 1,
    },
    {
        "name": "High-Waisted Plaid Bermuda Shorts",
        "description": "High-waisted shorts in a tartan-style plaid with dark teal/forest green and rust brown/orange, thin black grid lines. Soft front pleats, cuffed hem with contrasting dark blue inside. Above-knee length. Preppy, vintage smart-casual. Wool blend, flannel, or structured cotton twill.",
        "price": 72,
        "category": "women",
        "color": "Teal & Rust Plaid",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Shorts",
        "clothing_category": "pants",
        "occasion": "casual,date_night",
        "age_group": "young_adult",
        "season": "spring,summer",
        "image_index": 1,
        "sale_percentage": 25.0,
    },
    {
        "name": "Black Belt with Silver Square Buckle",
        "description": "Simple black belt with a sleek rectangular silver-tone metal buckle and clean lines. Smooth leather or faux leather strap. Classic minimalist waist accent for high-waisted bottoms.",
        "price": 36,
        "category": "women",
        "color": "Black",
        "size": "28",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 1,
    },
    {
        "name": "Layered Gold Necklace Set with Botanical Locket",
        "description": "Two-piece layered set: inner shorter delicate gold chain with small flat circular disc pendant; outer longer chunkier gold chain with larger circular locket-style pendant. Locket has clear front revealing pressed flowers or botanical insert in red, pink, and green. Bohemian vintage style; gold-plated or brass.",
        "price": 44,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 1,
    },
    # --- Image 2: Autumnal layered — turtleneck, ombre shirt, trousers, belt, heart necklace, ring ---
    {
        "name": "Black Ribbed Turtleneck",
        "description": "Long-sleeve turtleneck in solid black with fine vertical ribbed knit texture. Form-fitting on arms and neck, designed for layering. Sleeves extend beyond cuffs of outer shirt. Soft cotton or stretch blend.",
        "price": 42,
        "category": "women",
        "color": "Black",
        "size": "S",
        "fabric": "Cotton-Spandex Blend",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 2,
    },
    {
        "name": "Ombre Gradient Short-Sleeve Button-Up Shirt",
        "description": "Short-sleeved collared button-up with striking horizontal ombre: dark muted blue-grey at shoulders transitioning to earthy medium brown/tan, then rich rust/orange-brown at hem and wide batwing-style short sleeves. Loose oversized fit, point collar, button front. Lightweight flowing fabric—silk blend, rayon, or soft polyester.",
        "price": 68,
        "category": "women",
        "color": "Blue-Grey to Rust Ombre",
        "size": "L",
        "fabric": "Rayon Blend",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual,date_night",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 2,
        "sale_percentage": 20.0,
    },
    {
        "name": "Dark Brown High-Waisted Pleated Trousers",
        "description": "Rich dark brown high-waisted trousers with subtle sheen. Front pleats, tailored straight or wide leg. Smooth suiting or wool blend. Standard waistband with belt loops, clean finish. Smart-casual staple.",
        "price": 88,
        "category": "women",
        "color": "Dark Brown",
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
        "name": "Black Belt with Ornate Silver Buckle",
        "description": "Black leather or faux leather waist belt with prominent silver-toned ornate buckle—intricate engravings or Western-inspired design. Two decorative metal keepers. Worn cinched at natural waist.",
        "price": 40,
        "category": "women",
        "color": "Black",
        "size": "30",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 2,
    },
    {
        "name": "Gold Chain Necklace with Heart Pendant",
        "description": "Chunky irregular-link gold-toned chain with a small delicate heart-shaped pendant. Worn over turtleneck or base layers. Statement layering piece.",
        "price": 38,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 2,
    },
    {
        "name": "Silver Band Ring",
        "description": "Simple thin silver-toned band ring. Minimalist unisex accessory.",
        "price": 18,
        "category": "women",
        "color": "Silver",
        "size": "One Size",
        "fabric": "Metal",
        "clothing_type": "Ring",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 2,
    },
    # --- Image 3: Cropped plaid shirt, white tee, olive pleated trousers, layered necklaces ---
    {
        "name": "Cropped Plaid Short-Sleeve Button-Down Shirt",
        "description": "Casual boxy short-sleeved button-down with small tight plaid in khaki and light brown intersected by thin dark brown or black grid lines. Cropped length ending above navel, raw or roughly cut hem for deconstructed look. Button-down collar, white buttons, relaxed fit.",
        "price": 58,
        "category": "women",
        "color": "Khaki & Brown Plaid",
        "size": "M",
        "fabric": "Cotton",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "spring,summer",
        "image_index": 3,
        "sale_percentage": 15.0,
    },
    {
        "name": "White Crew-Neck Undershirt",
        "description": "Basic plain white short-sleeved t-shirt with classic crew neck. Standard comfortable fit. Visible at neckline and below cropped outer shirt. Cotton essential.",
        "price": 24,
        "category": "women",
        "color": "White",
        "size": "S",
        "fabric": "Cotton",
        "clothing_type": "T-Shirt",
        "clothing_category": "t_shirts",
        "occasion": "casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 3,
    },
    {
        "name": "High-Waisted Olive Green Pleated Trousers",
        "description": "Muted earthy olive green high-waisted trousers. Double front pleats, wide-leg relaxed fit. Linen or linen-blend. Button-tab closure on waistband, functional side entry pockets. Contemporary minimalist look.",
        "price": 82,
        "category": "women",
        "color": "Olive Green",
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
        "name": "Layered Gold-Tone Necklaces with Disc and Medallion",
        "description": "Layered delicate gold-toned necklaces: thinner chain with small flat circular pendant (coin or disc), plus slightly thicker chain with larger ornate medallion or charm. Worn above crew neck for a polished casual look.",
        "price": 42,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 3,
    },
    # --- Image 4: Olive oversized shirt, dark brown shorts, belt, bar necklace, watch, sunglasses ---
    {
        "name": "Olive Green Oversized Short-Sleeve Button-Up Shirt",
        "description": "Muted olive green casual oversized button-up. Classic pointed collar, short wide sleeves with neat cuff, rolled once or twice. Full button-down front with round white buttons; top buttons undone for relaxed look. Lightweight crisp cotton or cotton blend, tucked or untucked. Slightly gathered or puffed shoulder detail.",
        "price": 56,
        "category": "women",
        "color": "Olive Green",
        "size": "L",
        "fabric": "Cotton",
        "clothing_type": "Dress Shirt",
        "clothing_category": "shirts",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 4,
        "sale_percentage": 20.0,
    },
    {
        "name": "Dark Brown High-Waisted Pleated Shorts",
        "description": "Rich dark brown high-waisted tailored shorts. Double front pleats, relaxed wide-leg fit through thigh. Cuffed hem, mid-thigh length. Belt loops, side slash pockets. Medium-weight cotton twill, linen blend, or suiting fabric with subtle drape.",
        "price": 64,
        "category": "women",
        "color": "Dark Brown",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Shorts",
        "clothing_category": "pants",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 4,
    },
    {
        "name": "Black Thin Belt with Silver Oval Buckle",
        "description": "Thin minimalist black leather or faux leather belt with small sleek silver-colored oval or D-ring buckle. Classic waist accent for shorts or trousers.",
        "price": 32,
        "category": "women",
        "color": "Black",
        "size": "28",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 4,
    },
    {
        "name": "Gold-Toned Horizontal Bar Pendant Necklace",
        "description": "Delicate thin gold-toned chain with a small horizontal bar pendant. Minimalist everyday accessory.",
        "price": 28,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 4,
    },
    {
        "name": "Brown Multi-Wrap Leather Watch Strap",
        "description": "Multi-wrap thin brown leather strap worn on wrist—minimalist watch or layered bracelet style. Versatile accessory.",
        "price": 48,
        "category": "women",
        "color": "Brown",
        "size": "One Size",
        "fabric": "Leather",
        "clothing_type": "Watch",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 4,
    },
    {
        "name": "Black Sunglasses",
        "description": "Classic black-framed sunglasses. Timeless unisex style.",
        "price": 34,
        "category": "women",
        "color": "Black",
        "size": "One Size",
        "fabric": "Acetate",
        "clothing_type": "Sunglasses",
        "clothing_category": "other",
        "occasion": "casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 4,
    },
    # --- Image 5: Graphic tee, white collared shirt, black pleated trousers, belt, OK pendant ---
    {
        "name": "Black All-Seeing Eyes Graphic T-Shirt",
        "description": "Black short-sleeved crew-neck t-shirt with extensive repeating pattern of stylized eyes in various shapes, sizes, and expressions. White or light grey eyes with black outlines; anime/manga aesthetic with pupils, irises, lashes, and eyebrows. Relaxed or slightly oversized fit; sleeves reveal white shirt underneath. Cotton or cotton blend.",
        "price": 42,
        "category": "women",
        "color": "Black",
        "size": "M",
        "fabric": "Cotton",
        "clothing_type": "T-Shirt",
        "clothing_category": "t_shirts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "all_season",
        "image_index": 5,
        "sale_percentage": 15.0,
    },
    {
        "name": "White Layering Collared Shirt",
        "description": "Crisp white traditional collared button-down worn as a layer. Sharp pointed collar visible above graphic tee; long sleeves and cuffs extend beyond short sleeves of outer tee, neatly folded or rolled once. Cotton or poplin for crisp structure.",
        "price": 48,
        "category": "women",
        "color": "White",
        "size": "M",
        "fabric": "Cotton Poplin",
        "clothing_type": "Dress Shirt",
        "clothing_category": "shirts",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 5,
    },
    {
        "name": "Black High-Waisted Pleated Trousers",
        "description": "Solid black high-waisted trousers with distinct front pleats. Tailored relaxed straight or wide leg. Side pockets. Flowing yet structured drape—polyester blend, wool blend, or crepe.",
        "price": 78,
        "category": "women",
        "color": "Black",
        "size": "M",
        "fabric": "Polyester Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 5,
    },
    {
        "name": "Black Classic Belt with Silver Pin Buckle",
        "description": "Classic black leather or faux leather belt with rectangular silver-colored pin buckle and single loop for excess strap. Pairs with tailored trousers or jeans.",
        "price": 35,
        "category": "women",
        "color": "Black",
        "size": "30",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 5,
    },
    {
        "name": "Silver Ball Chain Necklace with OK Pendant",
        "description": "Thin silver ball chain with rectangular pendant—clear acrylic or resin with black outline illustration (minimalist character with speech bubble 'OK'). Anime-inspired statement piece. Stainless steel or silver-plated chain.",
        "price": 26,
        "category": "women",
        "color": "Silver",
        "size": "One Size",
        "fabric": "Stainless Steel & Acrylic",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "all_season",
        "image_index": 5,
    },
    # --- Image 6: Sheer floral blouse, brown turtleneck, beige trousers, belt, bead necklace ---
    {
        "name": "Sheer Floral Daisy Button-Up Blouse",
        "description": "Off-white or cream sheer lightweight blouse with delicate repeating floral or daisy motif in vertical rows—tiny dots forming petals around a central dot. Slightly crinkled texture. Button-up front with small white buttons, classic pointed collar, long slightly voluminous sleeves gathered at buttoned cuffs. Tucked into trousers. Cotton or synthetic blend with embroidered or woven pattern.",
        "price": 62,
        "category": "women",
        "color": "Off-White",
        "size": "M",
        "fabric": "Cotton Blend",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 6,
        "sale_percentage": 25.0,
    },
    {
        "name": "Brown Fitted Turtleneck",
        "description": "Warm medium brown or camel high-neck turtleneck, fitted to the body. Modest base layer under sheer blouse. Soft knit.",
        "price": 44,
        "category": "women",
        "color": "Brown",
        "size": "S",
        "fabric": "Cotton Knit",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 6,
    },
    {
        "name": "High-Waisted Beige Pleated Trousers",
        "description": "Light beige or tan high-waisted trousers with subtle color variation and textured weave. Prominent front pleats, relaxed tailored flow—wide-leg or straight. Linen-blend or slubby textured fabric for refined rustic look. Clean hem, belt loops.",
        "price": 86,
        "category": "women",
        "color": "Beige",
        "size": "M",
        "fabric": "Linen Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 6,
        "sale_percentage": 20.0,
    },
    {
        "name": "Dark Brown Leather Belt with Silver Buckle",
        "description": "Classic slim dark brown leather belt with visible stitching. Rectangular silver-toned metal buckle with single prong. Cinches waist for tailored looks.",
        "price": 38,
        "category": "women",
        "color": "Dark Brown",
        "size": "28",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 6,
    },
    {
        "name": "Gold-Toned Bead Necklace",
        "description": "Thin delicate gold-toned chain with a single small spherical bead or charm near the center. Resting just above neckline. Dainty minimalist accessory.",
        "price": 32,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 6,
    },
    # --- New products from 9 outfit images (image_index 7–15) ---
    {
        "name": "Muted Plaid Short-Sleeve Linen Shirt",
        "description": "Short-sleeve button-up with subtle muted plaid in light beige, faint light blue, and light reddish-brown on a beige base. Collar and placket in solid lighter beige or off-white linen. Relaxed fit, tucked style. Two light-colored round buttons. Linen or linen blend.",
        "price": 58,
        "category": "women",
        "color": "Beige & Light Blue Plaid",
        "size": "M",
        "fabric": "Linen Blend",
        "clothing_type": "Dress Shirt",
        "clothing_category": "shirts",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 7,
    },
    {
        "name": "High-Waisted Wide-Leg Pleated Linen Trousers",
        "description": "Olive green or khaki high-waisted trousers with textured linen weave. Prominent front pleats, wide-legged relaxed fit. Breathable, slightly rustic look. Side pockets.",
        "price": 84,
        "category": "women",
        "color": "Olive Green",
        "size": "M",
        "fabric": "Linen",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 7,
    },
    {
        "name": "Brown Leather Belt with Gold Rectangular Buckle",
        "description": "Wide solid brown leather belt with rectangular gold-toned or brass buckle. Threaded through belt loops, cinches the waist. Classic casual accent.",
        "price": 40,
        "category": "women",
        "color": "Brown",
        "size": "30",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 7,
    },
    {
        "name": "Olive Green Canvas Cross-Body Bag",
        "description": "Unstructured cross-body bag in olive green with thick canvas or webbing strap. Matches earth-tone outfits. Simple, roomy, casual.",
        "price": 52,
        "category": "women",
        "color": "Olive Green",
        "size": "One Size",
        "fabric": "Canvas",
        "clothing_type": "Bag",
        "clothing_category": "other",
        "occasion": "casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 7,
    },
    {
        "name": "Light Blue Long-Sleeve Button-Down Shirt",
        "description": "Light blue or baby blue long-sleeve button-down with two patch pockets on the chest. Lightweight linen or cotton blend, slightly wrinkled relaxed texture. Worn open over turtleneck; sleeves rolled. Open spread collar.",
        "price": 54,
        "category": "women",
        "color": "Light Blue",
        "size": "M",
        "fabric": "Cotton Blend",
        "clothing_type": "Dress Shirt",
        "clothing_category": "shirts",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 8,
    },
    {
        "name": "White Ribbed Turtleneck",
        "description": "White or off-white turtleneck with distinct ribbed knit texture. Long sleeves, comfortable stretch. Worn as a base layer under open shirts.",
        "price": 42,
        "category": "women",
        "color": "White",
        "size": "S",
        "fabric": "Cotton-Spandex Blend",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 8,
    },
    {
        "name": "Caramel Brown High-Waisted Trousers",
        "description": "Warm caramel brown high-waisted trousers. Soft flowing fabric, wool blend or similar drape. Wide-leg or straight-leg, relaxed yet sophisticated.",
        "price": 86,
        "category": "women",
        "color": "Caramel Brown",
        "size": "M",
        "fabric": "Wool Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 8,
    },
    {
        "name": "Black Belt with Gold Rectangular Buckle",
        "description": "Black leather or faux leather belt with classic rectangular metallic gold or brass buckle. Pairs with tailored trousers for smart casual look.",
        "price": 34,
        "category": "women",
        "color": "Black",
        "size": "28",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "business_casual,casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 8,
    },
    {
        "name": "Light Blue Knitted Polo Sweater",
        "description": "Soft pastel light blue long-sleeve knitted sweater in polo style. Classic polo collar and two-button placket. Fine rib or seed stitch, slightly oversized. Ribbed cuffs and hem. Cotton or wool blend.",
        "price": 62,
        "category": "women",
        "color": "Light Blue",
        "size": "M",
        "fabric": "Cotton Knit",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "fall,spring",
        "image_index": 9,
        "sale_percentage": 20.0,
    },
    {
        "name": "White Pleated Wide-Leg Trousers",
        "description": "Crisp white high-waisted wide-leg trousers with prominent front pleats. Subtle sheen, soft drape—satin, silk blend, or crepe. Flowing silhouette.",
        "price": 78,
        "category": "women",
        "color": "White",
        "size": "M",
        "fabric": "Silk Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 9,
    },
    {
        "name": "Dark Brown Leather Belt with Gold Buckle",
        "description": "Rich dark brown leather belt with large gold-toned rectangular buckle (rounded edges, single prong). Two small golden keeper loops. Slightly aged or brushed finish.",
        "price": 44,
        "category": "women",
        "color": "Dark Brown",
        "size": "30",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 9,
    },
    {
        "name": "Gold Curb Chain Necklace",
        "description": "Chunky statement gold chain necklace with curb or interlocking link design. Worn as a single piece for a polished look.",
        "price": 48,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 9,
    },
    {
        "name": "Gold Band Ring",
        "description": "Plain slender gold band ring. Minimalist unisex accessory.",
        "price": 22,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Metal",
        "clothing_type": "Ring",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 9,
    },
    {
        "name": "Pale Yellow Crew-Neck T-Shirt",
        "description": "Plain pale yellow or light beige short-sleeve t-shirt with rounded neckline. Soft cotton-like material, neat tuck. Relaxed minimalist staple.",
        "price": 28,
        "category": "women",
        "color": "Pale Yellow",
        "size": "M",
        "fabric": "Cotton",
        "clothing_type": "T-Shirt",
        "clothing_category": "t_shirts",
        "occasion": "casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 10,
    },
    {
        "name": "Olive Green Pleated Cuff Shorts",
        "description": "High-waisted olive or sage green shorts with prominent front pleats. Loose relaxed fit, cuffed hem. Sturdy chino or cotton twill. Side pockets.",
        "price": 58,
        "category": "women",
        "color": "Olive Green",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Shorts",
        "clothing_category": "pants",
        "occasion": "casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 10,
    },
    {
        "name": "Brown Leather Belt with Brass Buckle",
        "description": "Brown leather belt with rectangular brass or gold-toned buckle. Worn at the waist over shorts or trousers. Classic casual accent.",
        "price": 36,
        "category": "women",
        "color": "Brown",
        "size": "28",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 10,
    },
    {
        "name": "Gold Chain with Circular Embossed Pendant",
        "description": "Delicate gold chain with circular gold pendant featuring embossed coin or medallion design. Layering piece for casual and date looks.",
        "price": 38,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 10,
    },
    {
        "name": "Brown Rust Plaid Cropped Button-Down Shirt",
        "description": "Long-sleeve cropped button-down in rich brown or rust with subtle plaid of lighter orange-brown lines. Cropped length above waist, oversized fit. Small round orange-brown buttons. Modern casual layer.",
        "price": 64,
        "category": "women",
        "color": "Brown & Rust Plaid",
        "size": "M",
        "fabric": "Cotton Flannel",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual,date_night",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 11,
    },
    {
        "name": "Tan Beige Ribbed Turtleneck",
        "description": "Fitted turtleneck in solid light tan or beige with vertical ribbing. Slim silhouette, ideal under cropped shirts or alone. Soft cotton or blend.",
        "price": 44,
        "category": "women",
        "color": "Tan Beige",
        "size": "S",
        "fabric": "Cotton Knit",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 11,
    },
    {
        "name": "Brown High-Waisted Pleated Trousers with Button Flap",
        "description": "Medium to dark brown high-waisted trousers with visible front pleats (one per leg). Straight or wide-leg cut. Single round brown button closure and small decorative flap at waistband. Side pocket.",
        "price": 88,
        "category": "women",
        "color": "Brown",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 11,
    },
    {
        "name": "Gold Vintage Floral Pendant Necklace",
        "description": "Long gold chain with round pendant—clear or amber-tinted dome covering pressed flower, botanical, or miniature illustration. Antique delicate feel.",
        "price": 46,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 11,
    },
    {
        "name": "Cropped Plaid Gingham Shirt Short-Sleeve",
        "description": "Short-sleeve button-down in fine plaid or gingham—light brown/tan and dark brown/black. Cropped with raw or unfinished hem. Worn unbuttoned over turtleneck. Casual vintage vibe.",
        "price": 56,
        "category": "women",
        "color": "Tan & Dark Brown Plaid",
        "size": "M",
        "fabric": "Cotton",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 12,
    },
    {
        "name": "Black Long-Sleeve Turtleneck",
        "description": "Solid black long-sleeve turtleneck or mock neck. Sleeves extend beyond outer shirt. Versatile base layer.",
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
        "image_index": 12,
    },
    {
        "name": "Cognac Brown Pleated Trousers",
        "description": "Warm cognac or rust brown high-waisted pleated trousers. Loose wide-leg fit. Single brown button closure, belt loops. Side pockets. Relaxed drape.",
        "price": 82,
        "category": "women",
        "color": "Cognac Brown",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "fall",
        "image_index": 12,
    },
    {
        "name": "Gold Chain with Coin-Style Pendant",
        "description": "Long gold-toned chain with distinct circular pendant—intricate antique or coin-like design. Statement piece for layered looks.",
        "price": 42,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 12,
    },
    {
        "name": "Dark Olive Cropped Plaid Shirt",
        "description": "Loose long-sleeve button-up in dark olive or brown plaid with lighter tan or off-white grid lines. Cropped above waist, boxy silhouette. Classic collar, white buttons, single breast pocket. Worn unbuttoned over turtleneck.",
        "price": 66,
        "category": "women",
        "color": "Dark Olive & Tan Plaid",
        "size": "L",
        "fabric": "Cotton Flannel",
        "clothing_type": "Blouse",
        "clothing_category": "shirts",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 13,
    },
    {
        "name": "Light Brown Ribbed Turtleneck",
        "description": "Fitted high-neck turtleneck in solid light brown or tan with vertical ribbing. Warm neutral base layer.",
        "price": 44,
        "category": "women",
        "color": "Light Brown",
        "size": "S",
        "fabric": "Cotton Knit",
        "clothing_type": "Sweater",
        "clothing_category": "sweaters",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "fall,winter",
        "image_index": 13,
    },
    {
        "name": "Brown Pleated Wide-Leg Trousers",
        "description": "High-waisted wide-leg or straight-leg trousers in solid medium to dark brown. Prominent front pleats, relaxed fit. Waistband with button and belt loops.",
        "price": 85,
        "category": "women",
        "color": "Brown",
        "size": "M",
        "fabric": "Wool Blend",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "business_casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 13,
    },
    {
        "name": "Gold Locket with Floral Insert",
        "description": "Delicate gold chain with circular vintage-style locket. Inside: floral elements or miniature painting in red, orange, and green. Statement layering piece.",
        "price": 48,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 13,
    },
    {
        "name": "Light Yellow Beige Crew T-Shirt",
        "description": "Solid muted light yellow or beige short-sleeve crew-neck t-shirt. Soft drape, no pattern. Tucked styling. Modern casual.",
        "price": 26,
        "category": "women",
        "color": "Light Yellow",
        "size": "M",
        "fabric": "Cotton",
        "clothing_type": "T-Shirt",
        "clothing_category": "t_shirts",
        "occasion": "casual",
        "age_group": "all",
        "season": "spring,summer",
        "image_index": 14,
    },
    {
        "name": "Plaid High-Waisted Trousers Red Orange Beige",
        "description": "High-waisted trousers in bold plaid—vermillion/rust, orange, and beige/khaki with thin black grid lines. Relaxed fit. Statement casual piece.",
        "price": 72,
        "category": "women",
        "color": "Red, Orange & Beige Plaid",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Chinos",
        "clothing_category": "pants",
        "occasion": "casual,date_night",
        "age_group": "young_adult",
        "season": "fall",
        "image_index": 14,
    },
    {
        "name": "Black Belt with Silver Rectangular Buckle",
        "description": "Black leather belt with silver rectangular buckle. Worn at waist over plaid trousers. Minimalist accent.",
        "price": 32,
        "category": "women",
        "color": "Black",
        "size": "30",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 14,
    },
    {
        "name": "Gold Chain with Engraved Pendant",
        "description": "Thin gold chain with circular gold pendant featuring engraved profile or symbol. Delicate vintage-inspired accessory.",
        "price": 36,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 14,
    },
    {
        "name": "Maroon Burgundy Crew T-Shirt",
        "description": "Short-sleeve t-shirt in solid deep maroon or burgundy. Crew neck, relaxed fit, tucked into shorts. Versatile dark staple.",
        "price": 32,
        "category": "women",
        "color": "Maroon",
        "size": "M",
        "fabric": "Cotton",
        "clothing_type": "T-Shirt",
        "clothing_category": "t_shirts",
        "occasion": "casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 15,
    },
    {
        "name": "Plaid High-Waisted Shorts Beige Tan Red",
        "description": "High-waisted shorts in plaid—beige, tan, brown with thinner red or orange-red and dark blue or green lines. Pleats at waist, neatly cuffed hems. Tailored casual, preppy or dark academia vibe.",
        "price": 62,
        "category": "women",
        "color": "Beige, Tan & Red Plaid",
        "size": "M",
        "fabric": "Cotton Twill",
        "clothing_type": "Shorts",
        "clothing_category": "pants",
        "occasion": "casual",
        "age_group": "young_adult",
        "season": "spring,summer",
        "image_index": 15,
    },
    {
        "name": "Medium Brown Belt with Gold Buckle",
        "description": "Medium-brown leather or faux leather belt with simple rectangular or square gold-colored buckle. Cinches waist of shorts or trousers.",
        "price": 35,
        "category": "women",
        "color": "Brown",
        "size": "28",
        "fabric": "Leather",
        "clothing_type": "Belt",
        "clothing_category": "other",
        "occasion": "casual,business_casual",
        "age_group": "all",
        "season": "all_season",
        "image_index": 15,
    },
    {
        "name": "Layered Gold Necklaces with Medallion",
        "description": "Two layered gold-toned necklaces: shorter delicate chain and longer chain with round medallion-style pendant (embossed or engraved). Vintage preppy accent.",
        "price": 44,
        "category": "women",
        "color": "Gold",
        "size": "One Size",
        "fabric": "Gold-Plated Metal",
        "clothing_type": "Necklace",
        "clothing_category": "other",
        "occasion": "casual,date_night",
        "age_group": "all",
        "season": "all_season",
        "image_index": 15,
    },
]

# Size options by product type: different clothes have different sizes.
# Some products use a subset of sizes for variety (e.g. S/M/L only).
SIZE_CONFIG = {
    "T-Shirt": (["XS", "S", "M", "L", "XL"], False),
    "Blouse": (["XS", "S", "M", "L", "XL"], False),
    "Dress Shirt": (["XS", "S", "M", "L", "XL"], False),
    "Sweater": (["XS", "S", "M", "L", "XL"], False),
    "Shorts": (["26", "28", "30", "32"], False),
    "Chinos": (["26", "28", "30", "32"], False),
    "Belt": (["28", "30", "32"], False),
    "Necklace": (["One Size"], True),
    "Ring": (["One Size"], True),
    "Bag": (["One Size"], True),
    "Watch": (["One Size"], True),
    "Sunglasses": (["One Size"], True),
}
# Optional size subsets for variety: some products get only these instead of full set.
SIZE_SUBSETS_TOP = [
    ["XS", "S", "M", "L", "XL"],
    ["S", "M", "L", "XL"],
    ["S", "M", "L"],
    ["XS", "S", "M", "L"],
]
SIZE_SUBSETS_PANTS = [
    ["26", "28", "30", "32"],
    ["28", "30", "32"],
    ["26", "28", "30"],
]
DEFAULT_TOP_SIZES = (["XS", "S", "M", "L", "XL"], False)
DEFAULT_PANT_SIZES = (["26", "28", "30", "32"], False)
DEFAULT_ONE_SIZE = (["One Size"], True)

# Color options by product type: each product gets its primary color plus alternatives.
COLOR_CONFIG = {
    "T-Shirt": ["Black", "White", "Grey", "Navy", "Burgundy", "Olive Green", "Pale Yellow", "Light Blue", "Maroon"],
    "Blouse": ["White", "Off-White", "Black", "Light Blue", "Olive Green", "Tan", "Rust", "Beige & Light Blue Plaid", "Khaki & Brown Plaid"],
    "Dress Shirt": ["White", "Light Blue", "Olive Green", "Beige", "Pale Yellow", "Black", "Navy"],
    "Sweater": ["Black", "White", "Brown", "Light Blue", "Tan Beige", "Cream", "Grey", "Olive"],
    "Shorts": ["Olive Green", "Dark Brown", "Teal & Rust Plaid", "Beige", "Khaki", "Black", "Navy", "Beige, Tan & Red Plaid"],
    "Chinos": ["Dark Brown", "Olive Green", "Black", "Beige", "White", "Caramel Brown", "Brown", "Cognac Brown", "Red, Orange & Beige Plaid"],
    "Belt": ["Black", "Brown", "Dark Brown", "Tan", "Navy", "Burgundy"],
    "Necklace": ["Gold", "Silver", "Rose Gold", "Bronze", "Gunmetal"],
    "Ring": ["Gold", "Silver", "Rose Gold", "Bronze"],
    "Bag": ["Olive Green", "Black", "Brown", "Tan", "Navy"],
    "Watch": ["Brown", "Black", "Tan", "Navy", "Burgundy"],
    "Sunglasses": ["Black", "Brown", "Tortoise", "Navy", "Gold"],
}
DEFAULT_APPAREL_COLORS = ["Black", "White", "Navy", "Grey", "Brown", "Beige"]
DEFAULT_ACCESSORY_COLORS = ["Gold", "Silver", "Black", "Brown"]

# Single-word color names for stripping from names (trailing words and leading when no phrase matches).
SINGLE_WORD_COLORS = {
    "black", "white", "navy", "gold", "silver", "brown", "beige", "tan", "rust", "olive", "grey", "gray",
    "maroon", "burgundy", "red", "orange", "blue", "green", "yellow", "cream", "bronze", "gunmetal",
    "tortoise", "khaki", "cognac", "caramel", "teal", "pale", "light", "dark", "muted", "off-white",
}

# All known color phrases (for stripping from product names); longest first so we match "Cognac Brown" before "Brown".
_all_phrases = set()
for lst in list(COLOR_CONFIG.values()) + [DEFAULT_APPAREL_COLORS, DEFAULT_ACCESSORY_COLORS]:
    _all_phrases.update(c.strip() for c in lst if c and isinstance(c, str))
for w in SINGLE_WORD_COLORS:
    if w and len(w) > 1:
        _all_phrases.add(w.title())
ALL_KNOWN_COLOR_PHRASES = sorted(_all_phrases, key=lambda s: -len(s))


def get_available_colors_for_product(p, product_index=0):
    """Return a list of available colors for a product. Each product gets a different number
    of colors (2–6 for apparel, 1–4 for accessories). Primary color is always first."""
    primary = (p.get("color") or "").strip()
    clothing_type = p.get("clothing_type") or ""
    category = p.get("clothing_category") or "other"
    config = COLOR_CONFIG.get(clothing_type)
    if config is None:
        if category in ("t_shirts", "shirts", "sweaters", "pants"):
            config = DEFAULT_APPAREL_COLORS
        else:
            config = DEFAULT_ACCESSORY_COLORS
    # Vary count by product index so each product has different variety (deterministic per run).
    is_apparel = category in ("t_shirts", "shirts", "sweaters", "pants")
    if is_apparel:
        n_want = 2 + (product_index % 5)  # 2, 3, 4, 5, or 6 colors
    else:
        n_want = 1 + (product_index % 4)  # 1, 2, 3, or 4 colors for accessories
    n_want = min(n_want, len(config) + (1 if primary else 0))
    seen = set()
    result = []
    if primary and primary not in seen:
        result.append(primary)
        seen.add(primary)
    for c in config:
        if c and c not in seen and len(result) < n_want:
            result.append(c)
            seen.add(c)
    if not result and primary:
        result = [primary]
    return result


def get_sizes_and_stock_for_product(p, product_index=0):
    """Return (available_sizes list, size_stock dict, primary size) for a product seed entry.
    Different products get different size sets: full set or a subset (e.g. S/M/L only) for variety."""
    clothing_type = p.get("clothing_type") or ""
    category = p.get("clothing_category") or "other"
    config = SIZE_CONFIG.get(clothing_type)
    if config is None:
        if category in ("t_shirts", "shirts", "sweaters"):
            config = DEFAULT_TOP_SIZES
        elif category == "pants":
            config = DEFAULT_PANT_SIZES
        else:
            config = DEFAULT_ONE_SIZE
    size_labels_full, one_size = config
    # For apparel, pick a size subset so products have different size options (e.g. one has XS–XL, another S–L).
    if not one_size and size_labels_full:
        if category in ("t_shirts", "shirts", "sweaters"):
            size_labels = SIZE_SUBSETS_TOP[product_index % len(SIZE_SUBSETS_TOP)]
            size_labels = [s for s in size_labels if s in size_labels_full]
        elif category == "pants":
            size_labels = SIZE_SUBSETS_PANTS[product_index % len(SIZE_SUBSETS_PANTS)]
            size_labels = [s for s in size_labels if s in size_labels_full]
        else:
            size_labels = list(size_labels_full)
    else:
        size_labels = list(size_labels_full)
    if not size_labels:
        size_labels = list(size_labels_full)
    size_stock = {}
    for s in size_labels:
        size_stock[s] = random.randint(0, 18) if not one_size else random.randint(0, 40)
    primary = size_labels[0]
    for s in size_labels:
        if size_stock.get(s, 0) > 0:
            primary = s
            break
    return size_labels, size_stock, primary


def generate_slug(name, index):
    """Generate a unique URL-friendly slug."""
    slug = name.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    return f"{slug}-{index}"


def product_name_without_color(name, _color_hint=None):
    """Remove color from product name so the title is color-agnostic (colors are variation attributes).
    Strips any leading known color phrase and trailing single color words.
    E.g. 'Cognac Brown Pleated Trousers' -> 'Pleated Trousers'; 'Shorts Beige Tan Red' -> 'Shorts'."""
    if not name:
        return ""
    name_str = name.strip()
    if not name_str:
        return ""
    lower_name = name_str.lower()
    # Strip leading color phrases (longest first); repeat until no leading color matches
    changed = True
    while changed:
        changed = False
        for phrase in ALL_KNOWN_COLOR_PHRASES:
            if not phrase:
                continue
            lower_phrase = phrase.lower()
            if lower_name.startswith(lower_phrase):
                rest = name_str[len(phrase):].strip()
                if rest.startswith("-"):
                    rest = rest.lstrip("-").strip()
                if rest:
                    name_str = rest
                    lower_name = name_str.lower()
                    changed = True
                break
    # Strip trailing single-word colors (e.g. "Plaid Shorts Beige Tan Red" -> "Plaid Shorts")
    words = name_str.split()
    while words:
        last = words[-1].lower()
        last_clean = last.replace("-", " ")
        if last_clean in SINGLE_WORD_COLORS or last in SINGLE_WORD_COLORS:
            words.pop()
        else:
            break
    name_str = " ".join(words).strip()
    return name_str if name_str else name.strip()


def get_image_filename(image_index):
    """Return the image filename for this product (1–15)."""
    return f"product-{image_index}.png"


def seed_products():
    """Seed the database with detailed products from outfit imagery. Replaces any existing products."""
    with app.app_context():
        print("Starting to seed products...")

        # Remove dependent rows first (foreign keys to products)
        for model, label in [
            (CartItem, "cart items"),
            (OrderItem, "order items"),
            (Review, "reviews"),
            (ProductRelation, "product relations"),
            (WishlistItem, "wishlist items"),
        ]:
            try:
                n = model.query.delete()
                if n:
                    print(f"Removed {n} {label}.")
            except Exception as e:
                print(f"Note: could not clear {label}: {e}")
        ProductVariation.query.delete()
        db.session.commit()

        # Remove existing products so we have exactly these
        deleted = Product.query.delete()
        if deleted:
            print(f"Removed {deleted} existing product(s).")
        db.session.commit()

        static_images_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "static",
            "images",
        )
        for i in range(1, 16):
            path = os.path.join(static_images_dir, get_image_filename(i))
            if not os.path.exists(path):
                print(
                    f"Note: {get_image_filename(i)} not found in static/images. Add product images there for correct display."
                )

        today = date.today()
        sale_start = today - timedelta(days=1)
        sale_end = today + timedelta(days=30)

        # Shuffle so product order varies each seed run
        products_to_seed = list(PRODUCTS)
        random.shuffle(products_to_seed)

        for idx, p in enumerate(products_to_seed, start=1):
            image_url = f"/api/images/{get_image_filename(p['image_index'])}"

            sale_percentage = p.get("sale_percentage")
            sale_kw = {}
            if sale_percentage is not None:
                sale_kw = {
                    "sale_enabled": True,
                    "sale_start": sale_start,
                    "sale_end": sale_end,
                    "sale_percentage": float(sale_percentage),
                }

            # Different clothes have different sizes and colors; each product gets a varied set.
            available_sizes_list, size_stock_dict, primary_size = get_sizes_and_stock_for_product(p, product_index=idx)
            available_colors_list = get_available_colors_for_product(p, product_index=idx)

            # Name without any color so it works for all color variations.
            display_name = product_name_without_color(p["name"])
            default_color = available_colors_list[0] if available_colors_list else (p.get("color") or "")

            product = Product(
                name=display_name,
                description=p["description"],
                price=p["price"],
                category=p["category"],
                color=default_color,
                size=primary_size,
                available_sizes=json.dumps(available_sizes_list),
                size_stock=json.dumps(size_stock_dict),
                available_colors=json.dumps(available_colors_list),
                fabric=p["fabric"],
                clothing_type=p["clothing_type"],
                clothing_category=p["clothing_category"],
                occasion=p["occasion"],
                age_group=p["age_group"],
                season=p["season"],
                brand='other',
                image_url=image_url,
                stock_quantity=0,
                is_active=True,
                slug=generate_slug(display_name, idx),
                meta_title=f"{display_name} - InsightShop",
                meta_description=f"Shop {display_name} at InsightShop. {p['description'][:150]}...",
                **sale_kw,
            )
            db.session.add(product)
            db.session.flush()

            # Create one variation per (size, color) with its own stock
            def sku_safe(s):
                return "".join(c if c.isalnum() else "-" for c in str(s))[:15].strip("-") or "X"
            for vi, (size, color) in enumerate([(s, c) for s in available_sizes_list for c in available_colors_list]):
                qty = random.randint(0, 12) if size != "One Size" else random.randint(0, 25)
                sku = f"SKU-{product.id}-{sku_safe(size)}-{sku_safe(color)}-{vi}"
                var = ProductVariation(
                    product_id=product.id,
                    size=size,
                    color=color,
                    stock_quantity=qty,
                    sku=sku,
                )
                db.session.add(var)

        db.session.commit()
        print(f"Successfully created {len(PRODUCTS)} products with variations.")
        print("Product seeding completed! (Vector DB will sync in background.)")


if __name__ == "__main__":
    seed_products()
