import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "products_images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS = [
    {
        "id": "stickers",
        "title": "Custom Stickers",
        "badge": "20 ETB",
        "emoji": "🏷",
        "bg_color": (254, 243, 199),  # amber-100
        "border_color": (245, 158, 11),  # amber-500
        "sub": "Peel & Stick • High Resolution Vinyl"
    },
    {
        "id": "bookmarks",
        "title": "Aesthetic Bookmarks",
        "badge": "50 ETB",
        "emoji": "🔖",
        "bg_color": (254, 249, 195),  # yellow-100
        "border_color": (234, 179, 8),
        "sub": "Durable Gloss / Matte Finish"
    },
    {
        "id": "business_cards",
        "title": "Business Cards",
        "badge": "10 ETB",
        "emoji": "💼",
        "bg_color": (241, 245, 249),  # slate-100
        "border_color": (100, 116, 139),
        "sub": "Sharp Printing • Clean Edges"
    },
    {
        "id": "mini_notebook",
        "title": "Mini Notebook",
        "badge": "200 ETB",
        "emoji": "📓",
        "bg_color": (254, 242, 242),  # rose-100
        "border_color": (244, 63, 94),
        "sub": "Pocket Sized • Custom Cover"
    },
    {
        "id": "notebook",
        "title": "Custom Notebook",
        "badge": "500 ETB",
        "emoji": "📔",
        "bg_color": (255, 251, 235),  # amber-50
        "border_color": (217, 119, 6),
        "sub": "Quality Ruled / Plain Paper"
    },
    {
        "id": "minibook",
        "title": "Photo Minibook",
        "badge": "600 ETB",
        "emoji": "📖",
        "bg_color": (243, 232, 255),  # purple-100
        "border_color": (168, 85, 247),
        "sub": "Art & Memory Collections"
    },
    {
        "id": "polaroid",
        "title": "Polaroid Prints",
        "badge": "Custom",
        "emoji": "📸",
        "bg_color": (240, 253, 250),  # teal-50
        "border_color": (20, 184, 166),
        "sub": "Vintage Nostalgic Photo Style"
    },
    {
        "id": "mug",
        "title": "Custom Printed Mug",
        "badge": "1,500 ETB",
        "emoji": "☕",
        "bg_color": (255, 247, 237),  # orange-50
        "border_color": (249, 115, 22),
        "sub": "Ceramic • Dishwasher Safe"
    },
    {
        "id": "puzzle",
        "title": "Photo Jigsaw Puzzle",
        "badge": "1,500 ETB",
        "emoji": "🧩",
        "bg_color": (238, 242, 255),  # indigo-50
        "border_color": (99, 102, 241),
        "sub": "Personalized Gift Puzzle"
    },
    {
        "id": "sticker_poster_a5",
        "title": "Sticker Poster A5",
        "badge": "40 ETB (Min 10)",
        "emoji": "🟢",
        "bg_color": (240, 253, 244),  # green-50
        "border_color": (34, 197, 94),
        "sub": "Peel & Stick: Wall, Glass, Wood"
    },
    {
        "id": "sticker_poster_a4",
        "title": "Sticker Poster A4",
        "badge": "70 ETB (Min 10)",
        "emoji": "🟢",
        "bg_color": (236, 253, 245),  # emerald-50
        "border_color": (16, 185, 129),
        "sub": "Peel & Stick: Full A4 Size"
    }
]

def generate_banner(prod: dict):
    width = 600
    height = 360
    img = Image.new("RGB", (width, height), prod["bg_color"])
    draw = ImageDraw.Draw(img)

    # Outer border
    draw.rectangle([(8, 8), (width - 9, height - 9)], outline=prod["border_color"], width=4)

    # Inner decorative dashed-look frame
    draw.rectangle([(16, 16), (width - 17, height - 17)], outline=(255, 255, 255), width=2)

    # Brand header at top
    header_text = "SELORA PRINTS • ADDIS ABABA"
    draw.text((width // 2, 40), header_text, fill=(120, 120, 120), anchor="mm")

    # Center Title
    title_text = prod["title"]
    draw.text((width // 2, 140), title_text, fill=(30, 41, 59), anchor="mm")

    # Subtitle
    sub_text = prod["sub"]
    draw.text((width // 2, 190), sub_text, fill=(71, 85, 105), anchor="mm")

    # Price Badge Box at bottom
    badge_w, badge_h = 240, 50
    bx0 = (width - badge_w) // 2
    by0 = 250
    bx1 = bx0 + badge_w
    by1 = by0 + badge_h

    draw.rounded_rectangle([(bx0, by0), (bx1, by1)], radius=12, fill=prod["border_color"])
    draw.text((width // 2, by0 + 25), prod["badge"], fill=(255, 255, 255), anchor="mm")

    # Save
    out_file = OUTPUT_DIR / f"{prod['id']}.png"
    img.save(out_file, "PNG")
    print(f"Generated {out_file.name}")

if __name__ == "__main__":
    for p in PRODUCTS:
        generate_banner(p)
    print("All initial product images generated successfully!")

