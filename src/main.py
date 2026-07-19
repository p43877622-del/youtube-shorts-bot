import os
import sys
import json
import time
import logging
import tempfile
import traceback
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.content import generate_script
from src.audio import generate_audio
from src.video import create_video
from src.upload import upload_video, upload_thumbnail
from src.thumbnail import generate_thumbnail

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

def step(name):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            log.info(f"▶ {name}")
            start = time.time()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.time() - start
                log.info(f"✓ {name} — {elapsed:.1f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start
                log.error(f"✗ {name} — {elapsed:.1f}s — {e}")
                raise
        return wrapper
    return decorator

@step("Génération du contenu")
def gen_content(api_key):
    for attempt in range(3):
        try:
            script = generate_script(api_key=api_key)
            log.info(f"  Thème: {script['category']}")
            log.info(f"  Titre: {script['titre']}")
            log.info(f"  Faits: {len(script['faits'])}")
            return script
        except Exception as e:
            if attempt < 2:
                log.warning(f"  Tentative {attempt+1}/3: {e}. Nouvel essai dans 5s...")
                time.sleep(5)
            else:
                raise

@step("Génération audio")
def gen_audio(text):
    path = generate_audio(text, "temp_audio.mp3")
    log.info(f"  Taille: {os.path.getsize(path)} bytes")
    return path

@step("Création vidéo")
def make_video(script, audio_path):
    path = create_video(script, audio_path, "temp_video.mp4")
    if not os.path.exists(path):
        raise FileNotFoundError("Vidéo non créée")
    log.info(f"  Taille: {os.path.getsize(path)} bytes")
    return path

@step("Upload vidéo")
def upload(video_path, script, category):
    video_id = upload_video(video_path, script, category)
    log.info(f"  URL: https://youtube.com/shorts/{video_id}")
    return video_id

@step("Upload miniature")
def upload_thumb(video_id, script):
    thumb_path = generate_thumbnail(script, "temp_thumb.jpg")
    upload_thumbnail(video_id, thumb_path)

def main():
    log.info("=" * 50)
    log.info("GÉNÉRATION DU SHORT — DÉMARRAGE")
    log.info("=" * 50)

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        log.error("OPENROUTER_API_KEY non définie")
        sys.exit(1)

    script = gen_content(api_key)
    audio_path = gen_audio(script["full_text"])
    video_path = make_video(script, audio_path)
    video_id = upload(video_path, script, script["category"])
    upload_thumb(video_id, script)

    for f in ["temp_audio.mp3", "temp_video.mp4", "temp_thumb.jpg"]:
        if os.path.exists(f):
            os.remove(f)

    log.info("=" * 50)
    log.info("TERMINÉ AVEC SUCCÈS")
    log.info("=" * 50)

if __name__ == "__main__":
    main()
