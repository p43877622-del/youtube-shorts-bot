import os
import logging
import requests

log = logging.getLogger(__name__)

def get_credentials():
    page_id = os.environ.get("FB_PAGE_ID")
    access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    return page_id, access_token

def upload_video_to_facebook(video_path, description):
    page_id, access_token = get_credentials()
    if not page_id or not access_token:
        log.warning("FB_PAGE_ID ou FB_PAGE_ACCESS_TOKEN non configurés — Facebook ignoré")
        return None

    url = f"https://graph.facebook.com/v21.0/{page_id}/videos"
    with open(video_path, "rb") as f:
        files = {"source": f}
        data = {
            "description": description,
            "access_token": access_token,
            "published": "true",
        }
        log.info("  Upload Facebook Reel en cours...")
        r = requests.post(url, files=files, data=data, timeout=180)

    if r.status_code != 200:
        log.error(f"  Erreur Facebook upload: {r.status_code} {r.text}")
        return None

    result = r.json()
    video_id = result.get("id")
    if video_id:
        log.info(f"  Facebook Reel uploadé: https://facebook.com/{page_id}/videos/{video_id}")
        return video_id
    log.error(f"  Réponse Facebook inattendue: {result}")
    return None

def post_comment_affiliate_link(video_id, message):
    access_token = os.environ.get("FB_PAGE_ACCESS_TOKEN")
    if not access_token or not video_id:
        return False

    url = f"https://graph.facebook.com/v21.0/{video_id}/comments"
    data = {
        "message": message,
        "access_token": access_token,
    }
    try:
        r = requests.post(url, data=data, timeout=15)
        if r.status_code == 200:
            log.info("  Lien d'affiliation posté en commentaire Facebook")
            return True
        log.warning(f"  Erreur commentaire Facebook: {r.status_code} {r.text}")
    except Exception as e:
        log.warning(f"  Erreur commentaire Facebook: {e}")
    return False
