#!/usr/bin/env python
"""Create favicon.ico from existing PNG icon"""
try:
    from PIL import Image
    import os
    
    # Path to source icon
    source_icon = os.path.join('static', 'dist', 'img', 'icon-192x192.png')
    output_favicon = os.path.join('static', 'dist', 'img', 'favicon.ico')
    
    if os.path.exists(source_icon):
        # Open the source image
        img = Image.open(source_icon)
        
        # Save as ICO with multiple sizes
        img.save(output_favicon, format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
        print(f'✓ Favicon created: {output_favicon}')
    else:
        print(f'✗ Source icon not found: {source_icon}')
        
except ImportError:
    print('PIL/Pillow not installed. PNG favicon will be used (modern browsers support it).')
except Exception as e:
    print(f'Error creating favicon: {e}')
    print('PNG favicon will be used (modern browsers support it).')

