import os
import sys
import random
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.video import get_font, CATEGORY_COLORS, get_category_value

THUMB_COLORS = {
    "science": [(20, 50, 120), (30, 80, 180), (50, 120, 220)],
    "histoire": [(120, 80, 30), (160, 120, 40), (200, 160, 60)],
    "technologie": [(20, 60, 120), (40, 100, 200), (60, 140, 240)],
    "sante": [(30, 100, 60), (50, 160, 90), (70, 200, 120)],
    "animaux": [(30, 100, 40), (50, 160, 60), (70, 200, 80)],
    "espace": [(60, 30, 120), (90, 50, 180), (120, 70, 220)],
    "mystere": [(80, 20, 20), (140, 40, 40), (180, 60, 60)],
    "records": [(120, 60, 20), (180, 100, 40), (220, 140, 60)],
    "alimentation": [(120, 80, 20), (180, 120, 40), (220, 160, 60)],
    "general": [(20, 20, 60), (40, 40, 120), (60, 60, 180)],
}

def generate_thumbnail(script, output_path="thumb.jpg"):
    cat = script.get("category", "general")
    colors = get_category_value(cat, THUMB_COLORS, THUMB_COLORS["general"])
    bg_color = random.choice(colors)

    img = Image.new("RGB", (1280, 720), bg_color)
    draw = ImageDraw.Draw(img)

    for _ in range(20):
        c = random.choice(colors + [(255, 255, 255)])
        x = random.randint(0, 1280)
        y = random.randint(0, 720)
        r = random.randint(80, 400)
        circle = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        c_draw = ImageDraw.Draw(circle)
        c_draw.ellipse([x - r, y - r, x + r, y + r], fill=c + (30,))
        img = Image.alpha_composite(img.convert("RGBA"), circle).convert("RGB")
        draw = ImageDraw.Draw(img)

    title = script.get("titre", "Incroyable !")
    font = get_font(52, 700)
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

    accent = get_category_value(cat, CATEGORY_COLORS, (255, 200, 50))
    bg_rect_h = len(lines) * 70 + 60
    draw.rectangle([40, 280, 1240, 280 + bg_rect_h], fill=(0, 0, 0, 200))

    y = 310
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (1280 - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 200))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += 70

    template = script.get("template", "")
    template_labels = {
        "faits insolites": "SAVAIS-TU ?",
        "question-reponse": "QUIZ",
        "liste rapide": "TOP",
    }
    badge = template_labels.get(template, "SHORTS")
    badge_font = get_font(26, 700)
    bbox = draw.textbbox((0, 0), badge, font=badge_font)
    bw = bbox[2] - bbox[0] + 30
    bh = bbox[3] - bbox[1] + 16
    draw.rounded_rectangle([640 - bw//2, 550, 640 + bw//2, 550 + bh], radius=8, fill=accent)
    draw.text((640 - bw//2 + 15, 555), badge, font=badge_font, fill=(0, 0, 0, 255))

    cta_font = get_font(24, 600)
    cta = "Abonne-toi !"
    bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cx = (1280 - (bbox[2] - bbox[0])) // 2
    draw.text((cx, 650), cta, font=cta_font, fill=accent)

    img.save(output_path, "JPEG", quality=92)
    return output_path

if __name__ == "__main__":
    test = {"titre": "5 faits INCROYABLES sur la science", "category": "science", "template": "faits insolites"}
    generate_thumbnail(test, "test_thumb.jpg")
    print("Thumbnail creee: test_thumb.jpg")
