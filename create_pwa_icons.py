# create_pwa_icons.py
from PIL import Image
import os

def create_pwa_icons(source_path):
    # Ensure the source file exists
    if not os.path.exists(source_path):
        print(f"Source file {source_path} not found!")
        return
    
    # Open the source image
    with Image.open(source_path) as img:
        # Convert to RGB if necessary (handles JPEG)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Create square version (PWA icons should be square)
        width, height = img.size
        size = min(width, height)
        
        # Crop to square
        left = (width - size) // 2
        top = (height - size) // 2
        right = (width + size) // 2
        bottom = (height + size) // 2
        img = img.crop((left, top, right, bottom))
        
        # Create all required sizes
        sizes = [72, 96, 128, 144, 152, 192, 384, 512]
        
        for size in sizes:
            # Resize image
            resized_img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Save as PNG (required for PWA)
            output_path = f'static/dist/img/icon-{size}x{size}.png'
            resized_img.save(output_path, 'PNG')
            print(f"Created: {output_path}")

# Run the conversion
source_image = 'static/dist/img/download (2).jpg'
create_pwa_icons(source_image)
print("All PWA icons created successfully!")