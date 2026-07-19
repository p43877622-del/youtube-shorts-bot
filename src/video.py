import os
import math
import random
import tempfile
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip
from moviepy.video.fx import Resize, SlideIn
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

FONT_CACHE = {}
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"

ACCENT_COLORS = [
    (255, 200, 50),
    (50, 200, 255),
    (255, 100, 100),
    (100, 255, 100),
    (200, 100, 255),
    (255, 150, 50),
]

def zoom_in_effect(clip, zoom_ratio=0.04):
    def effect(get_frame, t):
        img = Image.fromarray(get_frame(t))
        base_size = img.size
        new_size = [
            math.ceil(img.size[0] * (1 + (zoom_ratio * t))),
            math.ceil(img.size[1] * (1 + (zoom_ratio * t))),
        ]
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)
        img = img.resize(new_size, Image.LANCZOS)
        x = math.ceil((new_size[0] - base_size[0]) / 2)
        y = math.ceil((new_size[1] - base_size[1]) / 2)
        img = img.crop([x, y, new_size[0] - x, new_size[1] - y]).resize(base_size, Image.LANCZOS)
        result = np.array(img)
        img.close()
        return result
    return clip.transform(effect)

MUSIC_URLS = [
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3",
]

def get_font(size, weight=400):
    cache_key = f"montserrat-{size}-{weight}"
    if cache_key in FONT_CACHE:
        return FONT_CACHE[cache_key]
    font_path = os.path.join(tempfile.gettempdir(), f"montserrat-{weight}.ttf")
    if not os.path.exists(font_path):
        try:
            r = requests.get(FONT_URL, timeout=10)
            if r.status_code == 200:
                with open(font_path, "wb") as f:
                    f.write(r.content)
        except:
            pass
    if os.path.exists(font_path):
        try:
            FONT_CACHE[cache_key] = ImageFont.truetype(font_path, size)
            return FONT_CACHE[cache_key]
        except:
            pass
    return ImageFont.load_default()

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

def create_text_image(text, size=(1000, 300), font_size=48, accent_color=None):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = get_font(font_size)

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

    if accent_color:
        r, g, b = accent_color
        bg = Image.new("RGBA", size, (0, 0, 0, 160))
        img = Image.alpha_composite(img, bg)
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, y_start - 10, size[0], y_start + total_h + 10], fill=(r, g, b, 40))
    else:
        bg = Image.new("RGBA", size, (0, 0, 0, 180))
        img = Image.alpha_composite(img, bg)

    draw = ImageDraw.Draw(img)
    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (size[0] - (bbox[2] - bbox[0])) // 2
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 128))
        if accent_color:
            draw.text((x, y), line, font=font, fill=accent_color + (255,))
        else:
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += font_size + 10

    return img

def create_watermark(size=(1080, 1920)):
    img = Image.new("RGBA", (300, 50), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(24, 600)
    text = "Faits Incroyables"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.rectangle([0, 0, tw + 30, th + 20], fill=(0, 0, 0, 100))
    draw.text((15, 10), text, font=font, fill=(255, 255, 255, 180))
    return img

def create_fact_counter(current, total, size=(1080, 1920)):
    img = Image.new("RGBA", (120, 50), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(20, 600)
    text = f"{current}/{total}"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.rounded_rectangle([5, 5, tw + 25, th + 15], radius=8, fill=(0, 0, 0, 120))
    draw.text((15, 10), text, font=font, fill=(255, 200, 50, 255))
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

def download_backgrounds(count, tmpdir):
    paths = []
    for i in range(count):
        path = os.path.join(tmpdir, f"bg_{i}.jpg")
        ok = False
        seed = random.randint(0, 99999)
        try:
            r = requests.get(
                f"https://picsum.photos/seed/{seed}/1080/1920",
                timeout=15,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if r.status_code == 200:
                with open(path, "wb") as f:
                    f.write(r.content)
                Image.open(path).convert("RGB").resize((1080, 1920), Image.LANCZOS).save(path, "JPEG", quality=85)
                ok = True
        except:
            pass
        if not ok:
            for url in BG_IMAGES:
                if download_background(url, path):
                    ok = True
                    break
        if not ok:
            make_fallback_bg(path)
        paths.append(path)
    return paths

def create_video(script, audio_path, output_path="output.mp4"):
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio introuvable: {audio_path}")

    audio = AudioFileClip(audio_path)
    duration = audio.duration

    if duration > 58:
        audio = audio.subclip(0, 58)
        duration = 58

    with tempfile.TemporaryDirectory() as tmpdir:
        all_texts = []
        if script.get("accroche"):
            all_texts.append(script["accroche"])
        all_texts.extend(script.get("faits", []))
        if script.get("outro"):
            all_texts.append(script["outro"])

        total_chars = max(1, sum(len(t) for t in all_texts))
        total_segments = len(all_texts)

        bg_paths = download_backgrounds(total_segments, tmpdir)

        clips = []
        current_time = 0.0

        for i, text in enumerate(all_texts):
            is_last = i == len(all_texts) - 1
            text_duration = max(2.0, (len(text) / total_chars) * duration)
            if current_time + text_duration > duration:
                text_duration = duration - current_time
            if text_duration <= 0.5:
                break

            bg_clip = ImageClip(bg_paths[i], duration=text_duration)
            bg_clip = zoom_in_effect(bg_clip, zoom_ratio=0.06)
            bg_clip = bg_clip.with_start(current_time)
            clips.append(bg_clip)

            color = ACCENT_COLORS[i % len(ACCENT_COLORS)]
            txt_img = create_text_image(
                text, font_size=42 if len(text) < 50 else 36, accent_color=color
            )
            txt_arr = np.array(txt_img)
            txt_clip = ImageClip(txt_arr, duration=text_duration)
            txt_clip = txt_clip.with_position(("center", 1250))
            txt_clip = txt_clip.with_start(current_time)
            txt_clip = txt_clip.with_effects([SlideIn(0.3, "bottom")])
            clips.append(txt_clip)

            if i > 0 and i - 1 < total_segments:
                counter_img = create_fact_counter(i, total_segments)
                counter_arr = np.array(counter_img)
                counter_clip = ImageClip(counter_arr, duration=text_duration)
                counter_clip = counter_clip.with_position(("left", "top"))
                counter_clip = counter_clip.with_start(current_time)
                clips.append(counter_clip)

            current_time += text_duration

        wm_img = create_watermark()
        wm_arr = np.array(wm_img)
        wm_clip = ImageClip(wm_arr, duration=duration)
        wm_clip = wm_clip.with_position(("right", "top"))
        clips.append(wm_clip)

        music_path = os.path.join(tmpdir, "music.mp3")
        music_ok = False
        music_url = random.choice(MUSIC_URLS)
        try:
            r = requests.get(music_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                with open(music_path, "wb") as f:
                    f.write(r.content)
                music_ok = True
        except:
            pass

        if music_ok and os.path.getsize(music_path) > 10000:
            try:
                bg_music = AudioFileClip(music_path).with_effects([
                    AudioFadeIn(1.0), AudioFadeOut(2.0)
                ])
                bg_music = bg_music.with_volume_scaled(0.08)
                bg_music = bg_music.with_duration(duration)
                final_audio = CompositeAudioClip([audio, bg_music])
            except:
                final_audio = audio
        else:
            final_audio = audio

        video = CompositeVideoClip(clips, size=(1080, 1920))
        video = video.with_audio(final_audio)
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
