import os
import math
import random
import logging
import tempfile
import requests
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip, ColorClip, AudioClip
from moviepy.video.fx import Resize, SlideIn, FadeOut
from moviepy.audio.fx import AudioFadeIn, AudioFadeOut

log = logging.getLogger(__name__)

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
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-9.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-10.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-11.mp3",
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-12.mp3",
]

CATEGORY_MUSIC = {
    "science": [5, 7, 11],
    "histoire": [2, 9, 3],
    "technologie": [0, 7, 10],
    "santé": [1, 4, 8],
    "animaux": [1, 4, 6],
    "espace": [3, 6, 9],
    "mystere": [6, 8, 11],
    "records": [5, 10, 0],
    "alimentation": [1, 4, 7],
    "general": [0, 1, 2],
}

CATEGORY_COLORS = {
    "science": (50, 200, 255),
    "histoire": (255, 200, 50),
    "technologie": (100, 200, 255),
    "santé": (100, 255, 150),
    "animaux": (100, 255, 100),
    "espace": (200, 100, 255),
    "mystere": (180, 60, 60),
    "records": (255, 150, 50),
    "alimentation": (255, 200, 100),
    "general": (255, 200, 50),
}

def get_category_value(category, mapping, default):
    for key, val in mapping.items():
        if key in category.lower():
            return val
    return default

