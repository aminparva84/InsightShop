"""Spelling tolerance utilities for product search."""

# Common misspellings and variations for clothing types
CLOTHING_TYPE_VARIANTS = {
    't-shirt': ['t-shirt', 'tshirt', 'tee', 't shirt', 't-shirts', 'tshirts', 'tees', 't shirts', 't-shrt', 'tshrt', 't-shit', 't-shrt'],
    'shirt': ['shirt', 'shirts', 'shrt', 'sirt', 'shirt'],
    'dress': ['dress', 'dres', 'dresses', 'dreses'],
    'jeans': ['jeans', 'jean', 'jens', 'jeans'],
    'pants': ['pants', 'pant', 'pnts', 'pants'],
    'shoes': ['shoes', 'shoe', 'shos', 'shoes'],
    'jacket': ['jacket', 'jackt', 'jaket', 'jackets'],
    'sweater': ['sweater', 'sweter', 'sweaters', 'swaters'],
    'blazer': ['blazer', 'blazr', 'blazers', 'blazrs'],
    'suit': ['suit', 'sut', 'suits', 'suts'],
    'polo': ['polo', 'polo shirt', 'polos'],
    'blouse': ['blouse', 'blous', 'blouses', 'blous'],
    'skirt': ['skirt', 'skrt', 'skirts', 'skrts'],
    'shorts': ['shorts', 'short', 'shorts'],
    'hoodie': ['hoodie', 'hoody', 'hoodies', 'hoodys'],
}

# Common misspellings for categories
CATEGORY_VARIANTS = {
    'women': ['women', 'woman', 'womens', 'womans', 'ladies', 'lady', 'ladys', 'femal', 'female'],
    'men': ['men', 'man', 'mens', 'mans', 'male', 'males', 'guy', 'guys'],
    'kids': ['kids', 'kid', 'kids', 'children', 'child', 'childs', 'childrens'],
}

# Common misspellings for colors (extend color_names.py)
COLOR_VARIANTS = {
    'red': ['red', 'rd', 're', 'redd'],
    'blue': ['blue', 'blu', 'bleu', 'blu'],
    'green': ['green', 'gren', 'grene', 'grn'],
    'yellow': ['yellow', 'yelow', 'yello', 'yllow'],
    'black': ['black', 'blak', 'blck', 'blac'],
    'white': ['white', 'whit', 'whte', 'whit'],
    'pink': ['pink', 'pnk', 'pink', 'pink'],
    'purple': ['purple', 'purpl', 'purpel', 'purp'],
    'orange': ['orange', 'orng', 'oragne', 'orang'],
    'brown': ['brown', 'brwn', 'brow', 'brown'],
    'gray': ['gray', 'grey', 'gry', 'gra'],
}

def normalize_clothing_type(user_input):
    """Normalize clothing type with spelling tolerance."""
    if not user_input:
        return None
    
    user_input_lower = user_input.lower().strip()
    
    # Check for exact matches first
    for normalized, variants in CLOTHING_TYPE_VARIANTS.items():
        if user_input_lower == normalized:
            return normalized
        if user_input_lower in variants:
            return normalized
    
    # Check for partial matches (contains)
    for normalized, variants in CLOTHING_TYPE_VARIANTS.items():
        if normalized in user_input_lower:
            return normalized
        for variant in variants:
            if variant in user_input_lower:
                return normalized
    
    # Fuzzy matching for common typos (simple Levenshtein-like)
    # Check if input is similar to any variant (1-2 character difference)
    for normalized, variants in CLOTHING_TYPE_VARIANTS.items():
        for variant in variants:
            if len(variant) > 3 and len(user_input_lower) > 3:
                # Simple similarity check
                if _is_similar(user_input_lower, variant, max_diff=2):
                    return normalized
    
    return None

def normalize_category(user_input):
    """Normalize category with spelling tolerance."""
    if not user_input:
        return None
    
    user_input_lower = user_input.lower().strip()
    
    # Check for exact matches
    for normalized, variants in CATEGORY_VARIANTS.items():
        if user_input_lower == normalized:
            return normalized
        if user_input_lower in variants:
            return normalized
    
    # Check for partial matches
    for normalized, variants in CATEGORY_VARIANTS.items():
        if normalized in user_input_lower:
            return normalized
        for variant in variants:
            if variant in user_input_lower:
                return normalized
    
    return None

def normalize_color_spelling(user_input):
    """Normalize color with spelling tolerance."""
    if not user_input:
        return None
    
    user_input_lower = user_input.lower().strip()
    
    # Check for exact matches
    for normalized, variants in COLOR_VARIANTS.items():
        if user_input_lower == normalized:
            return normalized
        if user_input_lower in variants:
            return normalized
    
    # Check for partial matches
    for normalized, variants in COLOR_VARIANTS.items():
        if normalized in user_input_lower:
            return normalized
        for variant in variants:
            if variant in user_input_lower:
                return normalized
    
    return None

def _is_similar(str1, str2, max_diff=2):
    """Simple similarity check (not full Levenshtein, but fast)."""
    if abs(len(str1) - len(str2)) > max_diff:
        return False
    
    # Count character differences
    diff = 0
    min_len = min(len(str1), len(str2))
    for i in range(min_len):
        if str1[i] != str2[i]:
            diff += 1
            if diff > max_diff:
                return False
    
    diff += abs(len(str1) - len(str2))
    return diff <= max_diff

