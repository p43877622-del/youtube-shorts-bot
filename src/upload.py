import os
import pickle
import random
import logging
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.pickle"
CLIENT_SECRETS_FILE = "client_secret.json"

# Remplace ces liens par tes liens d'affiliation Chariow après inscription
# Exemple: "https://affiliate.chariow.com/go/ton-lien"
AFFILIATE_LINKS = {
    "science": [
        "https://amzn.to/4bu2u4g",
    ],
    "histoire": [
        "https://amzn.to/4bu2u4g",
    ],
    "technologie": [
        "https://amzn.to/4bu2u4g",
    ],
    "santé": [
        "https://amzn.to/4bu2u4g",
    ],
    "animaux": [
        "https://amzn.to/4bu2u4g",
    ],
    "espace": [
        "https://amzn.to/4bu2u4g",
    ],
    "mystere": [
        "https://amzn.to/4bu2u4g",
    ],
    "records": [
        "https://amzn.to/4bu2u4g",
    ],
    "alimentation": [
        "https://amzn.to/4bu2u4g",
    ],
    "general": [
        "https://amzn.to/4bu2u4g",
        "https://amzn.to/44CEjgm",
    ],
}

AFFILIATE_TEXT = {
    "science": "Decouvre les meilleurs ebooks scientifiques",
    "histoire": "Plonge dans l'histoire avec ces ebooks",
    "technologie": "Ebooks tech et innovation",
    "santé": "Prends soin de toi avec ces lectures",
    "animaux": "Explore la faune avec ces ebooks",
    "espace": "Voyage dans l'univers avec ces ebooks",
    "mystere": "Perce les mysteres avec ces lectures",
    "records": "Les records les plus fous en ebook",
    "alimentation": "Mange mieux avec ces ebooks nutrition",
    "general": "Notre selection d'ebooks culture générale",
}

DESCRIPTION_TEMPLATE_YOUTUBE = """{affiliate_text} : {affiliate_url}

{description}

Abonne-toi pour plus de contenus !

{hashtags}
"""

DESCRIPTION_TEMPLATE_FACEBOOK = """{description}

Abonne-toi pour plus de contenus !

{hashtags}
"""

MAX_DESC_BYTES = 4900

def get_affiliate_link(category):
    affiliate_key = category.split()[0] if category else "general"
    affiliate_key = affiliate_key.lower()
    if affiliate_key not in AFFILIATE_LINKS:
        affiliate_key = "general"
    url = random.choice(AFFILIATE_LINKS[affiliate_key])
    text = AFFILIATE_TEXT.get(affiliate_key, "Decouvre notre selection")
    return text, url

def build_youtube_description(script, category):
    affiliate_text, affiliate_url = get_affiliate_link(category)
    hashtags = script.get("hashtags", "#culturegenerale #shorts")
    viral_hashtags = script.get("viral_hashtags", "#pourtoi #viral #shorts")
    all_hashtags = f"{hashtags} {viral_hashtags}"

    try:
        desc = DESCRIPTION_TEMPLATE_YOUTUBE.format(
            description=script.get("description", "Une video courte pleine de faits surprenants !"),
            affiliate_text=affiliate_text,
            affiliate_url=affiliate_url,
            hashtags=all_hashtags,
        ).strip()
        desc_bytes = desc.encode("utf-8")
        if len(desc_bytes) > MAX_DESC_BYTES:
            desc = desc_bytes[:MAX_DESC_BYTES].decode("utf-8", errors="ignore")
    except Exception:
        desc = script.get("description", "Une video courte pleine de faits surprenants !")
    return desc, affiliate_text, affiliate_url

def build_facebook_description(script, category):
    hashtags = script.get("hashtags", "#culturegenerale #shorts")
    viral_hashtags = script.get("viral_hashtags", "#pourtoi #viral #shorts")
    all_hashtags = f"{hashtags} {viral_hashtags}"

    try:
        desc = DESCRIPTION_TEMPLATE_FACEBOOK.format(
            description=script.get("description", "Une video courte pleine de faits surprenants !"),
            hashtags=all_hashtags,
        ).strip()
    except Exception:
        desc = script.get("description", "Une video courte pleine de faits surprenants !")
    return desc

def get_authenticated_service():
    credentials = None

    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "rb") as f:
                credentials = pickle.load(f)
        except (EOFError, pickle.UnpicklingError):
            credentials = None

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    "client_secret.json introuvable. Exécute d'abord: python setup.py"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRETS_FILE, SCOPES
            )
            credentials = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(credentials, f)

    return build("youtube", "v3", credentials=credentials)

def upload_video(video_path, script, category="general"):
    youtube = get_authenticated_service()

    desc, affiliate_text, affiliate_url = build_youtube_description(script, category)

    hashtags = script.get("hashtags", "#culturegenerale #shorts")
    viral_hashtags = script.get("viral_hashtags", "#pourtoi #viral #shorts")
    hashtag_words = [h.strip("#") for h in (hashtags + " " + viral_hashtags).split()]
    all_tags = script.get("tags", []) + [w for w in hashtag_words if w not in script.get("tags", [])][:20]

    body = {
        "snippet": {
            "title": script["titre"][:100],
            "description": desc,
            "tags": all_tags[:30],
            "categoryId": "22",
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload: {int(status.progress() * 100)}%")

    print(f"Vidéo uploadée: https://youtube.com/shorts/{response['id']}")
    try:
        add_to_playlist(response["id"], category)
    except Exception as e:
        print(f"⚠️ Ajout playlist: {e}")
    return response["id"], affiliate_text, affiliate_url

def upload_thumbnail(video_id, thumbnail_path):
    youtube = get_authenticated_service()
    media = MediaFileUpload(thumbnail_path, chunksize=-1, resumable=True)
    request = youtube.thumbnails().set(videoId=video_id, media_body=media)
    response = request.execute()
    print(f"Miniature uploadée: {response}")
    return response

def add_to_playlist(video_id, category):
    playlist_id = os.environ.get(f"PLAYLIST_{category.split()[0].upper()}")
    if not playlist_id:
        return
    youtube = get_authenticated_service()
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    )
    response = request.execute()
    print(f"Ajouté à la playlist: {response['snippet']['playlistId']}")
    return response

if __name__ == "__main__":
    print("Test upload...")
