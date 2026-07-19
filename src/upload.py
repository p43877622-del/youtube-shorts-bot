import os
import pickle
import random
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = "token.pickle"
CLIENT_SECRETS_FILE = "client_secret.json"

AFFILIATE_LINKS = {
    "science": [
        "https://amzn.to/4bookSciences",
        "https://amzn.to/4science2",
        "https://amzn.to/4science3",
    ],
    "histoire": [
        "https://amzn.to/4bookHistoire",
        "https://amzn.to/4histoire2",
        "https://amzn.to/4histoire3",
    ],
    "space": [
        "https://amzn.to/4bookEspace",
        "https://amzn.to/4space2",
        "https://amzn.to/4space3",
    ],
    "animaux": [
        "https://amzn.to/4bookAnimaux",
        "https://amzn.to/4animaux2",
        "https://amzn.to/4animaux3",
    ],
    "general": [
        "https://amzn.to/4cultureGen",
        "https://amzn.to/4general2",
        "https://amzn.to/4general3",
    ],
}

DESCRIPTION_TEMPLATE = """{description}

SOURCES & RECOMMANDATIONS :
{affiliate_text}
Decouvre notre selection : {affiliate_url}

Abonne-toi pour plus de contenus !

{hashtags}
{tags}
"""

MAX_DESC_BYTES = 4900

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

    affiliate_key = category.split()[0] if category else "general"
    affiliate_key = affiliate_key.lower()
    if affiliate_key not in AFFILIATE_LINKS:
        affiliate_key = "general"

    affiliate_url = random.choice(AFFILIATE_LINKS[affiliate_key])
    affiliate_text = {
        "science": "Les meilleurs livres scientifiques",
        "histoire": "Les livres d'histoire recommandés",
        "space": "Livres sur l'espace et l'astronomie",
        "animaux": "Découvre la faune extraordinaire",
        "general": "Notre sélection culture générale",
    }.get(affiliate_key, "Découvre notre sélection")

    tags_str = " ".join(f"#{t}" for t in script["tags"]) if script.get("tags") else ""
    hashtags = script.get("hashtags", "#culturegenerale #shorts")

    try:
        desc = DESCRIPTION_TEMPLATE.format(
            description=script.get("description", "Une video courte pleine de faits surprenants !"),
            affiliate_text=affiliate_text,
            affiliate_url=affiliate_url,
            hashtags=hashtags,
            tags=tags_str,
        ).strip()
        desc_bytes = desc.encode("utf-8")
        if len(desc_bytes) > MAX_DESC_BYTES:
            desc = desc_bytes[:MAX_DESC_BYTES].decode("utf-8", errors="ignore")
    except Exception:
        desc = script.get("description", "Une video courte pleine de faits surprenants !")

    body = {
        "snippet": {
            "title": script["titre"][:100],
            "description": desc,
            "tags": script.get("tags", []),
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
    return response["id"]

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
