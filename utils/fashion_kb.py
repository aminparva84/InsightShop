"""Fashion Knowledge Base for AI Agent - Style, Color Matching, and Occasions."""

FASHION_KNOWLEDGE_BASE = {
    "color_matching": {
        "basics": """
Color coordination is essential for creating polished outfits. Here are the fundamentals:

NEUTRAL COLORS (go with everything):
- Black, White, Gray, Navy, Beige, Brown, Khaki
- These are your foundation pieces - they pair with any color

COMPLEMENTARY COLORS (opposites on color wheel):
- Red & Green, Blue & Orange, Yellow & Purple
- Use sparingly for bold statements

ANALOGOUS COLORS (next to each other on color wheel):
- Blue & Green, Red & Orange, Yellow & Green
- Creates harmonious, cohesive looks

MONOCHROMATIC (same color family):
- Different shades of the same color
- Creates sophisticated, elegant looks

CLASSIC COMBINATIONS:
- Navy & White: Timeless, crisp, professional
- Black & White: Bold, modern, versatile
- Gray & Blue: Sophisticated, professional
- Beige & Brown: Warm, earthy, elegant
- Red & Navy: Classic, preppy, confident
- Pink & Gray: Soft, feminine, modern
        """,
        
        "by_color": {
            "black": "Black is the ultimate neutral. It pairs with everything - white, gray, navy, red, pink, yellow, and all bright colors. Perfect for creating contrast and sophistication.",
            "white": "White is fresh and versatile. Pairs beautifully with black, navy, gray, pastels, and bold colors. Great for summer and creating a clean, crisp look.",
            "navy": "Navy is sophisticated and professional. Complements white, beige, gray, red, pink, yellow, and light blue. More versatile than black for business settings.",
            "gray": "Gray is a modern neutral. Works with black, white, navy, pastels, and bright colors. Perfect for creating subtle, elegant combinations.",
            "beige": "Beige is warm and elegant. Pairs with navy, brown, white, black, and earth tones. Creates sophisticated, timeless looks.",
            "red": "Red is bold and confident. Complements navy, white, black, gray, and beige. Use as an accent or statement piece.",
            "blue": "Blue is calming and versatile. Pairs with white, gray, navy, beige, and complementary colors like orange or yellow.",
            "green": "Green is fresh and natural. Complements beige, brown, white, navy, and earth tones. Great for casual and outdoor occasions.",
            "pink": "Pink is feminine and soft. Pairs with gray, navy, white, black, and complementary colors. Perfect for spring and summer.",
            "yellow": "Yellow is cheerful and bright. Complements navy, white, gray, and black. Use as an accent for energy and positivity.",
            "brown": "Brown is earthy and warm. Pairs with beige, cream, white, navy, and green. Creates cozy, autumnal looks.",
            "purple": "Purple is regal and creative. Complements gray, white, black, and yellow. Great for adding sophistication to an outfit."
        }
    },
    
    "style_advice": {
        "fit": """
Proper fit is the foundation of great style:
- Clothes should skim the body, not cling or hang
- Shoulders should align with garment seams
- Pants should break slightly at the shoe
- Shirts should allow for comfortable movement
- Tailoring can transform any garment
        """,
        
        "layering": """
Layering adds depth and versatility:
- Start with a base layer (tank, t-shirt, camisole)
- Add a middle layer (button-down, sweater, cardigan)
- Finish with outer layer (jacket, blazer, coat)
- Mix textures and weights for interest
- Use neutral base layers for versatility
        """,
        
        "proportions": """
Balance is key to flattering proportions:
- Pair fitted tops with looser bottoms (or vice versa)
- High-waisted pants elongate the legs
- V-necks create length in the torso
- Belts define the waist and add structure
- Avoid matching loose with loose or tight with tight
        """
    },
    
    "occasions": {
        "business_formal": """
Business formal requires polished, professional attire:
- Men: Suit (navy, charcoal, or black), dress shirt, tie, dress shoes
- Women: Suit or tailored dress, blazer, closed-toe heels, minimal accessories
- Colors: Navy, black, gray, white
- Fabrics: Wool, cotton, silk
- Avoid: Casual fabrics, bright colors, sneakers, denim
        """,
        
        "business_casual": """
Business casual balances professionalism with comfort:
- Men: Chinos or dress pants, button-down shirt, blazer (optional), dress shoes or loafers
- Women: Dress pants or skirt, blouse or sweater, blazer or cardigan, flats or low heels
- Colors: Navy, gray, beige, white, subtle patterns
- Fabrics: Cotton, wool blends, chinos
- Avoid: Jeans, t-shirts, sneakers, overly casual items
        """,
        
        "casual": """
Casual wear is comfortable and relaxed:
- Men: Jeans or chinos, t-shirt or polo, sneakers or casual shoes, hoodie or sweater
- Women: Jeans or leggings, t-shirt or blouse, sneakers or flats, cardigan or jacket
- Colors: Any colors work, more freedom for expression
- Fabrics: Cotton, denim, jersey, fleece
- Perfect for: Weekends, errands, casual outings
        """,
        
        "date_night": """
Date night calls for elevated, romantic styling:
- Men: Dark jeans or chinos, button-down or polo, blazer, dress shoes
- Women: Dress or nice top with skirt/pants, heels or nice flats, statement jewelry
- Colors: Navy, black, burgundy, deep colors, or soft pastels
- Fabrics: Silk, satin, nice cotton, wool
- Add: A touch of sophistication without being overdressed
        """,
        
        "wedding": """
Wedding attire depends on the dress code:
- Formal: Suit or formal dress, elegant accessories
- Semi-formal: Dress or suit, polished but not overly formal
- Casual: Nice dress or separates, comfortable but put-together
- Colors: Avoid white (unless specified), choose colors that complement the wedding theme
- Fabrics: Elegant fabrics appropriate for the season
        """,
        
        "outdoor_active": """
Outdoor and active wear prioritizes function and comfort:
- Men: Athletic wear, moisture-wicking fabrics, comfortable shoes, layers
- Women: Athletic wear, leggings or shorts, supportive shoes, layers
- Colors: Bright colors for visibility, or earth tones for nature
- Fabrics: Polyester blends, spandex, technical fabrics
- Features: Breathable, moisture-wicking, UV protection
        """,
        
        "summer": """
Summer styling is light and breathable:
- Light colors: White, pastels, light blue, beige
- Light fabrics: Linen, cotton, lightweight blends
- Styles: Shorts, dresses, light layers
- Accessories: Sun hats, sunglasses, sandals
- Avoid: Heavy fabrics, dark colors, layers
        """,
        
        "winter": """
Winter styling is warm and layered:
- Rich colors: Navy, burgundy, forest green, charcoal
- Warm fabrics: Wool, cashmere, fleece, down
- Layers: Base layer, sweater, jacket/coat
- Accessories: Scarves, gloves, boots
- Features: Insulation, wind resistance, water resistance
        """
    },
    
    "fabric_guide": {
        "cotton": {
            "description": "100% Cotton is breathable, soft, and comfortable. Perfect for everyday wear, especially in warm weather.",
            "care": "Machine washable, may shrink slightly. Iron on medium heat.",
            "best_for": "T-shirts, casual shirts, summer clothing, everyday wear",
            "characteristics": "Absorbs moisture, natural fiber, durable, easy to care for"
        },
        "polyester": {
            "description": "Polyester is durable, wrinkle-resistant, and quick-drying. Often blended with other fibers for better properties.",
            "care": "Machine washable, low maintenance, dries quickly",
            "best_for": "Activewear, outerwear, blends for durability",
            "characteristics": "Wrinkle-resistant, moisture-wicking, durable, easy care"
        },
        "wool": {
            "description": "Wool is warm, naturally insulating, and breathable. Excellent for cold weather and professional attire.",
            "care": "Dry clean or gentle hand wash, air dry flat",
            "best_for": "Sweaters, suits, coats, winter clothing",
            "characteristics": "Warm, insulating, naturally wrinkle-resistant, odor-resistant"
        },
        "silk": {
            "description": "Silk is luxurious, smooth, and elegant. Perfect for special occasions and formal wear.",
            "care": "Dry clean or gentle hand wash, air dry, avoid direct sunlight",
            "best_for": "Dresses, blouses, formal wear, special occasions",
            "characteristics": "Luxurious feel, elegant drape, temperature-regulating, delicate"
        },
        "linen": {
            "description": "Linen is breathable, lightweight, and perfect for summer. Natural wrinkles are part of its charm.",
            "care": "Machine washable, air dry, wrinkles easily (embrace it!)",
            "best_for": "Summer clothing, casual wear, warm weather",
            "characteristics": "Highly breathable, lightweight, natural, casual elegance"
        },
        "denim": {
            "description": "Denim is durable, versatile, and timeless. The foundation of casual American style.",
            "care": "Machine washable, wash inside out to preserve color, air dry or low heat",
            "best_for": "Jeans, jackets, casual wear, everyday style",
            "characteristics": "Durable, versatile, gets better with age, classic"
        },
        "cashmere": {
            "description": "Cashmere is ultra-soft, luxurious, and warm. The premium choice for sweaters and accessories.",
            "care": "Dry clean or gentle hand wash, lay flat to dry",
            "best_for": "Sweaters, scarves, luxury items, cold weather",
            "characteristics": "Ultra-soft, lightweight warmth, luxurious, premium"
        },
        "blend": {
            "description": "Fabric blends combine the best properties of different fibers. Common blends include cotton-polyester for durability and comfort.",
            "care": "Follow care instructions for primary fiber, usually machine washable",
            "best_for": "Versatile everyday wear, combining comfort and durability",
            "characteristics": "Best of multiple fibers, often more durable and easier to care for"
        }
    },
    
    "styling_tips": {
        "build_wardrobe": """
Building a versatile wardrobe:
1. Start with neutrals: Black, white, navy, gray, beige
2. Add quality basics: Well-fitting jeans, white t-shirt, button-down shirt
3. Invest in key pieces: Good blazer, quality shoes, versatile dress
4. Add color gradually: Start with one or two favorite colors
5. Mix price points: Invest in items you'll wear often, save on trends
        """,
        
        "accessories": """
Accessories elevate any outfit:
- Shoes: Quality shoes make the outfit
- Belts: Define waist and add polish
- Jewelry: Less is more, choose statement or minimal
- Bags: Should complement, not compete with outfit
- Scarves: Add color and texture, versatile layering piece
        """,
        
        "seasonal_transitions": """
Transitioning between seasons:
- Spring: Layer light pieces, add cardigans, mix winter and summer items
- Fall: Add layers gradually, incorporate rich colors, mix textures
- Use accessories: Scarves, jackets, and layers help bridge seasons
- Color palette: Transition from light to rich or vice versa
        """
    }
}

