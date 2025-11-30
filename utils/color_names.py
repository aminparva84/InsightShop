"""Comprehensive list of color names for fashion/clothing products."""

# Comprehensive color names organized by category
COLOR_NAMES = {
    # Basic Colors
    'red': ['red', 'crimson', 'scarlet', 'burgundy', 'maroon', 'cherry', 'rose', 'coral', 'salmon', 'pink', 'magenta', 'fuchsia', 'raspberry', 'wine', 'ruby'],
    'orange': ['orange', 'tangerine', 'peach', 'apricot', 'coral', 'amber', 'rust', 'copper', 'terracotta', 'pumpkin', 'carrot', 'mango', 'papaya'],
    'yellow': ['yellow', 'gold', 'amber', 'lemon', 'mustard', 'canary', 'butter', 'cream', 'ivory', 'beige', 'tan', 'khaki', 'sand', 'wheat', 'champagne'],
    'green': ['green', 'emerald', 'lime', 'mint', 'sage', 'olive', 'forest', 'teal', 'turquoise', 'jade', 'kelly', 'hunter', 'army', 'moss', 'fern', 'chartreuse'],
    'blue': ['blue', 'navy', 'royal', 'sky', 'azure', 'cobalt', 'indigo', 'sapphire', 'teal', 'turquoise', 'cerulean', 'steel', 'powder', 'baby', 'denim', 'midnight'],
    'purple': ['purple', 'violet', 'lavender', 'plum', 'amethyst', 'lilac', 'mauve', 'eggplant', 'grape', 'orchid', 'periwinkle', 'magenta', 'fuchsia'],
    'pink': ['pink', 'rose', 'blush', 'salmon', 'coral', 'fuchsia', 'magenta', 'peach', 'watermelon', 'bubblegum', 'cotton candy', 'strawberry', 'cherry'],
    'brown': ['brown', 'tan', 'beige', 'khaki', 'camel', 'taupe', 'coffee', 'mocha', 'chocolate', 'caramel', 'hazelnut', 'walnut', 'espresso', 'mahogany', 'chestnut'],
    'black': ['black', 'ebony', 'charcoal', 'ink', 'jet', 'onyx', 'raven', 'midnight', 'obsidian', 'coal', 'slate'],
    'white': ['white', 'ivory', 'cream', 'pearl', 'snow', 'alabaster', 'eggshell', 'off-white', 'vanilla', 'bone', 'chalk'],
    'gray': ['gray', 'grey', 'silver', 'charcoal', 'slate', 'ash', 'pewter', 'steel', 'smoke', 'stone', 'graphite', 'iron', 'cloud', 'mist'],
    
    # Fashion-Specific Colors
    'nude': ['nude', 'naked', 'flesh', 'skin', 'tan', 'beige', 'camel'],
    'metallic': ['metallic', 'silver', 'gold', 'bronze', 'copper', 'platinum', 'rose gold', 'champagne'],
    'pastel': ['pastel', 'soft', 'light', 'pale', 'muted', 'washed'],
    'neon': ['neon', 'electric', 'fluorescent', 'bright', 'vibrant'],
    'earth': ['earth', 'natural', 'organic', 'rustic', 'terracotta', 'clay'],
    
    # Pattern/Texture Colors
    'striped': ['striped', 'stripes'],
    'polka': ['polka', 'dots', 'dotted'],
    'floral': ['floral', 'flower', 'print'],
    'animal': ['animal', 'leopard', 'zebra', 'snake', 'cow'],
    'geometric': ['geometric', 'abstract', 'pattern'],
    
    # Fabric-Specific (these are fabrics, not colors, but users might search for them)
    'chiffon': ['chiffon'],
    'satin': ['satin', 'stretch satin', 'metallic satin'],
    'velvet': ['velvet'],
    'silk': ['silk'],
    'denim': ['denim', 'jean'],
    'leather': ['leather'],
    'suede': ['suede'],
    'lace': ['lace'],
    'mesh': ['mesh'],
    'jersey': ['jersey'],
    'cotton': ['cotton'],
    'linen': ['linen'],
    'wool': ['wool'],
    'cashmere': ['cashmere'],
    'polyester': ['polyester'],
    'spandex': ['spandex', 'stretch'],
}

# Flattened list for easy searching
ALL_COLOR_NAMES = []
for color_group, variants in COLOR_NAMES.items():
    ALL_COLOR_NAMES.extend(variants)

# Normalize function to find color from user input
def normalize_color_name(user_input):
    """Find the best matching color name from user input."""
    if not user_input:
        return None
    
    user_input_lower = user_input.lower().strip()
    
    # Direct match
    for color_group, variants in COLOR_NAMES.items():
        if user_input_lower == color_group:
            return color_group
        for variant in variants:
            if user_input_lower == variant:
                return color_group
    
    # Partial match
    for color_group, variants in COLOR_NAMES.items():
        if color_group in user_input_lower:
            return color_group
        for variant in variants:
            if variant in user_input_lower:
                return color_group
    
    return None

# Get all variants for a color
def get_color_variants(color_name):
    """Get all variant names for a given color."""
    return COLOR_NAMES.get(color_name.lower(), [])

