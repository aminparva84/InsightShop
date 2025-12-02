"""Assign images from generated_images folder to products and delete large PNG files."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.product import Product
from models.database import db
import re
import shutil

def assign_generated_images():
    """Assign images from generated_images folder to products."""
    with app.app_context():
        # Get generated_images directory
        generated_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'generated_images')
        
        if not os.path.exists(generated_dir):
            print(f"Directory {generated_dir} does not exist!")
            return
        
        # Get all JPG files (compressed/web-ready versions)
        image_files = [f for f in os.listdir(generated_dir) if f.lower().endswith('.jpg')]
        
        if not image_files:
            print(f"No JPG image files found in {generated_dir}")
            return
        
        print(f"Found {len(image_files)} JPG image files to process...")
        
        # Copy JPG files to static/images and assign to products
        static_images_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images')
        os.makedirs(static_images_dir, exist_ok=True)
        
        updated_count = 0
        copied_count = 0
        
        for filename in image_files:
            # Extract product ID from filename
            # Format: product_{id}_{description}.jpg
            match = re.match(r'product_(\d+)_', filename)
            if not match:
                print(f"  [SKIP] Could not extract product ID from {filename}")
                continue
            
            product_id = int(match.group(1))
            
            # Copy to static/images
            source_path = os.path.join(generated_dir, filename)
            dest_filename = f"product_{product_id}.jpg"
            dest_path = os.path.join(static_images_dir, dest_filename)
            
            try:
                shutil.copy2(source_path, dest_path)
                copied_count += 1
            except Exception as e:
                print(f"  [ERROR] Failed to copy {filename}: {e}")
                continue
            
            # Update product with image URL
            product = Product.query.get(product_id)
            if product:
                image_url = f"/api/images/{dest_filename}"
                product.image_url = image_url
                updated_count += 1
                
                if updated_count % 10 == 0:
                    db.session.commit()
                    print(f"  Updated {updated_count} products...")
            else:
                print(f"  [WARNING] Product {product_id} not found in database")
        
        db.session.commit()
        print(f"\n[OK] Successfully copied {copied_count} images to static/images")
        print(f"[OK] Successfully updated {updated_count} products with image URLs")
        
        # Delete large PNG files
        print(f"\n{'='*50}")
        print("Deleting large PNG files (keeping compressed JPG versions)...")
        
        png_files = [f for f in os.listdir(generated_dir) if f.lower().endswith('.png')]
        deleted_count = 0
        total_size_freed = 0
        
        for png_file in png_files:
            png_path = os.path.join(generated_dir, png_file)
            try:
                file_size = os.path.getsize(png_path)
                os.remove(png_path)
                deleted_count += 1
                total_size_freed += file_size
                print(f"  Deleted: {png_file} ({file_size / 1024 / 1024:.2f} MB)")
            except Exception as e:
                print(f"  [ERROR] Failed to delete {png_file}: {e}")
        
        print(f"\n[OK] Deleted {deleted_count} PNG files")
        print(f"[OK] Freed {total_size_freed / 1024 / 1024:.2f} MB of space")
        print(f"\n[OK] Kept {len(image_files)} compressed JPG files (web-ready)")

if __name__ == '__main__':
    assign_generated_images()

