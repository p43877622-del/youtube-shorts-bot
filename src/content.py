import os
import json
import random
from openai import OpenAI

CATEGORIES = [
    "science et nature",
    "histoire et cultures du monde",
    "technologie et innovations",
    "corps humain et santé",
    "animaux et espèces rares",
    "espace et astronomie",
    "phénomènes mystérieux",
    "records du monde et exploits",
    "alimentation et nutrition",
    "inventions qui ont changé le monde",
]

TEMPLATES = [
    {
        "name": "faits insolites",
        "prompt": """Tu es un créateur de contenu YouTube Shorts en français.
Génère un script pour une vidéo courte (20-25 secondes) sur le thème: {category}.

Format de réponse STRICT (réponds UNIQUEMENT ce JSON, rien d'autre):

{{
  "titre": "LE TITRE ACCROCHEUR (max 60 caractères)",
  "accroche": "Une phrase d'accroche choc pour les 3 premières secondes",
  "faits": [
    "Fait intéressant 1 (une phrase courte et percutante)",
    "Fait intéressant 2",
    "Fait intéressant 3",
    "Fait intéressant 4",
    "Fait intéressant 5"
  ],
  "outro": "Une phrase de conclusion marquante",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Règles:
- Chaque fait doit tenir en UNE phrase courte (< 15 mots)
- Les faits doivent être surprenants, vérifiables et intéressants
- Langage simple et direct, accessible à tous
- Ton dynamique et captivant
- PUBLIC VISÉ: francophone général (Afrique, Europe)
- EFFET BOUCLE: L'outro et l'accroche doivent se connecter naturellement (la fin ramène au début)
""",
    },
    {
        "name": "question-réponse",
        "prompt": """Tu es un créateur de contenu YouTube Shorts en français spécialisé dans les quiz.
Génère un script pour une vidéo courte (20-25 secondes) sur le thème: {category}, sous format question-réponse.

Format de réponse STRICT (réponds UNIQUEMENT ce JSON):

{{
  "titre": "Titre accrocheur avec question (max 60 car.)",
  "accroche": "Une question qui intrigue pour les 3 premières secondes",
  "faits": [
    "Question 1 ? Réponse : explication courte",
    "Question 2 ? Réponse : explication courte",
    "Question 3 ? Réponse : explication courte",
    "Question 4 ? Réponse : explication courte",
    "Question 5 ? Réponse : explication courte"
  ],
  "outro": "Phrase qui donne envie d'en savoir plus",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Règles:
- Format question + réponse pour chaque fait
- Questions surprenantes qui donnent envie de répondre
- Réponses courtes et claires (< 15 mots)
- PUBLIC VISÉ: francophone général (Afrique, Europe)
- EFFET BOUCLE: La dernière question ramène à la première
""",
    },
    {
        "name": "liste rapide",
        "prompt": """Tu es un créateur de contenu YouTube Shorts en français.
Génère un script pour une vidéo courte (15-20 secondes) sur le thème: {category}.
Style: liste rapide et dynamique, comme un top 5.

Format de réponse STRICT (réponds UNIQUEMENT ce JSON):

{{
  "titre": "TOP 5 [catégorie] (max 50 car.)",
  "accroche": "Accroche ultra-rapide qui annonce le top",
  "faits": [
    "Numéro 5 : ...",
    "Numéro 4 : ...",
    "Numéro 3 : ...",
    "Numéro 2 : ...",
    "Numéro 1 : ..."
  ],
  "outro": "Phrase de conclusion percutante",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Règles:
- Chaque fait doit commencer par son numéro
- Très rythmé, phrases très courtes (< 10 mots)
- Le numéro 1 doit être le plus impressionnant
- PUBLIC VISÉ: francophone général (Afrique, Europe)
- EFFET BOUCLE: La fin ramène au début
""",
    },
]

CATEGORY_HASHTAGS = {
    "science": "#science #decouverte #savoirs #apprendre #curiosite #biologie #physique #chimie",
    "histoire": "#histoire #passe #culture #patrimoine #civilisation #archeologie #lecon #histoireDeFrance",
    "technologie": "#tech #innovation #futur #numerique #hightech #IA #intelligenceArtificielle #gadget",
    "santé": "#sante #bienetre #corps #medecine #vitalite #fitness #nutrition #santeNaturelle",
    "animaux": "#animaux #nature #faune #especes #sauvage #animauxDrole #curiositeAnimal #biodiversite",
    "espace": "#espace #astronomie #univers #planetes #etoiles #NASA #astrophysique #cosmos",
    "mystere": "#mystere #inexplique #phenomene #enigme #secrets #paranormal #mysteresDuMonde #etrange",
    "records": "#records #exploits #guiness #mondial #challenge #incroyable #performances #recordDuMonde",
    "alimentation": "#nutrition #alimentation #sante #cuisine #bienmanger #recette #gastronomie #food",
    "general": "#culturegenerale #savoir #apprendre #curiosite #intelligence #connaissance #shorts #education",
}

