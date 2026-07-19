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

FACT_TEMPLATE = """Tu es un créateur de contenu YouTube Shorts en français.
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
- EFFET BOUCLE: L'outro et l'accroche doivent se connecter naturellement (la fin ramène au début pour un visionnage en boucle)
"""

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
    category = random.choice(CATEGORIES)
    prompt = FACT_TEMPLATE.format(category=category)

    providers_to_try = list(PROVIDERS)
    random.shuffle(providers_to_try)

    if api_key:
        providers_to_try.insert(0, {
            "name": "Custom",
            "base_url": "https://openrouter.ai/api/v1",
            "api_key_var": None,
            "model": "openrouter/free",
            "headers": {"HTTP-Referer": "https://github.com/p43877622-del/youtube-shorts-bot"},
        })

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
                return {
                    "titre": script.get("titre", "Incroyable !"),
                    "accroche": script.get("accroche", ""),
                    "faits": script.get("faits", []),
                    "outro": script.get("outro", ""),
                    "full_text": full_text,
                    "tags": script.get("tags", ["shorts", "faits"]),
                    "category": category,
                }
        except Exception as e:
            last_error = e
            continue

    raise ValueError(f"Génération échouée: {last_error}")

if __name__ == "__main__":
    s = generate_script()
    print(json.dumps(s, ensure_ascii=False, indent=2))
