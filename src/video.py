import os
import random
import tempfile
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
from moviepy.video.fx import Resize, CrossFadeIn

BG_IMAGES = [
    "https://images.pexels.com/photos/207247/pexels-photo-207247.jpeg?auto=compress&cs=tinysrgb&w=1080",
    "https://images.pexels.com/photos/355465/pexels-photo-355465.jpeg?auto=compress&cs=tinysrgb&w=1080",
    "https://images.pexels.com/photos/110854/pexels-photo-110854.jpeg?auto=compress&cs=tinysrgb&w=1080",
    "https://images.pexels.com/photos/36717/amazing-animal-beautiful-beautifull.jpg?auto=compress&cs=tinysrgb&w=1080",
    "https://images.pexels.com/photos/414171/pexels-photo-414171.jpeg?auto=compress&cs=tinysrgb&w=1080",
    "https://images.pexels.com/photos/1624496/pexels-photo-1624496.jpeg?auto=compress&cs=tinysrgb&w=1080",
    "https://images.pexels.com/photos/19670/pexels-photo.jpg?auto=compress&cs=tinysrgb&w=1080",
    "https://images.pexels.com/photos/1303098/pexels-photo-1303098.jpeg?auto=compress&cs=tinysrgb&w=1080",
]

def create_text_image(text, size=(1000, 300), font_size=48):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype(
                "C:\\Windows\\Fonts\\arial.ttf", font_size
            )
        except:
            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    font_size,
                )
            except:
                font = ImageFont.load_default()

    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > size[0] - 80:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = test
    if current_line:
        lines.append(current_line)

    total_h = len(lines) * (font_size + 10)
    y_start = max(10, (size[1] - total_h) // 2)

    bg = Image.new("RGBA", size, (0, 0, 0, 180))
    img = Image.alpha_composite(img, bg)
    draw = ImageDraw.Draw(img)

    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 128))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += font_size + 10

    return img

def download_background(url, output_path):
    try:
        r = requests.get(
            url, timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            img = Image.open(output_path).convert("RGB")
            img = img.resize((1080, 1920), Image.LANCZOS)
            img.save(output_path, "JPEG", quality=85)
            return True
    except:
        pass
    return False

def make_fallback_bg(path):
    bg = Image.new("RGB", (1080, 1920), (20, 25, 45))
    draw = ImageDraw.Draw(bg)
    colors = [
        (30, 40, 80), (60, 30, 70), (20, 60, 50),
        (80, 40, 30), (40, 50, 90), (70, 30, 60),
    ]
    for _ in range(30):
        c = random.choice(colors)
        x = random.randint(0, 1080)
        y = random.randint(0, 1920)
        r = random.randint(50, 300)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=c + (80,), outline=None)
    bg.save(path, "JPEG", quality=85)

def create_video(script, audio_path, output_path="output.mp4"):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio introuvable: {audio_path}")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    if duration > 58:
        audio = audio.subclip(0, 58)
        duration = 58

    with tempfile.TemporaryDirectory() as tmpdir:
        bg_path = os.path.join(tmpdir, "bg.jpg")
        bg_ok = False

        seed = random.randint(0, 99999)
        try:
            r = requests.get(
                f"https://picsum.photos/seed/{seed}/1080/1920",
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if r.status_code == 200:
                with open(bg_path, "wb") as f:
                    f.write(r.content)
                img = Image.open(bg_path).convert("RGB").resize(
                    (1080, 1920), Image.LANCZOS
                )
                img.save(bg_path, "JPEG", quality=85)
                bg_ok = True
        except:
            pass

        if not bg_ok:
            for url in BG_IMAGES:
                if download_background(url, bg_path):
                    bg_ok = True
                    break

        if not bg_ok:
            make_fallback_bg(bg_path)

        bg_clip = ImageClip(bg_path, duration=duration)
        bg_clip = bg_clip.with_effects([Resize((1080, 1920))])

        clips = [bg_clip]

        all_texts = []
        if script.get("accroche"):
            all_texts.append(script["accroche"])
        all_texts.extend(script.get("faits", []))
        if script.get("outro"):
            all_texts.append(script["outro"])

        total_chars = max(1, sum(len(t) for t in all_texts))
        current_time = 0.0

        for i, text in enumerate(all_texts):
            is_last = i == len(all_texts) - 1
            text_duration = max(
                2.0, (len(text) / total_chars) * duration
            )
            if current_time + text_duration > duration:
                text_duration = duration - current_time
            if text_duration <= 0.5:
                break

            txt_img = create_text_image(
                text, font_size=42 if len(text) < 50 else 36
            )
            txt_arr = np.array(txt_img)
            txt_clip = ImageClip(txt_arr, duration=text_duration)
            txt_clip = txt_clip.with_position(("center", 1250))
            txt_clip = txt_clip.with_start(current_time)

            if is_last:
                txt_clip = txt_clip.with_effects([CrossFadeIn(0.3)])

            clips.append(txt_clip)
            current_time += text_duration

        video = CompositeVideoClip(clips, size=(1080, 1920))
        video = video.with_audio(audio)
        video = video.with_duration(duration)

        video.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=2,
            preset="ultrafast",
            logger=None,
        )

    return output_path

if __name__ == "__main__":
    test_script = {
        "accroche": "Le saviez-vous ? Voici un fait incroyable !",
        "faits": [
            "Le cœur humain bat 100 000 fois par jour.",
            "Un humain cligne des yeux 15 fois par minute.",
        ],
        "outro": "Abonnez-vous pour plus de faits surprenants !",
    }
    test_audio = "test_audio.mp3"
    if os.path.exists(test_audio):
        create_video(test_script, test_audio, "test_video.mp4")
        print("Vidéo de test créée: test_video.mp4")
