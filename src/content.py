import os
import json
import random
import google.generativeai as genai

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
"""

def generate_script(api_key=None):
    if api_key:
        genai.configure(api_key=api_key)
    else:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY non trouvée")
        genai.configure(api_key=api_key)

    category = random.choice(CATEGORIES)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = FACT_TEMPLATE.format(category=category)

    response = model.generate_content(prompt)

    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        script = json.loads(text)
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
        script = result

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

if __name__ == "__main__":
    s = generate_script()
    print(json.dumps(s, ensure_ascii=False, indent=2))
