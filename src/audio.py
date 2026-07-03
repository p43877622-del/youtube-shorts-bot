import os
import asyncio
import edge_tts

VOICE = "fr-FR-DeniseNeural"
RATE = "+10%"

async def generate_audio_async(text, output_path="output.mp3"):
    communicate = edge_tts.Communicate(text, VOICE, rate=RATE)
    await communicate.save(output_path)
    return output_path

def generate_audio(text, output_path="output.mp3"):
    asyncio.run(generate_audio_async(text, output_path))
    return output_path

if __name__ == "__main__":
    text = "Le saviez-vous ? Le cœur humain bat environ cent mille fois par jour. Incroyable non ?"
    path = generate_audio(text, "test_audio.mp3")
    print(f"Audio généré: {path}")
