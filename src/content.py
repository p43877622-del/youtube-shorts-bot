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
        "prompt": """Tu es un créateur de contenu YouTube Shorts en français speialise dans le viral.
Genere un script pour une video courte (35-45 secondes) sur le theme: {category}.

Format de reponse STRICT (reponds UNIQUEMENT ce JSON, rien d'autre):

{{
  "titre": "Titre qui donne envie de cliquer (max 60 car., utiliser 'secret', 'pourquoi', 'cette raison', 'jamais', 'personne ne sait')",
  "accroche": "Accroche qui stoppe le scroll en 1 seconde - chiffre choquant ou question intrigante",
  "faits": [
    "Fait 1",
    "Fait 2",
    "Fait 3",
    "Fait 4",
    "Fait 5",
    "Fait 6",
    "Fait 7"
  ],
  "outro": "Conclusion qui connecte a l'accroche (effet boucle)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Regles:
- 7 faits, chaque fait tient en UNE phrase (< 15 mots)
- Faits surprenants, verificables, qui donnent envie de partager
- L'accroche doit creer un FOSSE DE CURIOSITE des la 1ere seconde
- LE TITRE doit utiliser un mot puissant: secret, pourquoi, cette raison, jamais, personne, incroyable
- Langage simple, ton dynamique, accessible a tous
- Public vise: francophone general (Afrique, Europe)
- EFFET BOUCLE: l'outro et l'accroche se connectent naturellement (la fin ramene au debut)
""",
    },
    {
        "name": "question-reponse",
        "prompt": """Tu es un createur de contenu YouTube Shorts en francais specialise dans les quiz viraux.
Genere un script pour une video courte (35-45 secondes) sur le theme: {category}, format question-reponse.

Format de reponse STRICT (reponds UNIQUEMENT ce JSON):

{{
  "titre": "Question qui intrigue + mot puissant (max 60 car.)",
  "accroche": "Question choc qui stoppe le scroll en 1 seconde",
  "faits": [
    "Question 1 ? Reponse : explication courte",
    "Question 2 ? Reponse : explication courte",
    "Question 3 ? Reponse : explication courte",
    "Question 4 ? Reponse : explication courte",
    "Question 5 ? Reponse : explication courte",
    "Question 6 ? Reponse : explication courte",
    "Question 7 ? Reponse : explication courte"
  ],
  "outro": "Question finale qui donne envie de commenter",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Regles:
- 7 questions, format question + reponse pour chaque
- Questions surprenantes qui donnent envie de repondre en commentaire
- Reponses courtes et claires (< 15 mots)
- L'accroche doit etre une question qui cree un fosse de curiosite
- LE TITRE doit etre une question qui donne envie de cliquer
- Public vise: francophone general (Afrique, Europe)
- EFFET BOUCLE: la derniere question ramene a la premiere
""",
    },
    {
        "name": "liste rapide",
        "prompt": """Tu es un createur de contenu YouTube Shorts en francais.
Genere un script pour une video courte (30-40 secondes) sur le theme: {category}.
Style: classement rapide et dynamique, comme un top 7.

Format de reponse STRICT (reponds UNIQUEMENT ce JSON):

{{
  "titre": "Classement surprise avec mot puissant (max 50 car.)",
  "accroche": "Phrase choc qui annonce le classement et intrigue",
  "faits": [
    "Numero 7 : ...",
    "Numero 6 : ...",
    "Numero 5 : ...",
    "Numero 4 : ...",
    "Numero 3 : ...",
    "Numero 2 : ...",
    "Numero 1 : ..."
  ],
  "outro": "Revelation finale percutante qui connecte a l'accroche",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Regles:
- 7 elements, chaque fait commence par son numero
- Tres rythme, phrases tres courtes (< 10 mots)
- Le numero 1 doit etre le plus impressionnant (garder le meilleur pour la fin)
- L'accroche doit creer un fosse de curiosite: "Vous ne devinerez jamais le numero 1"
- LE TITRE doit eviter 'TOP 7' - preferer 'Les X les plus [adjectif]' ou 'Le classement [theme]'
- Public vise: francophone general (Afrique, Europe)
- EFFET BOUCLE: la fin ramene au debut
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