def get_fashion_knowledge_base_text():
    """Get the full fashion knowledge base as formatted text for AI."""
    kb_text = """
FASHION KNOWLEDGE BASE FOR INSIGHTSHOP AI ASSISTANT
===================================================

COLOR MATCHING & COORDINATION:
{color_matching}

STYLE ADVICE:
{style_advice}

OCCASION-APPROPRIATE DRESSING:
{occasions}

FABRIC GUIDE:
{fabric_guide}

STYLING TIPS:
{styling_tips}
    """.format(
        color_matching=FASHION_KNOWLEDGE_BASE["color_matching"]["basics"],
        style_advice=FASHION_KNOWLEDGE_BASE["style_advice"]["fit"] + "\n" + FASHION_KNOWLEDGE_BASE["style_advice"]["layering"] + "\n" + FASHION_KNOWLEDGE_BASE["style_advice"]["proportions"],
        occasions="\n".join([f"{k.upper().replace('_', ' ')}:\n{v}" for k, v in FASHION_KNOWLEDGE_BASE["occasions"].items()]),
        fabric_guide="\n".join([f"{k.upper()}:\n{v['description']}\nBest for: {v['best_for']}\nCharacteristics: {v['characteristics']}" for k, v in FASHION_KNOWLEDGE_BASE["fabric_guide"].items()]),
        styling_tips=FASHION_KNOWLEDGE_BASE["styling_tips"]["build_wardrobe"] + "\n" + FASHION_KNOWLEDGE_BASE["styling_tips"]["accessories"] + "\n" + FASHION_KNOWLEDGE_BASE["styling_tips"]["seasonal_transitions"]
    )
    return kb_text

def get_color_matching_advice(color):
    """Get color matching advice for a specific color."""
    color_lower = color.lower() if color else ""
    return FASHION_KNOWLEDGE_BASE["color_matching"]["by_color"].get(color_lower, "This color pairs well with neutrals like black, white, gray, and navy for a classic look.")

def get_fabric_info(fabric_name):
    """Get information about a specific fabric."""
    if not fabric_name:
        return None
    
    fabric_lower = fabric_name.lower()
    for fabric_key, fabric_info in FASHION_KNOWLEDGE_BASE["fabric_guide"].items():
        if fabric_key in fabric_lower or fabric_lower in fabric_key:
            return fabric_info
    return None

def get_occasion_advice(occasion):
    """Get styling advice for a specific occasion."""
    occasion_lower = occasion.lower().replace(" ", "_")
    return FASHION_KNOWLEDGE_BASE["occasions"].get(occasion_lower, "Choose clothing that makes you feel confident and appropriate for the setting.")

