import os
import asyncio
import random
import edge_tts

VOICES = [
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
    "fr-CA-SylvieNeural",
    "fr-CH-ArianeNeural",
    "fr-BE-CharlineNeural",
]
RATES = {
    "accroche": "+5%",
    "normal": "+10%",
    "outro": "+8%",
}

async def generate_audio_async(text, output_path="output.mp3"):
    voice = random.choice(VOICES)
    communicate = edge_tts.Communicate(text, voice, rate=RATES["normal"])
    await communicate.save(output_path)
    return output_path

def generate_audio(text, output_path="output.mp3"):
    asyncio.run(generate_audio_async(text, output_path))
    return output_path

if __name__ == "__main__":
    text = "Le saviez-vous ? Le cœur humain bat environ cent mille fois par jour. Incroyable non ?"
    path = generate_audio(text, "test_audio.mp3")
    print(f"Audio généré: {path}")
