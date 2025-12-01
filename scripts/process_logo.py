"""
Script to process the logo image by removing white background
and creating a transparent PNG version for use as favicon and throughout the site.
"""
from PIL import Image
import os
import sys

def remove_white_background(input_path, output_path, threshold=240, border_width=2):
    """
    Remove white/light background from an image, make it transparent, and add a white border.
    
    Args:
        input_path: Path to input image
        output_path: Path to save processed image
        threshold: RGB threshold (0-255) for considering a pixel as white/background
        border_width: Width of the white border in pixels (default: 2)
    """
    try:
        # Open the image
        img = Image.open(input_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Get image data
        data = img.getdata()
        width, height = img.size
        
        # Create new image data with transparency
        new_data = []
        for y in range(height):
            for x in range(width):
                idx = y * width + x
                item = data[idx]
                
                # If pixel is white/light (all RGB values above threshold), make it transparent
                if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                    new_data.append((255, 255, 255, 0))  # Transparent
                else:
                    new_data.append(item)  # Keep original
        
        # Update image with new data
        img.putdata(new_data)
        
        # Add white border by creating a larger canvas
        # Calculate new dimensions with border
        new_width = width + (border_width * 2)
        new_height = height + (border_width * 2)
        
        # Create new image with white background
        bordered_img = Image.new('RGBA', (new_width, new_height), (255, 255, 255, 255))
        
        # Paste the original image in the center
        bordered_img.paste(img, (border_width, border_width), img)
        
        # Save the processed image
        bordered_img.save(output_path, 'PNG')
        print(f"Processed logo with white border saved to: {output_path}")
        return True
    except Exception as e:
        print(f"Error processing logo: {e}")
        return False

if __name__ == '__main__':
    # Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    input_logo = os.path.join(project_root, 'frontend', 'src', 'Gemini_Generated_Image_wlisx4wlisx4wlis.png')
    output_logo_src = os.path.join(project_root, 'frontend', 'src', 'logo.png')
    output_logo_public = os.path.join(project_root, 'frontend', 'public', 'logo.png')
    output_favicon = os.path.join(project_root, 'frontend', 'public', 'favicon.png')
    
    # Check if input exists
    if not os.path.exists(input_logo):
        print(f"Error: Logo file not found at {input_logo}")
        sys.exit(1)
    
    # Process logo for src folder (larger, for components)
    print("Processing logo for components...")
    if remove_white_background(input_logo, output_logo_src, threshold=240, border_width=2):
        print("[OK] Logo processed for components with white border")
    
    # Process logo for public folder (for favicon and direct access)
    print("Processing logo for public folder...")
    if remove_white_background(input_logo, output_logo_public, threshold=240, border_width=2):
        print("[OK] Logo processed for public folder with white border")
    
    # Create favicon (32x32 or 64x64)
    print("Creating favicon...")
    try:
        img = Image.open(output_logo_public)
        # Resize to common favicon sizes
        favicon_sizes = [(32, 32), (64, 64), (16, 16)]
        favicon_images = []
        for size in favicon_sizes:
            favicon_img = img.resize(size, Image.Resampling.LANCZOS)
            favicon_images.append(favicon_img)
        
        # Save as ICO format (multi-size)
        img.save(output_favicon, 'PNG')
        print(f"[OK] Favicon created at {output_favicon}")
    except Exception as e:
        print(f"Error creating favicon: {e}")
    
    print("\nLogo processing complete!")
    print(f"  - Component logo: {output_logo_src}")
    print(f"  - Public logo: {output_logo_public}")
    print(f"  - Favicon: {output_favicon}")

