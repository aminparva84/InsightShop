"""Fashion Knowledge Base for AI Agent - Style, Color Matching, Occasions, and Complete-the-Look Recommendations."""

FASHION_KNOWLEDGE_BASE = {
    "color_matching": {
        "basics": """
Color coordination is essential for creating polished outfits. Here are the fundamentals:

NEUTRAL COLORS (go with everything):
- Black, White, Gray, Navy, Beige, Brown, Khaki, Charcoal, Cream, Camel
- These are your foundation pieces - they pair with any color

COLOR TEMPERATURE (undertones matter):
- WARM: Red, orange, yellow, gold, camel, rust, olive, mustard, terracotta. Pair warm with warm for harmony.
- COOL: Blue, green, purple, silver, gray, mint, blush. Pair cool with cool for harmony.
- MIXING: Neutrals (black, white, gray, navy) bridge both; one warm + one cool can work when one is neutral or muted.

COMPLEMENTARY COLORS (opposites on color wheel):
- Red & Green, Blue & Orange, Yellow & Purple
- Use sparingly for bold statements; soften one shade (e.g. burgundy + sage) for wearability

ANALOGOUS COLORS (next to each other on color wheel):
- Blue & Green, Red & Orange, Yellow & Green, Blue & Purple
- Creates harmonious, cohesive looks with low risk

MONOCHROMATIC (same color family):
- Different shades of the same color (e.g. navy shirt, light blue chinos)
- Creates sophisticated, elegant looks; add one neutral for balance

CLASSIC COMBINATIONS:
- Navy & White: Timeless, crisp, professional
- Black & White: Bold, modern, versatile
- Gray & Blue: Sophisticated, professional
- Beige & Brown: Warm, earthy, elegant
- Red & Navy: Classic, preppy, confident
- Pink & Gray: Soft, feminine, modern
- Burgundy & Gray: Refined, autumn-ready
- Olive & Camel: Earthy, contemporary
- Blush & Gray: Soft, modern feminine
        """,
        
        "by_color": {
            "black": "Black is the ultimate neutral. It pairs with everything - white, gray, navy, red, pink, yellow, and all bright colors. Perfect for creating contrast and sophistication. For cart/outfit matching: suggest white or light tops with black bottoms, or black accessories with colored pieces.",
            "white": "White is fresh and versatile. Pairs beautifully with black, navy, gray, pastels, and bold colors. Great for summer and creating a clean, crisp look. Ideal base for statement pieces.",
            "navy": "Navy is sophisticated and professional. Complements white, beige, gray, red, pink, yellow, and light blue. More versatile than black for business settings. Pairs with khaki, white chinos, and brown shoes.",
            "gray": "Gray is a modern neutral. Works with black, white, navy, pastels, and bright colors. Charcoal for formal; light gray for casual. Perfect for creating subtle, elegant combinations.",
            "beige": "Beige is warm and elegant. Pairs with navy, brown, white, black, and earth tones. Creates sophisticated, timeless looks. Works with olive, camel, and cream.",
            "red": "Red is bold and confident. Complements navy, white, black, gray, and beige. Use as an accent or statement piece. For matching: suggest neutral bottoms and shoes (navy, black, white).",
            "blue": "Blue is calming and versatile. Pairs with white, gray, navy, beige, and complementary colors like orange or yellow. Light blue with navy for monochromatic; with white for crisp.",
            "green": "Green is fresh and natural. Complements beige, brown, white, navy, and earth tones. Olive pairs with camel, black, white; forest green with burgundy or cream.",
            "pink": "Pink is feminine and soft. Pairs with gray, navy, white, black, and complementary colors. Blush with gray or navy; hot pink as accent with neutrals.",
            "yellow": "Yellow is cheerful and bright. Complements navy, white, gray, and black. Use as an accent for energy. Mustard pairs with olive, brown, and denim.",
            "brown": "Brown is earthy and warm. Pairs with beige, cream, white, navy, and green. Creates cozy, autumnal looks. Brown shoes with navy or gray for classic menswear.",
            "purple": "Purple is regal and creative. Complements gray, white, black, and yellow. Lavender with white or gray; deep purple with gold or black.",
            "burgundy": "Burgundy is rich and refined. Pairs with gray, navy, black, cream, and gold. Excellent for fall/winter and smart casual or formal.",
            "olive": "Olive is earthy and versatile. Pairs with camel, beige, white, black, denim, and rust. Modern military-inspired and casual-professional.",
            "camel": "Camel is warm and luxurious. Pairs with black, white, navy, gray, and brown. Coats and sweaters anchor outfits; pair with neutral or complementary bottoms.",
            "cream": "Cream is soft and elegant. Pairs with navy, brown, black, and pastels. Softer alternative to white for warm palettes.",
            "charcoal": "Charcoal is formal and sleek. Pairs like gray but more formal; ideal with white, light blue, and burgundy for business or evening.",
            "blush": "Blush is soft and modern. Pairs with gray, navy, white, and metallics. Popular for dresses and blouses; suggest neutral or matching accessories.",
            "rust": "Rust is warm and seasonal. Pairs with cream, olive, brown, and denim. Autumn staple; suggest earth-tone or neutral complements.",
            "mustard": "Mustard is bold and warm. Pairs with navy, black, olive, brown, and denim. Use as statement; balance with neutrals."
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
        """,
        
        "texture_mixing": """
Texture mixing adds depth and prevents flat outfits:
- Pair smooth (silk, cotton) with textured (tweed, cable knit, corduroy)
- Leather or suede with cotton or denim for contrast
- Avoid two heavy textures (e.g. thick knit + thick tweed) unless intentional
- One matte + one subtle shine (e.g. cotton shirt + silk tie) works well
        """,
        
        "formality_levels": """
Match formality across the outfit for a cohesive look:
- FORMAL: Suits, dress shoes, structured fabrics, dark neutrals
- SMART CASUAL: Chinos, blazers, loafers, polished but relaxed
- CASUAL: Jeans, tees, sneakers, relaxed fits
- When recommending matches: keep top and bottom in same formality tier; shoes and accessories should match or elevate slightly.
        """,
        
        "style_archetypes": """
Common style directions (use to guide cohesive recommendations):
- MINIMALIST: Neutral palette, clean lines, few accessories, quality basics
- PREPPY: Navy, white, khaki, stripes, loafers, polished casual
- BOHO: Flowing fabrics, earth tones, layered jewelry, natural textures
- EDGY: Black, leather, denim, boots, minimal color
- CLASSIC: Timeless pieces, navy/black/gray/white, tailored fits
- When suggesting matches for cart or past purchases, align with the style of the existing item (e.g. blazer + chinos for preppy; leather jacket + black jeans for edgy).
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
        """,
        
        "interview": """
Interview attire should be polished and context-appropriate:
- Corporate: Suit (navy or charcoal), dress shirt, conservative tie, dress shoes
- Business casual office: Blazer, dress pants or skirt, button-down or blouse, loafers or heels
- Creative/startup: Smart casual - blazer with chinos or dark jeans, clean sneakers or loafers
- Colors: Navy, gray, white, subtle patterns; avoid loud colors or heavy fragrance
        """,
        
        "travel": """
Travel-friendly styling balances comfort and polish:
- Wrinkle-resistant fabrics: Wool blends, technical synthetics, jersey
- Neutral color base so pieces mix and match (capsule approach)
- Layers: Cardigan or jacket for planes; scarf as accessory and blanket
- Shoes: One comfortable walking pair that works with multiple outfits
- Suggest items that pair with multiple bottoms/tops for fewer pieces
        """,
        
        "brunch_weekend": """
Brunch and weekend daytime: relaxed but put-together:
- Women: Casual dress, nice top with jeans or skirt, flats or low heels, light layers
- Men: Chinos or dark jeans, polo or casual button-down, clean sneakers or loafers
- Colors: Light, fresh, or soft; avoid full formal black
        """,
        
        "evening_cocktail": """
Evening cocktail: elevated but not black-tie:
- Women: Cocktail dress, elegant jumpsuit, or dressy separates; heels; statement jewelry
- Men: Dark suit or blazer with dress pants, dress shirt, optional tie; dress shoes
- Colors: Dark or jewel tones; avoid casual denim or sneakers
        """
    },
    
    "dress_codes": {
        "black_tie": "Formal evening: Tuxedo or dark suit, bow tie, dress shoes. Women: Floor-length gown or formal cocktail dress, elegant accessories.",
        "cocktail": "Semi-formal: Suit or blazer and dress pants. Women: Knee-length or midi dress, heels. No full-length gown or casual jeans.",
        "business_formal": "Full suit (navy/charcoal/black), dress shirt, tie, dress shoes. Women: Suit or tailored dress, closed-toe heels.",
        "smart_casual": "Polished casual: Chinos or dark jeans, button-down or polo, blazer optional, loafers or clean sneakers. No shorts or athletic wear.",
        "casual": "Relaxed: Jeans, tees, sneakers acceptable. Still put-together (no gym wear unless context-appropriate).",
        "white_tie": "Most formal: Tailcoat, white bow tie, waistcoat. Women: Full-length formal gown. Rare; only for very formal events."
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
        },
        "velvet": {
            "description": "Velvet is luxurious, soft, and has a distinctive nap. Adds richness and works for evening or elevated casual.",
            "care": "Dry clean or gentle hand wash; avoid crushing; hang or roll for storage",
            "best_for": "Evening wear, blazers, accessories, winter pieces",
            "characteristics": "Luxurious, rich texture, warm, seasonal (fall/winter)"
        },
        "corduroy": {
            "description": "Corduroy is durable, textured, and casual-smart. Ribbed surface adds visual interest.",
            "care": "Machine wash cold, tumble dry low; may soften with wear",
            "best_for": "Pants, jackets, casual wear, autumn",
            "characteristics": "Textured, durable, warm, casual to smart casual"
        },
        "tweed": {
            "description": "Tweed is a rough, woolen fabric often with mixed colors. Classic for blazers and outerwear.",
            "care": "Dry clean; brush to remove debris",
            "best_for": "Blazers, coats, skirts, autumn/winter professional",
            "characteristics": "Textured, warm, traditional, pairs with cotton and wool"
        },
        "jersey": {
            "description": "Jersey is a soft, stretchy knit. Comfortable and versatile for tops and dresses.",
            "care": "Machine wash cold, lay flat or low tumble dry",
            "best_for": "T-shirts, dresses, casual tops, loungewear",
            "characteristics": "Soft, stretchy, casual, easy care"
        },
        "satin": {
            "description": "Satin has a glossy surface and smooth drape. Elegant for evening and special occasions.",
            "care": "Dry clean or gentle hand wash; avoid snagging",
            "best_for": "Blouses, dresses, lingerie, accessories",
            "characteristics": "Shiny, smooth, elegant, delicate"
        },
        "fleece": {
            "description": "Fleece is soft, warm, and quick-drying. Ideal for casual and active outer layers.",
            "care": "Machine washable, low heat dry",
            "best_for": "Hoodies, jackets, loungewear, cold-weather casual",
            "characteristics": "Warm, soft, casual, easy care"
        }
    },
    
    "fabric_pairing": """
When recommending items to complete an outfit, consider fabric harmony:
- Same formality: Wool suit with cotton dress shirt; silk blouse with wool trousers
- Casual head-to-toe: Denim + cotton tee; jersey dress + denim jacket
- Mix textures: Cotton shirt under tweed blazer; silk scarf with wool coat
- Season alignment: Linen with linen or cotton in summer; wool with wool or cashmere in winter
- Avoid: Heavy wool with light linen in one outfit; athletic fabric with formal suiting (unless intentional)
    """,
    
    "dress_styles": {
        "necklines": {
            "scoop": {
                "description": "Scoop neckline - A rounded, U-shaped neckline that sits below the collarbone. Flattering for most body types, creates a feminine, casual look.",
                "best_for": "Casual dresses, t-shirts, everyday wear, all body types",
                "occasions": "Casual, everyday, weekend, relaxed settings"
            },
            "v-neck": {
                "description": "V-neck - A V-shaped neckline that elongates the neck and creates a slimming effect. Versatile and flattering.",
                "best_for": "Dresses, blouses, t-shirts, professional wear",
                "occasions": "Business casual, date night, everyday, professional"
            },
            "round": {
                "description": "Round neckline - A classic circular neckline, also called crew neck. Timeless and versatile.",
                "best_for": "T-shirts, casual dresses, everyday basics",
                "occasions": "Casual, everyday, relaxed settings"
            },
            "boat": {
                "description": "Boat neckline - A wide, horizontal neckline that extends to the shoulders. Creates a sophisticated, elegant look.",
                "best_for": "Dresses, blouses, formal wear",
                "occasions": "Formal events, business, elegant occasions"
            },
            "halter": {
                "description": "Halter neckline - Straps that tie behind the neck, leaving shoulders and back exposed. Modern and stylish.",
                "best_for": "Dresses, tops, summer wear",
                "occasions": "Summer, casual, date night, warm weather"
            },
            "off-shoulder": {
                "description": "Off-shoulder - Neckline that sits below the shoulders, exposing them. Romantic and feminine.",
                "best_for": "Dresses, blouses, special occasions",
                "occasions": "Date night, parties, summer events, special occasions"
            },
            "high-neck": {
                "description": "High neckline - Covers the neck completely, also called turtleneck or mock neck. Elegant and warm.",
                "best_for": "Dresses, sweaters, winter wear",
                "occasions": "Winter, formal, professional, elegant occasions"
            },
            "square": {
                "description": "Square neckline - A straight, horizontal neckline creating a square shape. Classic and structured.",
                "best_for": "Dresses, blouses, formal wear",
                "occasions": "Formal events, business, classic occasions"
            }
        },
        "dress_features": {
            "bow": {
                "description": "Bow detail - Decorative bow element, often at the neckline, waist, or as a belt. Adds femininity and elegance.",
                "best_for": "Dresses, blouses, formal wear, feminine styles",
                "occasions": "Formal events, parties, date night, elegant occasions"
            },
            "padding": {
                "description": "Padded or structured - Built-in padding or structure, often in the bust area or shoulders. Creates shape and definition.",
                "best_for": "Dresses, blouses, formal wear, structured styles",
                "occasions": "Formal events, business, occasions requiring structure"
            },
            "slit": {
                "description": "Slit - A vertical opening in the skirt or dress, typically on the side or front. Adds movement and elegance.",
                "best_for": "Dresses, skirts, formal wear, evening wear",
                "occasions": "Formal events, parties, date night, evening occasions"
            },
            "peplum": {
                "description": "Peplum - A short overskirt or ruffle attached at the waist. Creates an hourglass silhouette.",
                "best_for": "Dresses, tops, feminine styles",
                "occasions": "Date night, parties, feminine occasions"
            },
            "wrap": {
                "description": "Wrap style - Dresses or tops that wrap around the body and tie. Flattering and adjustable fit.",
                "best_for": "Dresses, blouses, versatile styles",
                "occasions": "Casual, business casual, date night, versatile"
            },
            "a-line": {
                "description": "A-line - Fitted at the top and flared at the bottom, creating an A shape. Flattering for most body types.",
                "best_for": "Dresses, skirts, versatile styles",
                "occasions": "Casual, business casual, formal, versatile"
            },
            "bodycon": {
                "description": "Bodycon - Fitted, body-conscious style that hugs the curves. Modern and bold.",
                "best_for": "Dresses, evening wear, confident styles",
                "occasions": "Parties, date night, evening events, bold occasions"
            },
            "maxi": {
                "description": "Maxi - Long, floor-length dress. Elegant and comfortable.",
                "best_for": "Dresses, summer wear, formal wear",
                "occasions": "Summer, formal events, parties, elegant occasions"
            },
            "midi": {
                "description": "Midi - Medium-length dress, typically hitting mid-calf. Classic and versatile.",
                "best_for": "Dresses, versatile styles",
                "occasions": "Business casual, date night, versatile occasions"
            },
            "mini": {
                "description": "Mini - Short dress, typically above the knee. Modern and youthful.",
                "best_for": "Dresses, casual wear, party wear",
                "occasions": "Parties, casual, date night, youthful occasions"
            }
        },
        "men_styles": {
            "v-neck": {
                "description": "V-neck - V-shaped neckline for men's shirts and t-shirts. Classic and versatile.",
                "best_for": "T-shirts, casual shirts, everyday wear",
                "occasions": "Casual, everyday, relaxed settings"
            },
            "crew": {
                "description": "Crew neck - Round neckline for men's t-shirts and casual wear. Timeless classic.",
                "best_for": "T-shirts, casual wear, basics",
                "occasions": "Casual, everyday, relaxed settings"
            },
            "henley": {
                "description": "Henley - Collarless shirt with a placket and 2-5 buttons. Casual and comfortable.",
                "best_for": "Casual shirts, everyday wear",
                "occasions": "Casual, weekend, relaxed settings"
            },
            "polo": {
                "description": "Polo - Collared shirt with 2-3 buttons. Smart casual staple.",
                "best_for": "Casual shirts, business casual",
                "occasions": "Business casual, casual, versatile"
            }
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
    },
    
    "outfit_formulas": {
        "description": "Use these rules when recommending matching items for products already in the cart or previously purchased. Suggest items that COMPLETE THE LOOK.",
        "by_primary_category": {
            "shirt_blouse_top_tee": "Suggest: bottoms (chinos, trousers, jeans, skirt) in neutral or complementary color; shoes (loafers, sneakers, heels) matching formality; optional blazer or cardigan; belt if trousers.",
            "dress": "Suggest: shoes (heels, flats, sandals, boots by season); bag; jewelry (earrings, necklace); outer layer (blazer, cardigan) if appropriate.",
            "pants_trousers_chinos_jeans": "Suggest: top (shirt, blouse, tee, sweater) in color that matches color_matching rules; shoes; belt; optional jacket.",
            "jacket_blazer_coat": "Suggest: inner layer (shirt, blouse, sweater) and bottoms that match formality; shoes; scarf if coat.",
            "sweater_cardigan": "Suggest: base layer (shirt, tee) and bottoms (jeans, chinos, skirt); shoes; optional outer jacket.",
            "shorts": "Suggest: top (tee, polo, tank) and shoes (sneakers, sandals, loafers); avoid formal shoes.",
            "skirt": "Suggest: top (blouse, tee, sweater) and shoes (heels, flats, boots); tights in cold weather.",
            "shoes": "Suggest: bottoms and top that match formality and color; socks if applicable.",
            "accessories_bag_belt_hat": "Suggest: outfit base (top + bottom) that the accessory complements; avoid clashing colors or formality."
        },
        "color_logic": "For any primary item: recommend complements from color_matching.by_color (same or adjacent key). Prefer one neutral in the outfit; second piece can be color. For prints, suggest solids in a color from the print.",
        "formality_logic": "Match formality: casual top → casual bottom and casual shoes; blazer → chinos or dress pants and loafers/dress shoes; dress → heels or dressy flats.",
        "season_logic": "Recommend pieces appropriate to current season: summer → light fabrics, sandals, hats; winter → layers, boots, scarves; spring/fall → transitional layers and colors."
    },
    
    "pattern_rules": {
        "basics": """
Pattern mixing and pairing for recommendations:
- STRIPE + SOLID: Striped top pairs with solid bottom in a color from the stripe (e.g. navy stripe shirt → navy or white chinos). Classic and safe.
- PLAID + SOLID: Plaid shirt or jacket with solid pants or skirt. Pick one color from the plaid for the solid.
- PLAID + DENIM: Plaid flannel with denim (jeans or jacket) is a classic casual combo.
- FLORAL + SOLID: Floral dress or top with solid accessories; or solid bottom in a dominant or accent color from the floral.
- ONE PATTERN RULE: If the user has one patterned item, suggest solids or subtle textures for the rest. If they have solids only, you can suggest one patterned piece.
- SCALE: Don't pair two large bold patterns; one bold + one small pattern or texture can work.
        """,
        "avoid": "Avoid: two different loud patterns (e.g. bold stripes + bold floral); clashing color temperatures in same outfit unless one is neutral."
    },
    
    "recommendation_priority": """
When the AI suggests matching pairs for items in the cart or already bought, apply this priority:
1. CATEGORY MATCH: Suggest the right category (e.g. shirt → pants, dress → shoes) per outfit_formulas.by_primary_category.
2. COLOR HARMONY: Use color_matching.by_color and color_temperature so suggested item coordinates (neutral or complementary).
3. FORMALITY MATCH: Keep suggested item in same formality tier as the cart/owned item (style_advice.formality_levels).
4. SEASON: Prefer items suitable for current season and weather (occasions + fabric_guide).
5. RATINGS: When multiple options exist, prefer products with higher rating and more reviews.
6. STYLE COHESION: Align with style_archetypes if the primary item implies a clear style (e.g. leather jacket → edgy complements).
Always give a brief reason for the match (e.g. 'This pairs with your navy shirt' or 'Same formality for a complete look').
    """
}

def get_fashion_knowledge_base_text():
    """Get the full fashion knowledge base as formatted text for AI."""
    kb = FASHION_KNOWLEDGE_BASE
    
    # Color matching: basics + by_color summary for quick lookup
    color_basics = kb.get("color_matching", {}).get("basics", "")
    by_color = kb.get("color_matching", {}).get("by_color", {})
    color_by_color_text = "\n".join([f"- {k}: {v}" for k, v in by_color.items()]) if by_color else ""
    color_matching_full = color_basics + "\n\nBY COLOR (for cart/outfit matching):\n" + color_by_color_text if color_by_color_text else color_basics
    
    # Style advice: all keys (fit, layering, proportions, texture_mixing, formality_levels, style_archetypes)
    style_advice_dict = kb.get("style_advice", {})
    style_keys = ["fit", "layering", "proportions", "texture_mixing", "formality_levels", "style_archetypes"]
    style_advice_parts = [style_advice_dict[k] for k in style_keys if style_advice_dict.get(k)]
    style_advice_text = "\n".join(style_advice_parts) if style_advice_parts else ""
    
    # Occasions
    occasions_dict = kb.get("occasions", {})
    occasions_text = "\n".join([f"{k.upper().replace('_', ' ')}:\n{v}" for k, v in occasions_dict.items()]) if occasions_dict else ""
    
    # Dress codes (optional)
    dress_codes = kb.get("dress_codes", {})
    dress_codes_text = "\n".join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in dress_codes.items()]) if dress_codes else ""
    
    # Fabric guide
    fabric_guide_dict = kb.get("fabric_guide", {})
    fabric_parts = []
    for k, v in fabric_guide_dict.items():
        if isinstance(v, dict):
            fabric_parts.append(f"{k.upper()}: {v.get('description', '')}\nBest for: {v.get('best_for', '')}\nCharacteristics: {v.get('characteristics', '')}")
    fabric_guide_text = "\n".join(fabric_parts) if fabric_parts else ""
    
    # Fabric pairing (optional)
    fabric_pairing_text = kb.get("fabric_pairing", "") or ""
    
    # Dress styles
    dress_styles = kb.get("dress_styles", {})
    necklines = dress_styles.get("necklines", {})
    features = dress_styles.get("dress_features", {})
    men_styles = dress_styles.get("men_styles", {})
    necklines_text = "\n".join([f"{k.upper().replace('_', '-')} NECKLINE:\n{v.get('description','')}\nBest for: {v.get('best_for','')}\nOccasions: {v.get('occasions','')}" for k, v in necklines.items()]) if necklines else ""
    features_text = "\n".join([f"{k.upper().replace('_', '-')} FEATURE:\n{v.get('description','')}\nBest for: {v.get('best_for','')}\nOccasions: {v.get('occasions','')}" for k, v in features.items()]) if features else ""
    men_styles_text = "\n".join([f"{k.upper().replace('_', '-')} STYLE:\n{v.get('description','')}\nBest for: {v.get('best_for','')}\nOccasions: {v.get('occasions','')}" for k, v in men_styles.items()]) if men_styles else ""
    
    # Styling tips
    styling_tips_dict = kb.get("styling_tips", {})
    styling_keys = ["build_wardrobe", "accessories", "seasonal_transitions"]
    styling_parts = [styling_tips_dict.get(k, "") for k in styling_keys if styling_tips_dict.get(k)]
    styling_tips_text = "\n".join(styling_parts) if styling_parts else ""
    
    # Outfit formulas (for cart/owned-item matching)
    outfit_formulas = kb.get("outfit_formulas", {})
    of_desc = outfit_formulas.get("description", "")
    of_by_cat = outfit_formulas.get("by_primary_category", {})
    of_by_cat_text = "\n".join([f"- {k}: {v}" for k, v in of_by_cat.items()]) if of_by_cat else ""
    of_color = outfit_formulas.get("color_logic", "")
    of_formality = outfit_formulas.get("formality_logic", "")
    of_season = outfit_formulas.get("season_logic", "")
    outfit_formulas_text = f"{of_desc}\n\nBY PRIMARY CATEGORY:\n{of_by_cat_text}\n\nCOLOR LOGIC: {of_color}\n\nFORMALITY LOGIC: {of_formality}\n\nSEASON LOGIC: {of_season}" if (of_desc or of_by_cat_text) else ""
    
    # Pattern rules
    pattern_rules = kb.get("pattern_rules", {})
    pattern_basics = pattern_rules.get("basics", "")
    pattern_avoid = pattern_rules.get("avoid", "")
    pattern_rules_text = f"{pattern_basics}\nAVOID: {pattern_avoid}" if (pattern_basics or pattern_avoid) else ""
    
    # Recommendation priority
    recommendation_priority_text = kb.get("recommendation_priority", "") or ""
    
    # Build full KB text with optional sections
    sections = [
        ("COLOR MATCHING & COORDINATION", color_matching_full),
        ("STYLE ADVICE", style_advice_text),
        ("OCCASION-APPROPRIATE DRESSING", occasions_text),
        ("DRESS CODES", dress_codes_text),
        ("FABRIC GUIDE", fabric_guide_text),
        ("FABRIC PAIRING (outfit harmony)", fabric_pairing_text),
        ("DRESS STYLES & NECKLINES (WOMEN)", necklines_text),
        ("DRESS FEATURES (WOMEN)", features_text),
        ("MEN'S STYLES", men_styles_text),
        ("STYLING TIPS", styling_tips_text),
        ("OUTFIT FORMULAS (complete-the-look for cart/owned items)", outfit_formulas_text),
        ("PATTERN RULES", pattern_rules_text),
        ("RECOMMENDATION PRIORITY (for matching pairs)", recommendation_priority_text),
    ]
    parts = ["FASHION KNOWLEDGE BASE FOR INSIGHTSHOP AI ASSISTANT", "=" * 50]
    for title, content in sections:
        if content and content.strip():
            parts.append(f"\n{title}:\n{content.strip()}")
    kb_text = "\n".join(parts)
    return kb_text

def get_color_matching_advice(color):
    """Get color matching advice for a specific color."""
    color_lower = (color or "").lower()
    by_color = FASHION_KNOWLEDGE_BASE.get("color_matching", {}).get("by_color", {})
    return by_color.get(color_lower, "This color pairs well with neutrals like black, white, gray, and navy for a classic look.")


def get_fabric_info(fabric_name):
    """Get information about a specific fabric."""
    if not fabric_name:
        return None
    fabric_lower = fabric_name.lower()
    for fabric_key, fabric_info in (FASHION_KNOWLEDGE_BASE.get("fabric_guide") or {}).items():
        if fabric_key in fabric_lower or fabric_lower in fabric_key:
            return fabric_info
    return None

def get_occasion_advice(occasion):
    """Get styling advice for a specific occasion."""
    occasion_lower = occasion.lower().replace(" ", "_")
    return FASHION_KNOWLEDGE_BASE.get("occasions", {}).get(occasion_lower, "Choose clothing that makes you feel confident and appropriate for the setting.")


def get_outfit_formula(primary_category_or_product_name):
    """
    Get 'complete the look' suggestion text for a given product type.
    Used to recommend matching pairs for cart or already-bought items.
    primary_category_or_product_name: e.g. 'shirt', 'dress', 'Blue T-Shirt', 'chinos'
    """
    formulas = FASHION_KNOWLEDGE_BASE.get("outfit_formulas", {}).get("by_primary_category", {})
    if not formulas:
        return None
    name_lower = (primary_category_or_product_name or "").lower()
    for category_key, advice in formulas.items():
        # category_key is like "shirt_blouse_top_tee" - check if any part matches
        keywords = category_key.replace("_", " ").split()
        if any(kw in name_lower for kw in keywords):
            return advice
    return None


def get_dress_code_advice(dress_code):
    """Get advice for a dress code (e.g. black_tie, smart_casual)."""
    code_lower = (dress_code or "").lower().replace(" ", "_")
    return FASHION_KNOWLEDGE_BASE.get("dress_codes", {}).get(code_lower)

