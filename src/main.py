import os
import sys
import json
import tempfile
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.content import generate_script
from src.audio import generate_audio
from src.video import create_video
from src.upload import upload_video

def main():
    print("=== GÉNÉRATION DU SHORT ===")

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        sys.exit("ERREUR: OPENROUTER_API_KEY non définie")

    try:
        script = generate_script(api_key=api_key)
        print(f"Thème: {script['category']}")
        print(f"Titre: {script['titre']}")
        print(f"Faits: {len(script['faits'])}")
    except Exception as e:
        sys.exit(f"Erreur génération contenu: {e}")

    try:
        audio_path = generate_audio(script["full_text"], "temp_audio.mp3")
        print(f"Audio OK ({os.path.getsize(audio_path)} bytes)")
    except Exception as e:
        sys.exit(f"Erreur génération audio: {e}")

    try:
        video_path = create_video(script, audio_path, "temp_video.mp4")
        if not os.path.exists(video_path):
            sys.exit("Erreur: fichier vidéo non créé")
        print(f"Vidéo OK ({os.path.getsize(video_path)} bytes)")
    except Exception as e:
        sys.exit(f"Erreur création vidéo: {e}")

    try:
        video_id = upload_video(video_path, script, script["category"])
        print(f"✅ Vidéo publiée: https://youtube.com/shorts/{video_id}")
    except Exception as e:
        print(f"❌ Erreur upload: {e}")
        traceback.print_exc()
        sys.exit(1)

    for f in ["temp_audio.mp3", "temp_video.mp4"]:
        if os.path.exists(f):
            os.remove(f)

    print("=== TERMINÉ ===")

if __name__ == "__main__":
    main()
