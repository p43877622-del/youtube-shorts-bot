import os
import sys
import random
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.video import get_font

def generate_thumbnail(script, output_path="thumb.jpg"):
    img = Image.new("RGB", (1280, 720), (10, 10, 35))
    draw = ImageDraw.Draw(img)

    for _ in range(15):
        c = random.choice([
            (20, 40, 100), (60, 20, 80), (20, 70, 60),
            (90, 30, 40), (30, 50, 110), (80, 20, 50),
        ])
        x = random.randint(0, 1280)
        y = random.randint(0, 720)
        r = random.randint(100, 500)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c + (80,), outline=None)

    title = script.get("titre", "Incroyable !")
    font = get_font(56, 700)
    lines = []
    words = title.split()
    current = ""
    for w in words:
        test = current + " " + w if current else w
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > 1100:
            if current:
                lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    bg_rect_h = len(lines) * 70 + 60
    draw.rectangle([40, 330, 1240, 330 + bg_rect_h], fill=(0, 0, 0, 180))

    font_title = get_font(52, 700)
    y = 360
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_title)
        x = (1280 - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, font=font_title, fill=(0, 0, 0, 200))
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255, 255))
        y += 70

    font_cta = get_font(28, 400)
    cta = "Regarde ça !"
    bbox = draw.textbbox((0, 0), cta, font=font_cta)
    cx = (1280 - (bbox[2] - bbox[0])) // 2
    draw.text((cx, 600), cta, font=font_cta, fill=(255, 200, 50, 255))

    img.save(output_path, "JPEG", quality=90)
    return output_path

if __name__ == "__main__":
    test = {"titre": "5 faits INCROYABLES sur la science"}
    generate_thumbnail(test, "test_thumb.jpg")
    print("Thumbnail créée: test_thumb.jpg")