VIRAL_HASHTAGS = "#pourtoi #fyp #viral #tendance #shorts #shortsYouTube #decouvrir"

USED_FILE = ".used_categories.json"

def _get_available_categories():
    used = []
    if os.path.exists(USED_FILE):
        try:
            with open(USED_FILE, "r") as f:
                used = json.load(f)
        except:
            pass
    available = [c for c in CATEGORIES if c not in used]
    if not available:
        available = CATEGORIES
        used = []
    return available, used

def _mark_used(category, used):
    used.append(category)
    with open(USED_FILE, "w") as f:
        json.dump(used, f)

def get_hashtags(category):
    for key, tags in CATEGORY_HASHTAGS.items():
        if key in category:
            return tags
    return CATEGORY_HASHTAGS["general"]

PROVIDERS = [
    {
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_key_var": "OPENROUTER_API_KEY",
        "model": "openrouter/free",
        "headers": {"HTTP-Referer": "https://github.com/p43877622-del/youtube-shorts-bot"},
    },
    {
        "name": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_var": "GROQ_API_KEY",
        "model": "llama3-70b-8192",
        "headers": {},
    },
]

def _call_provider(provider, prompt):
    api_key = os.environ.get(provider["api_key_var"])
    if not api_key:
        return None
    client = OpenAI(
        api_key=api_key,
        base_url=provider["base_url"],
        default_headers=provider["headers"] if provider["headers"] else None,
    )
    response = client.chat.completions.create(
        model=provider["model"],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def _parse_script(text):
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lines = text.split("\n")
        result = {"titre": "", "accroche": "", "faits": [], "outro": "", "tags": []}
        current_key = None
        for line in lines:
            line = line.strip()
            if '"titre"' in line:
                result["titre"] = line.split(":", 1)[1].strip().strip('",')
                current_key = "titre"
            elif '"accroche"' in line:
                result["accroche"] = line.split(":", 1)[1].strip().strip('",')
                current_key = "accroche"
            elif '"outro"' in line:
                result["outro"] = line.split(":", 1)[1].strip().strip('",')
                current_key = None
            elif '"faits"' in line:
                current_key = "faits"
            elif '"tags"' in line:
                current_key = "tags"
            elif current_key == "faits" and line.startswith('"'):
                fait = line.strip().strip('",')
                if fait:
                    result["faits"].append(fait)
            elif current_key == "tags" and '"' in line:
                tag = line.strip().strip('",')
                if tag and not tag.startswith("]"):
                    result["tags"].append(tag.replace('"', "").strip())
        return result

def _is_valid_script(script):
    if not script.get("titre") or not script.get("accroche"):
        return False
    if len(script.get("faits", [])) < 3:
        return False
    if not script.get("outro"):
        return False
    return True

def generate_script(api_key=None):
    available, used = _get_available_categories()
    category = random.choice(available)
    _mark_used(category, used)

    template = random.choice(TEMPLATES)
    prompt = template["prompt"].format(category=category)

    providers_to_try = list(PROVIDERS)
    random.shuffle(providers_to_try)

    last_error = None
    for provider in providers_to_try:
        try:
            key = api_key if provider["api_key_var"] is None else os.environ.get(provider["api_key_var"])
            if not key:
                continue
            text = _call_provider(provider, prompt)
            if not text:
                continue
            script = _parse_script(text)
            if _is_valid_script(script):
                full_text = script["accroche"] + ". " + " ".join(script["faits"]) + ". " + script["outro"]
                tags = script.get("tags", [])
                if isinstance(tags, str):
                    tags = [tags]
                tags_str = " ".join(f"#{t}" for t in tags) if tags else ""
                return {
                    "titre": script.get("titre", "Incroyable !"),
                    "accroche": script.get("accroche", ""),
                    "faits": script.get("faits", []),
                    "outro": script.get("outro", ""),
                    "full_text": full_text,
                    "tags": tags,
                    "tags_str": tags_str,
                    "hashtags": get_hashtags(category),
                    "viral_hashtags": VIRAL_HASHTAGS,
                    "category": category,
                    "template": template["name"],
                }
        except Exception as e:
            last_error = e
            continue

    raise ValueError(f"Génération échouée: {last_error}")

if __name__ == "__main__":
    s = generate_script()
    print(json.dumps(s, ensure_ascii=False, indent=2))