def create_title_image(title, size=(1080, 1920)):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = get_font(56, 800)
    words = title.split()
    lines = []
    current = ""
    for w in words:
        test = current + " " + w if current else w
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > 900:
            if current:
                lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)

    total_h = len(lines) * 76
    y_start = max(800, (size[1] - total_h) // 2)
    bw = 1000
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        x = (size[0] - lw) // 2
        y = y_start + i * 76
        padding = 20
        draw.rounded_rectangle([x - padding, y - padding, x + lw + padding, y + bbox[3] - bbox[1] + padding], radius=16, fill=(0, 0, 0, 200))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    return img

def create_chime(freq=880, duration=0.15, volume=0.12):
    def make_frame(t):
        t = np.asarray(t)
        env = np.clip(1.0 - t / duration, 0.0, 1.0)
        mono = (np.sin(2 * np.pi * freq * t) * env * 0.5).astype(np.float32)
        return np.column_stack([mono, mono])
    chime = AudioClip(make_frame, duration=duration)
    chime = chime.with_fps(44100)
    return chime.with_volume_scaled(volume)

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
                log.info(f"  Fond {i+1}/{count}: picsum (seed={seed})")
        except:
            pass
        if not ok:
            for url in BG_IMAGES:
                if download_background(url, path):
                    ok = True
                    log.info(f"  Fond {i+1}/{count}: pexels")
                    break
        if not ok:
            make_fallback_bg(path)
            log.info(f"  Fond {i+1}/{count}: fallback")
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

        cat_color = get_category_value(script.get("category", ""), CATEGORY_COLORS, (255, 200, 50))

        for i, text in enumerate(all_texts):
            is_last = i == len(all_texts) - 1
            text_duration = min(5.0, max(2.0, (len(text) / total_chars) * duration))
            if current_time + text_duration > duration:
                text_duration = duration - current_time
            if text_duration <= 0.5:
                break

            bg_clip = ImageClip(bg_paths[i], duration=text_duration)
            bg_clip = zoom_in_effect(bg_clip, zoom_ratio=0.06)
            bg_clip = bg_clip.with_start(current_time)
            clips.append(bg_clip)

            if i == 0:
                color = cat_color
            else:
                color = ACCENT_COLORS[(i - 1) % len(ACCENT_COLORS)]
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

        title_img = create_title_image(script.get("titre", ""))
        title_arr = np.array(title_img)
        title_duration = min(2.0, duration * 0.08)
        title_clip = ImageClip(title_arr, duration=title_duration)
        title_clip = title_clip.with_position(("center", "center"))
        title_clip = title_clip.with_start(0)
        title_clip = title_clip.with_effects([FadeOut(0.5)])
        clips.append(title_clip)

        wm_img = create_watermark()
        wm_arr = np.array(wm_img)
        wm_clip = ImageClip(wm_arr, duration=duration)
        wm_clip = wm_clip.with_position(("right", "top"))
        clips.append(wm_clip)

        progress_bar = ColorClip(size=(1, 6), color=(255, 200, 50), duration=duration)
        progress_bar = progress_bar.with_effects([Resize(lambda t: (max(1, int(1080 * t / duration)), 6))])
        progress_bar = progress_bar.with_position((0, 1914))
        clips.append(progress_bar)

        cta_duration = min(3.0, duration * 0.15)
        cta_start = duration - cta_duration
        if cta_start > 0:
            cta_img = Image.new("RGBA", (600, 100), (0, 0, 0, 0))
            cta_draw = ImageDraw.Draw(cta_img)
            cta_font = get_font(40, 700)
            cta_text = "Abonne-toi 🔔"
            cta_bbox = cta_draw.textbbox((0, 0), cta_text, font=cta_font)
            cta_draw.rounded_rectangle([10, 10, cta_bbox[2] - cta_bbox[0] + 50, cta_bbox[3] - cta_bbox[1] + 30], radius=20, fill=(255, 200, 50, 220))
            cta_draw.text((35, 20), cta_text, font=cta_font, fill=(0, 0, 0, 255))
            cta_arr = np.array(cta_img)
            cta_clip = ImageClip(cta_arr, duration=cta_duration)
            cta_clip = cta_clip.with_position(("center", 900))
            cta_clip = cta_clip.with_start(cta_start)
            cta_clip = cta_clip.with_effects([SlideIn(0.5, "bottom")])
            clips.append(cta_clip)

            comment_img = Image.new("RGBA", (700, 80), (0, 0, 0, 0))
            comment_draw = ImageDraw.Draw(comment_img)
            comment_font = get_font(30, 600)
            comment_text = "Et toi ? Dis-nous en commentaire !"
            comment_bbox = comment_draw.textbbox((0, 0), comment_text, font=comment_font)
            comment_draw.rounded_rectangle([10, 10, comment_bbox[2] - comment_bbox[0] + 50, comment_bbox[3] - comment_bbox[1] + 30], radius=16, fill=(255, 200, 50, 220))
            comment_draw.text((35, 15), comment_text, font=comment_font, fill=(0, 0, 0, 255))
            comment_arr = np.array(comment_img)
            comment_clip = ImageClip(comment_arr, duration=cta_duration)
            comment_clip = comment_clip.with_position(("center", 700))
            comment_clip = comment_clip.with_start(cta_start)
            comment_clip = comment_clip.with_effects([SlideIn(0.5, "bottom")])
            clips.append(comment_clip)

            link_img = Image.new("RGBA", (400, 50), (0, 0, 0, 0))
            link_draw = ImageDraw.Draw(link_img)
            link_font = get_font(22, 500)
            link_text = "📖 Lien en description"
            link_bbox = link_draw.textbbox((0, 0), link_text, font=link_font)
            link_draw.rounded_rectangle([5, 5, link_bbox[2] - link_bbox[0] + 35, link_bbox[3] - link_bbox[1] + 20], radius=12, fill=(0, 0, 0, 160))
            link_draw.text((20, 13), link_text, font=link_font, fill=(255, 255, 255, 220))
            link_arr = np.array(link_img)
            link_clip = ImageClip(link_arr, duration=cta_duration)
            link_clip = link_clip.with_position(("center", 1700))
            link_clip = link_clip.with_start(cta_start)
            clips.append(link_clip)

        music_path = os.path.join(tmpdir, "music.mp3")
        music_ok = False
        cat = script.get("category", "")
        music_indices = get_category_value(cat, CATEGORY_MUSIC, [0, 1, 2])
        music_url = MUSIC_URLS[random.choice(music_indices)]
        try:
            r = requests.get(music_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if r.status_code == 200:
                with open(music_path, "wb") as f:
                    f.write(r.content)
                music_ok = True
        except:
            pass

        chime_times = []
        chime_pos = 0.0
        for i, text in enumerate(all_texts):
            t = max(2.0, (len(text) / total_chars) * duration)
            chime_pos += t
            if chime_pos < duration - 2.0 and i < len(all_texts) - 1:
                chime_times.append(chime_pos)

        audio_layers = [audio]
        if chime_times:
            try:
                chime = create_chime()
                chimes_clip = CompositeAudioClip([chime.with_start(t) for t in chime_times])
                audio_layers.append(chimes_clip)
            except:
                pass

        if music_ok and os.path.getsize(music_path) > 10000:
            try:
                bg_music = AudioFileClip(music_path).with_effects([
                    AudioFadeIn(1.0), AudioFadeOut(2.0)
                ])
                bg_music = bg_music.with_volume_scaled(0.08)
                bg_music = bg_music.with_duration(duration)
                audio_layers.append(bg_music)
            except:
                pass

        final_audio = CompositeAudioClip(audio_layers)

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
