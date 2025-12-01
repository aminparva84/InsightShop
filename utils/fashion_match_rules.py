"""Fashion Match Rules - Product matching for complete outfit suggestions."""

# Fashion matching rules: Primary Product -> Matched Product -> Match Type -> Priority
# Priority: 1 = High priority (essential matches), 2 = Secondary (nice-to-have)
FASHION_MATCH_RULES = [
    # Original 20 rules
    {"primary": "Blue Men's Oxford Shirt", "matched": "White Chinos/Pants", "match_type": "Complete Outfit", "priority": 1},
    {"primary": "Blue Men's Oxford Shirt", "matched": "Brown Leather Loafers", "match_type": "Complementary", "priority": 1},
    {"primary": "Black Cocktail Dress", "matched": "Silver Stiletto Heels", "match_type": "Formal Style", "priority": 1},
    {"primary": "Black Cocktail Dress", "matched": "Diamond-look Stud Earrings", "match_type": "Accessory", "priority": 2},
    {"primary": "Gray Business Suit", "matched": "Red Silk Tie", "match_type": "Color Pop", "priority": 1},
    {"primary": "Gray Business Suit", "matched": "Black Leather Belt", "match_type": "Essential", "priority": 2},
    {"primary": "Yellow Summer Sundress", "matched": "Woven Straw Sun Hat", "match_type": "Seasonal", "priority": 1},
    {"primary": "Yellow Summer Sundress", "matched": "White Flat Sandals", "match_type": "Complementary", "priority": 2},
    {"primary": "Dark Denim Jeans", "matched": "White T-Shirt", "match_type": "Classic Casual", "priority": 1},
    {"primary": "Dark Denim Jeans", "matched": "Black Combat Boots", "match_type": "Edgy Style", "priority": 2},
    {"primary": "Green Cargo Shorts", "matched": "Light Gray Crew Neck T-Shirt", "match_type": "Casual", "priority": 1},
    {"primary": "Green Cargo Shorts", "matched": "Canvas Slip-on Sneakers", "match_type": "Comfort", "priority": 2},
    {"primary": "Striped Navy Blazer", "matched": "Solid Light Blue Dress Shirt", "match_type": "Pattern Match", "priority": 1},
    {"primary": "Striped Navy Blazer", "matched": "Dark Brown Dress Shoes", "match_type": "Formal Wear", "priority": 2},
    {"primary": "Cream Cable Knit Sweater", "matched": "Medium-Wash Straight Leg Jeans", "match_type": "Cozy Look", "priority": 1},
    {"primary": "Cream Cable Knit Sweater", "matched": "Suede Ankle Boots", "match_type": "Winter Style", "priority": 2},
    {"primary": "Floral Print Skirt", "matched": "Solid Pink Blouse", "match_type": "Color Harmony", "priority": 1},
    {"primary": "Floral Print Skirt", "matched": "Delicate Gold Pendant Necklace", "match_type": "Accessory", "priority": 2},
    {"primary": "Athletic Black Leggings", "matched": "Bright Pink Running Shoes", "match_type": "Gym Wear", "priority": 1},
    {"primary": "Athletic Black Leggings", "matched": "Moisture-Wicking Sports Bra", "match_type": "Complete Set", "priority": 2},
    
    # Additional 20 rules
    {"primary": "Navy Blazer", "matched": "Khaki Chinos", "match_type": "Smart Casual", "priority": 1},
    {"primary": "Navy Blazer", "matched": "White Dress Shirt", "match_type": "Classic Combination", "priority": 1},
    {"primary": "Red Floral Summer Dress", "matched": "Tan Wedge Sandals", "match_type": "Seasonal", "priority": 1},
    {"primary": "Red Floral Summer Dress", "matched": "Straw Tote Bag", "match_type": "Accessory", "priority": 2},
    {"primary": "Black Leather Jacket", "matched": "Dark Wash Skinny Jeans", "match_type": "Edgy Style", "priority": 1},
    {"primary": "Black Leather Jacket", "matched": "Black Ankle Boots", "match_type": "Complete Outfit", "priority": 1},
    {"primary": "White Button-Down Shirt", "matched": "Black Trousers", "match_type": "Professional", "priority": 1},
    {"primary": "White Button-Down Shirt", "matched": "Navy Blazer", "match_type": "Business Casual", "priority": 2},
    {"primary": "Plaid Flannel Shirt", "matched": "Dark Denim Jeans", "match_type": "Casual", "priority": 1},
    {"primary": "Plaid Flannel Shirt", "matched": "Brown Work Boots", "match_type": "Rustic Style", "priority": 2},
    {"primary": "Little Black Dress", "matched": "Black Pumps", "match_type": "Classic", "priority": 1},
    {"primary": "Little Black Dress", "matched": "Pearl Necklace", "match_type": "Elegant Accessory", "priority": 2},
    {"primary": "Olive Green Cargo Pants", "matched": "Black T-Shirt", "match_type": "Military Style", "priority": 1},
    {"primary": "Olive Green Cargo Pants", "matched": "Black Combat Boots", "match_type": "Tactical Look", "priority": 2},
    {"primary": "Pink Blouse", "matched": "White Pencil Skirt", "match_type": "Office Chic", "priority": 1},
    {"primary": "Pink Blouse", "matched": "Nude Heels", "match_type": "Professional", "priority": 2},
    {"primary": "Blue Denim Jacket", "matched": "White T-Shirt", "match_type": "Classic Casual", "priority": 1},
    {"primary": "Blue Denim Jacket", "matched": "Blue Jeans", "match_type": "Denim on Denim", "priority": 2},
    {"primary": "Beige Trench Coat", "matched": "Black Dress", "match_type": "Timeless", "priority": 1},
    {"primary": "Beige Trench Coat", "matched": "Black Ankle Boots", "match_type": "Fall Style", "priority": 2},
]

