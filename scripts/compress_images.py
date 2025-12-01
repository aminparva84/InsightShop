"""Compress PNG images in generated_images directory to reduce file size."""
import os
import sys
from PIL import Image

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

def compress_all_images(directory='generated_images', output_dir=None, quality=85):
    """Compress all PNG images in a directory."""
    if output_dir is None:
        output_dir = directory
    
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist!")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    png_files = [f for f in os.listdir(directory) if f.lower().endswith('.png')]
    
    if not png_files:
        print(f"No PNG files found in {directory}")
        return
    
    print(f"Found {len(png_files)} PNG files to compress...")
    
    total_original = 0
    total_new = 0
    success_count = 0
    failed_count = 0
    
    for filename in png_files:
        input_path = os.path.join(directory, filename)
        # Change extension to .jpg for compressed version
        output_filename = os.path.splitext(filename)[0] + '.jpg'
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\nCompressing {filename}...")
        result = compress_image(input_path, output_path, quality=quality)
        
        if result['success']:
            success_count += 1
            total_original += result['original_size']
            total_new += result['new_size']
            print(f"  [OK] Success: {result['original_size']/1024:.1f} KB -> {result['new_size']/1024:.1f} KB ({result['reduction']:.1f}% reduction)")
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

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Compress PNG images')
    parser.add_argument('--directory', '-d', default='generated_images', help='Directory containing PNG files')
    parser.add_argument('--output', '-o', default=None, help='Output directory (default: same as input)')
    parser.add_argument('--quality', '-q', type=int, default=85, help='JPEG quality (1-100, default: 85)')
    
    args = parser.parse_args()
    compress_all_images(args.directory, args.output, args.quality)

