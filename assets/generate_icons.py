"""Generate placeholder icon files for the application."""
from PIL import Image, ImageDraw
import os

# Ensure assets dir exists (when run standalone)
os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)


def create_icon():
    # Create a 256x256 RGBA image
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a simple book shape
    draw.rectangle([40, 30, 216, 226], fill=(41, 98, 255), outline=(20, 50, 180), width=3)
    draw.rectangle([50, 30, 60, 226], fill=(20, 50, 180))   # spine
    draw.line([70, 80, 200, 80],  fill=(255, 255, 255), width=3)
    draw.line([70, 110, 200, 110], fill=(255, 255, 255), width=3)
    draw.line([70, 140, 160, 140], fill=(255, 255, 255), width=3)

    assets_dir = os.path.dirname(os.path.abspath(__file__))

    # Save PNG
    png_path = os.path.join(assets_dir, 'icon.png')
    img.save(png_path, 'PNG')
    print(f"Saved: {png_path}")

    # Save ICO with multiple sizes
    ico_path = os.path.join(assets_dir, 'icon.ico')
    img_256 = img.resize((256, 256), Image.LANCZOS)
    img_256.save(
        ico_path,
        format='ICO',
        sizes=[(16, 16), (32, 32), (48, 48), (256, 256)],
    )
    print(f"Saved: {ico_path}")


if __name__ == '__main__':
    create_icon()