# Keywords for matching products (for flexible matching)
MATCH_KEYWORDS = {
    "shirt": ["shirt", "blouse", "top", "tee", "t-shirt"],
    "dress": ["dress", "gown", "frock"],
    "pants": ["pants", "trousers", "chinos", "slacks"],
    "jeans": ["jeans", "denim"],
    "shoes": ["shoes", "sneakers", "boots", "heels", "sandals", "loafers", "pumps"],
    "jacket": ["jacket", "blazer", "coat"],
    "sweater": ["sweater", "cardigan", "pullover"],
    "shorts": ["shorts"],
    "skirt": ["skirt"],
    "accessories": ["belt", "necklace", "earrings", "hat", "bag", "tie"],
}

def find_matching_products(primary_product_name, primary_product_id=None):
    """
    Find matching products for a given primary product.
    
    Args:
        primary_product_name: Name of the primary product
        primary_product_id: Optional ID of the primary product
    
    Returns:
        List of matching product suggestions with match types and priorities
    """
    matches = []
    primary_lower = primary_product_name.lower()
    
    # Find exact or partial matches in rules
    for rule in FASHION_MATCH_RULES:
        if rule["primary"].lower() in primary_lower or primary_lower in rule["primary"].lower():
            matches.append({
                "matched_product": rule["matched"],
                "match_type": rule["match_type"],
                "priority": rule["priority"]
            })
    
    # If no exact matches, try keyword-based matching
    if not matches:
        matches = find_matches_by_keywords(primary_product_name)
    
    # Sort by priority (1 = high priority first)
    matches.sort(key=lambda x: x["priority"])
    
    # Return top 3-4 matches
    return matches[:4]

def find_matches_by_keywords(product_name):
    """Find matches based on product type keywords."""
    product_lower = product_name.lower()
    matches = []
    
    # Determine product type
    product_type = None
    for key, keywords in MATCH_KEYWORDS.items():
        if any(keyword in product_lower for keyword in keywords):
            product_type = key
            break
    
    if not product_type:
        return []
    
    # Find complementary items based on product type
    for rule in FASHION_MATCH_RULES:
        rule_primary_lower = rule["primary"].lower()
        
        # Check if rule's primary product matches our product type
        if any(keyword in rule_primary_lower for keyword in MATCH_KEYWORDS.get(product_type, [])):
            # Check if this rule's matched product is a good complement
            matched_lower = rule["matched"].lower()
            
            # Skip if matched product is same type (unless it's accessories)
            if product_type != "accessories" and any(kw in matched_lower for kw in MATCH_KEYWORDS.get(product_type, [])):
                continue
            
            matches.append({
                "matched_product": rule["matched"],
                "match_type": rule["match_type"],
                "priority": rule["priority"]
            })
    
    return matches

def get_match_explanation(match_type):
    """Get explanation text for different match types."""
    explanations = {
        "Complete Outfit": "These are essential for creating a complete, polished look.",
        "Complementary": "These complement your item perfectly, creating a harmonious color palette.",
        "Formal Style": "Perfect for formal occasions and professional settings.",
        "Accessory": "Adds the perfect finishing touch to complete your look.",
        "Color Pop": "Adds a vibrant accent color to make your outfit stand out.",
        "Essential": "A must-have piece that ties the whole outfit together.",
        "Seasonal": "Perfect for the current season and weather.",
        "Classic Casual": "A timeless combination that never goes out of style.",
        "Edgy Style": "Creates a bold, modern look with attitude.",
        "Casual": "Great for everyday comfort and relaxed settings.",
        "Comfort": "Prioritizes comfort without sacrificing style.",
        "Pattern Match": "Coordinates beautifully with patterns and textures.",
        "Formal Wear": "Ideal for business and formal events.",
        "Cozy Look": "Creates a warm, comfortable, and inviting style.",
        "Winter Style": "Perfect for colder weather and layering.",
        "Color Harmony": "Creates a beautiful, balanced color scheme.",
        "Gym Wear": "Designed for active wear and workouts.",
        "Complete Set": "All pieces work together for a cohesive look.",
        "Smart Casual": "Perfect balance between casual and professional.",
        "Classic Combination": "A tried-and-true pairing that always works.",
        "Professional": "Ideal for office and business environments.",
        "Business Casual": "Perfect for modern workplace settings.",
        "Rustic Style": "Creates a rugged, outdoorsy aesthetic.",
        "Classic": "Timeless elegance that never goes out of style.",
        "Elegant Accessory": "Adds sophistication and refinement.",
        "Military Style": "Bold, structured look with tactical appeal.",
        "Tactical Look": "Functional and stylish for active lifestyles.",
        "Office Chic": "Professional yet fashionable for the workplace.",
        "Denim on Denim": "A bold fashion statement that works when done right.",
        "Timeless": "Classic style that transcends trends.",
        "Fall Style": "Perfect for autumn weather and colors.",
    }
    
    return explanations.get(match_type, "These pieces work beautifully together to create a stylish look.")

