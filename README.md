# Bot YouTube Shorts IA

Génère et publie automatiquement des YouTube Shorts chaque jour.

## Comment ça marche

1. Choisit un thème (science, histoire, animaux, etc.)
2. Génère un script via Google Gemini IA
3. Crée une voix off naturelle avec edge-tts
4. Monte une vidéo avec images + texte
5. Publie automatiquement sur YouTube
6. Ajoute des liens d'affiliation dans la description

## Configuration (une seule fois, 15 minutes)

### 1. Crée un compte Google Cloud
- Va sur https://console.cloud.google.com/
- Crée un projet → APIs & Services
- Active **YouTube Data API v3**
- Crée un écran de consentement OAuth (External, ajoute ton email comme test)
- Crée des identifiants OAuth 2.0 → **Application de bureau**
- Télécharge le JSON, renomme-le `client_secret.json`

### 2. Obtiens une clé Gemini
- Va sur https://aistudio.google.com/apikey
- Crée une clé API gratuite

### 3. Exécute la configuration
```bash
python setup.py
```
Un navigateur s'ouvre → connecte-toi → autorise

### 4. Crée un dépôt GitHub
- https://github.com/new
- Ajoute les **Secrets** (Settings → Secrets and variables → Actions):
  - `GEMINI_API_KEY` = ta clé Gemini
  - `YOUTUBE_TOKEN` = contenu de `token.pickle` en base64
  - `CLIENT_SECRET` = contenu de `client_secret.json` en base64

### 5. Pousse le code sur GitHub
```bash
git init
git add .
git commit -m "Mon bot Shorts"
git remote add origin https://github.com/TON_COMPTE/youtube-shorts-bot.git
git push -u origin main
```

### 6. Active GitHub Actions
Va dans l'onglet Actions de ton dépôt → Active les workflows.
Le bot générera 1 Short par jour automatiquement.

## Secrets GitHub requis

| Secret | Description |
|--------|-------------|
| `GEMINI_API_KEY` | Clé API Google Gemini |
| `YOUTUBE_TOKEN` | Token OAuth YouTube (base64) |
| `CLIENT_SECRET` | Fichier client_secret.json (base64) |

## Personnalisation

- Modifie les catégories dans `src/content.py`
- Modifie les liens d'affiliation dans `src/upload.py`
- Modifie la fréquence dans `.github/workflows/generate-shorts.yml`
