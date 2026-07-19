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
        "prompt": """Tu es un createur de contenu viral. Genere un script Short (10-15s) sur: {category}.

Format JSON UNIQUEMENT:
{{
  "titre": "Titre court avec mot puissant (secret/pourquoi/jamais) max 50 car.",
  "accroche": "UN CHIFFRE CHOC qui stoppe le scroll (ex: '99% ignorent que...')",
  "faits": ["Fait 1 percutant", "Fait 2 surprenant", "Fait 3 bluffant"],
  "outro": "Phrase boucle qui connecte a l'accroche",
  "tags": ["tag1", "tag2", "tag3"]
}}

Regles:
- 3 faits seulement, chaque fait < 10 mots
- Accroche = FOSSE DE CURIOSITE en 1 seconde avec chiffre
- Langage simple, ton dynamique, public Afrique/Europe
- EFFET BOUCLE: l'outro ramene au debut
""",
    },
    {
        "name": "question-reponse",
        "prompt": """Tu es un createur de quiz viral. Genere un script Short (10-15s) sur: {category}, format question-reponse.

Format JSON UNIQUEMENT:
{{
  "titre": "Question intrigue max 50 car.",
  "accroche": "Question choc qui stoppe le scroll",
  "faits": ["Question 1 ? Reponse courte", "Question 2 ? Reponse courte", "Question 3 ? Reponse courte"],
  "outro": "Question finale pour commenter",
  "tags": ["tag1", "tag2", "tag3"]
}}

Regles:
- 3 questions, format question + reponse
- Questions qui donnent envie de commenter
- Reponses < 10 mots
- Public Afrique/Europe
""",
    },
    {
        "name": "liste rapide",
        "prompt": """Tu es un createur de contenu viral. Genere un script Short (10-15s) sur: {category}. Style: classement rapide Top 3.

Format JSON UNIQUEMENT:
{{
  "titre": "Titre classement max 50 car.",
  "accroche": "Annonce choc du classement qui intrigue",
  "faits": ["Numero 3 : ...", "Numero 2 : ...", "Numero 1 : ..."],
  "outro": "Revelation finale percutante",
  "tags": ["tag1", "tag2", "tag3"]
}}

Regles:
- 3 elements, phrases < 10 mots
- Numero 1 = le plus impressionnant
- Public Afrique/Europe
""",
    },
]

CATEGORY_HASHTAGS = {
    "science": "#science #curiosite",
    "histoire": "#histoire #culture",
    "technologie": "#tech #innovation",
    "santé": "#sante #bienetre",
    "animaux": "#animaux #nature",
    "espace": "#espace #astronomie",
    "mystere": "#mystere #enigme",
    "records": "#records #exploit",
    "alimentation": "#alimentation #nutrition",
    "general": "#culturegenerale #savoir",
}

VIRAL_HASHTAGS = "#pourtoi #viral #shorts"

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
        "model": "llama-3.3-70b-versatile",
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
        max_tokens=512,
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
