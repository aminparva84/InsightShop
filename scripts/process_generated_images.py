"""Process generated images: compress, extract metadata, update database, and create fashion match relations."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
from PIL import Image
import re
import json
from utils.fashion_kb import FASHION_KNOWLEDGE_BASE

# Color compatibility mapping based on fashion knowledge
COLOR_COMPATIBILITY = {
    'black': ['white', 'gray', 'navy', 'red', 'pink', 'yellow', 'blue', 'green', 'purple', 'orange', 'beige'],
    'white': ['black', 'navy', 'gray', 'beige', 'red', 'blue', 'green', 'pink', 'yellow', 'purple', 'brown'],
    'navy': ['white', 'beige', 'gray', 'red', 'pink', 'yellow', 'light blue', 'blue'],
    'gray': ['black', 'white', 'navy', 'pastels', 'bright colors', 'pink', 'blue'],
    'beige': ['navy', 'brown', 'white', 'black', 'earth tones', 'green'],
    'red': ['navy', 'white', 'black', 'gray', 'beige'],
    'blue': ['white', 'gray', 'navy', 'beige', 'orange', 'yellow'],
    'green': ['beige', 'brown', 'white', 'navy', 'earth tones'],
    'pink': ['gray', 'navy', 'white', 'black'],
    'yellow': ['navy', 'white', 'gray', 'black'],
    'brown': ['beige', 'cream', 'white', 'navy', 'green'],
    'purple': ['gray', 'white', 'black', 'yellow'],
    'orange': ['blue', 'white', 'navy'],
    'maroon': ['navy', 'white', 'gray', 'beige'],
    'teal': ['white', 'navy', 'beige', 'gray']
}

# Clothing type compatibility (what goes well together)
CLOTHING_TYPE_COMPATIBILITY = {
    'T-Shirt': ['Jeans', 'Shorts', 'Chinos', 'Leggings'],
    'Polo Shirt': ['Jeans', 'Chinos', 'Shorts'],
    'Dress Shirt': ['Chinos', 'Jeans', 'Dress Pants'],
    'Blouse': ['Jeans', 'Skirt', 'Leggings', 'Dress Pants'],
    'Dress': ['Shoes', 'Heels', 'Sandals'],
    'Jeans': ['T-Shirt', 'Polo Shirt', 'Dress Shirt', 'Blouse', 'Hoodie', 'Sweater', 'Jacket'],
    'Chinos': ['T-Shirt', 'Polo Shirt', 'Dress Shirt', 'Sweater', 'Blazer'],
    'Shorts': ['T-Shirt', 'Polo Shirt', 'Sneakers', 'Sandals'],
    'Skirt': ['Blouse', 'T-Shirt', 'Sweater'],
    'Leggings': ['T-Shirt', 'Blouse', 'Hoodie', 'Sweater'],
    'Hoodie': ['Jeans', 'Leggings', 'Shorts'],
    'Sweater': ['Jeans', 'Chinos', 'Skirt', 'Leggings'],
    'Jacket': ['Jeans', 'Chinos', 'T-Shirt', 'Dress Shirt'],
    'Blazer': ['Dress Shirt', 'Chinos', 'Dress Pants'],
    'Coat': ['Sweater', 'Dress Shirt', 'Jeans', 'Chinos'],
    'Suit': ['Dress Shirt', 'Shoes'],
    'Shoes': ['Jeans', 'Chinos', 'Dress Pants', 'Dress'],
    'Sneakers': ['Jeans', 'Shorts', 'T-Shirt', 'Hoodie'],
    'Heels': ['Dress', 'Skirt', 'Dress Pants'],
    'Sandals': ['Shorts', 'Dress', 'Skirt']
}

def compress_image(input_path, output_path, quality=85, max_size=(800, 800)):
    """Compress a single image."""
    try:
        with Image.open(input_path) as img:
            # Convert RGBA to RGB if necessary (removes alpha channel)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if too large
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save as optimized JPEG (smaller than PNG for photos)
            img.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            reduction = ((original_size - new_size) / original_size) * 100
            
            return {
                'success': True,
                'original_size': original_size,
                'new_size': new_size,
                'reduction': reduction
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def extract_metadata_from_filename(filename):
    """Extract product ID and metadata from filename.
    
    Expected format: product_{id}_{description}.{ext}
    Examples:
    - product_1_mens_classic_blue_t-shirt.jpg
    - product_10_blue_t-shirt_for_men.png
    """
    # Remove extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Match pattern: product_{id}_{rest}
    match = re.match(r'product_(\d+)_(.+)', name_without_ext)
    if not match:
        return None
    
    product_id = int(match.group(1))
    description = match.group(2)
    
    # Extract color, category, and clothing type from description
    metadata = {
        'product_id': product_id,
        'description': description,
        'color': None,
        'category': None,
        'clothing_type': None
    }
    
    # Extract color
    colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'gray', 'pink', 
              'purple', 'orange', 'brown', 'navy', 'beige', 'maroon', 'teal']
    description_lower = description.lower()
    for color in colors:
        if color in description_lower:
            metadata['color'] = color.capitalize()
            break
    
    # Extract category
    if 'men' in description_lower or 'mens' in description_lower:
        metadata['category'] = 'men'
    elif 'women' in description_lower or 'womens' in description_lower:
        metadata['category'] = 'women'
    elif 'kids' in description_lower or 'kid' in description_lower:
        metadata['category'] = 'kids'
    
    # Extract clothing type
    clothing_types = ['t-shirt', 'polo shirt', 'dress shirt', 'blouse', 'dress', 
                      'jeans', 'chinos', 'shorts', 'skirt', 'leggings', 'hoodie', 
                      'sweater', 'jacket', 'blazer', 'coat', 'suit', 'shoes', 
                      'sneakers', 'heels', 'sandals']
    for ct in clothing_types:
        if ct in description_lower:
            # Capitalize properly
            if ct == 't-shirt':
                metadata['clothing_type'] = 'T-Shirt'
            else:
                metadata['clothing_type'] = ct.title()
            break
    
    return metadata

def are_colors_compatible(color1, color2):
    """Check if two colors are compatible for fashion matching."""
    if not color1 or not color2:
        return False
    
    color1_lower = color1.lower()
    color2_lower = color2.lower()
    
    # Same color is always compatible
    if color1_lower == color2_lower:
        return True
    
    # Check compatibility mapping
    compatible_colors = COLOR_COMPATIBILITY.get(color1_lower, [])
    return color2_lower in [c.lower() for c in compatible_colors]

def are_clothing_types_compatible(type1, type2):
    """Check if two clothing types are compatible (e.g., shirt + pants)."""
    if not type1 or not type2:
        return False
    
    # Same type is not compatible (don't match shirt with shirt)
    if type1.lower() == type2.lower():
        return False
    
    compatible_types = CLOTHING_TYPE_COMPATIBILITY.get(type1, [])
    return type2 in compatible_types or type1 in CLOTHING_TYPE_COMPATIBILITY.get(type2, [])

def are_occasions_compatible(occasion1, occasion2):
    """Check if two occasions are compatible."""
    if not occasion1 or not occasion2:
        return True  # If no occasion specified, assume compatible
    
    # Split comma-separated occasions
    occ1_list = [o.strip().lower() for o in occasion1.split(',')]
    occ2_list = [o.strip().lower() for o in occasion2.split(',')]
    
    # If they share any occasion, they're compatible
    return bool(set(occ1_list) & set(occ2_list))

def are_products_fashion_compatible(product1, product2):
    """Determine if two products are fashion-compatible for matching."""
    # Same product is not compatible
    if product1.id == product2.id:
        return False
    
    # Same category is preferred (but not required)
    same_category = product1.category == product2.category
    
    # Check color compatibility
    color_compatible = are_colors_compatible(product1.color, product2.color)
    
    # Check clothing type compatibility
    type_compatible = are_clothing_types_compatible(product1.clothing_type, product2.clothing_type)
    
    # Check occasion compatibility
    occasion_compatible = are_occasions_compatible(product1.occasion, product2.occasion)
    
    # Products are compatible if:
    # 1. Colors are compatible AND
    # 2. Clothing types are compatible AND
    # 3. Occasions are compatible
    # Category match is a bonus but not required
    return color_compatible and type_compatible and occasion_compatible

def create_product_relations_table():
    """Create a table to store fashion match relations between products."""
    with app.app_context():
        # Check if table exists
        from sqlalchemy import inspect, text
        
        inspector = inspect(db.engine)
        if 'product_relations' in inspector.get_table_names():
            print("Product relations table already exists.")
            return
        
        # Create table using raw SQL
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS product_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                related_product_id INTEGER NOT NULL,
                is_fashion_match BOOLEAN DEFAULT 1,
                match_score REAL DEFAULT 1.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (related_product_id) REFERENCES products(id) ON DELETE CASCADE,
                UNIQUE(product_id, related_product_id)
            )
        """))
        
        # Create indexes
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_relations_product_id 
            ON product_relations(product_id)
        """))
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_relations_related_product_id 
            ON product_relations(related_product_id)
        """))
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_product_relations_fashion_match 
            ON product_relations(is_fashion_match)
        """))
        
        db.session.commit()
        print("Product relations table created successfully.")

def process_images():
    """Main function to process all images."""
    with app.app_context():
        # Create static/images directory in the project root
        # This will be served by Flask's static file handler
        project_root = os.path.dirname(os.path.dirname(__file__))
        static_dir = os.path.join(project_root, 'static')
        images_dir = os.path.join(static_dir, 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # Create product relations table
        create_product_relations_table()
        
        # Directory containing generated images
        generated_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated_images')
        
        if not os.path.exists(generated_dir):
            print(f"Directory {generated_dir} does not exist!")
            return
        
        # Get all image files
        image_files = [f for f in os.listdir(generated_dir) 
                      if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not image_files:
            print(f"No image files found in {generated_dir}")
            return
        
        print(f"Found {len(image_files)} image files to process...")
        
        # Process each image
        processed = {}
        total_original = 0
        total_new = 0
        success_count = 0
        failed_count = 0
        
        for filename in image_files:
            input_path = os.path.join(generated_dir, filename)
            
            # Extract metadata
            metadata = extract_metadata_from_filename(filename)
            if not metadata:
                print(f"  [SKIP] Could not extract metadata from {filename}")
                failed_count += 1
                continue
            
            product_id = metadata['product_id']
            
            # Check if we already processed this product (prefer PNG over JPG for compression)
            if product_id in processed:
                # If current file is JPG and we already have PNG, skip
                if filename.lower().endswith('.jpg') and processed[product_id]['ext'] == 'png':
                    continue
                # If current file is PNG and we already processed JPG, replace
                elif filename.lower().endswith('.png') and processed[product_id]['ext'] == 'jpg':
                    pass  # Continue to process PNG
            
            # Compress image
            output_filename = f"product_{product_id}.jpg"
            output_path = os.path.join(images_dir, output_filename)
            
            print(f"\nProcessing {filename} (Product ID: {product_id})...")
            result = compress_image(input_path, output_path, quality=85)
            
            if result['success']:
                success_count += 1
                total_original += result['original_size']
                total_new += result['new_size']
                
                # Store processed info
                processed[product_id] = {
                    'filename': output_filename,
                    'path': output_path,
                    'metadata': metadata,
                    'ext': 'png' if filename.lower().endswith('.png') else 'jpg'
                }
                
                print(f"  [OK] Compressed: {result['original_size']/1024:.1f} KB -> {result['new_size']/1024:.1f} KB ({result['reduction']:.1f}% reduction)")
            else:
                failed_count += 1
                print(f"  [ERROR] Failed: {result['error']}")
        
        print(f"\n{'='*50}")
        print(f"Compression Summary:")
        print(f"  Success: {success_count}")
        print(f"  Failed: {failed_count}")
        print(f"  Total original size: {total_original/1024/1024:.2f} MB")
        print(f"  Total new size: {total_new/1024/1024:.2f} MB")
        print(f"  Total reduction: {((total_original - total_new) / total_original * 100):.1f}%")
        print(f"  Space saved: {(total_original - total_new)/1024/1024:.2f} MB")
        
        # Update products with image URLs
        print(f"\n{'='*50}")
        print("Updating products with image URLs...")
        updated_count = 0
        
        for product_id, info in processed.items():
            product = Product.query.get(product_id)
            if product:
                # Create relative URL path (will be served by Flask route)
                image_url = f"/api/images/{info['filename']}"
                product.image_url = image_url
                
                # Update metadata if missing
                metadata = info['metadata']
                if metadata['color'] and not product.color:
                    product.color = metadata['color']
                if metadata['category'] and not product.category:
                    product.category = metadata['category']
                if metadata['clothing_type'] and not product.clothing_type:
                    product.clothing_type = metadata['clothing_type']
                
                updated_count += 1
                
                if updated_count % 10 == 0:
                    db.session.commit()
                    print(f"  Updated {updated_count} products...")
        
        db.session.commit()
        print(f"Successfully updated {updated_count} products with image URLs and metadata!")
        
        # Create fashion match relations
        print(f"\n{'='*50}")
        print("Creating fashion match relations...")
        
        # Get all active products
        products = Product.query.filter_by(is_active=True).all()
        print(f"Processing {len(products)} products for fashion matches...")
        
        relations_created = 0
        batch_size = 100
        
        for i, product1 in enumerate(products):
            if (i + 1) % 50 == 0:
                print(f"  Processing product {i + 1}/{len(products)}...")
            
            # Find compatible products
            compatible_products = []
            for product2 in products:
                if are_products_fashion_compatible(product1, product2):
                    compatible_products.append(product2)
            
            # Store relations (limit to top 10 matches per product)
            for related_product in compatible_products[:10]:
                try:
                    from sqlalchemy import text
                    # Check if relation already exists
                    existing = db.session.execute(
                        text("""
                            SELECT id FROM product_relations 
                            WHERE product_id = :pid AND related_product_id = :rid
                        """),
                        {'pid': product1.id, 'rid': related_product.id}
                    ).fetchone()
                    
                    if not existing:
                        db.session.execute(
                            text("""
                                INSERT INTO product_relations 
                                (product_id, related_product_id, is_fashion_match, match_score)
                                VALUES (:pid, :rid, :match, :score)
                            """),
                            {'pid': product1.id, 'rid': related_product.id, 'match': True, 'score': 1.0}
                        )
                        relations_created += 1
                except Exception as e:
                    print(f"  [ERROR] Failed to create relation {product1.id} -> {related_product.id}: {e}")
            
            # Commit in batches
            if (i + 1) % batch_size == 0:
                db.session.commit()
        
        db.session.commit()
        print(f"Successfully created {relations_created} fashion match relations!")
        
        # Print summary
        print(f"\n{'='*50}")
        print("PROCESSING COMPLETE!")
        print(f"  Images compressed: {success_count}")
        print(f"  Products updated: {updated_count}")
        print(f"  Fashion relations created: {relations_created}")
        print(f"  Images stored in: {images_dir}")

if __name__ == '__main__':
    process_images()

