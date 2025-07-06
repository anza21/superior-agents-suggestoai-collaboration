import os
from google.cloud import texttospeech
from pydub import AudioSegment

# Requires: pip install google-cloud-texttospeech pydub
# Και να έχεις GOOGLE_APPLICATION_CREDENTIALS στο env σου (json credentials file)

def synthesize_speech(text, voice_name, output_path):
    client = texttospeech.TextToSpeechClient()
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=input_text, voice=voice, audio_config=audio_config
    )
    with open(output_path, "wb") as out:
        out.write(response.audio_content)
    return output_path

def split_script_by_voice(script):
    # Returns list of (voice, text) tuples
    lines = script.strip().split("\n")
    result = []
    current_voice = "en-US-Wavenet-D"  # Default male
    buffer = []
    for line in lines:
        if line.strip().startswith("[Male Voice]"):
            if buffer:
                result.append((current_voice, " ".join(buffer)))
                buffer = []
            current_voice = "en-US-Wavenet-D"
        elif line.strip().startswith("[Female Voice]"):
            if buffer:
                result.append((current_voice, " ".join(buffer)))
                buffer = []
            current_voice = "en-US-Wavenet-F"
        else:
            buffer.append(line.strip())
    if buffer:
        result.append((current_voice, " ".join(buffer)))
    return result

def generate_tts_audio(script, output_audio="output_tts.mp3"):
    parts = split_script_by_voice(script)
    audio_segments = []
    for i, (voice, text) in enumerate(parts):
        part_path = f"tts_part_{i}.mp3"
        synthesize_speech(text, voice, part_path)
        audio_segments.append(AudioSegment.from_mp3(part_path))
    final_audio = sum(audio_segments)
    final_audio.export(output_audio, format="mp3")
    # Καθάρισε τα προσωρινά αρχεία
    for i in range(len(parts)):
        os.remove(f"tts_part_{i}.mp3")
    return output_audio

if __name__ == "__main__":
    # Demo usage
    demo_script = """
[Male Voice]
Welcome to SuggestoAI! Today, we're reviewing the brand new SmartWatch X.
[Female Voice]
Is it compatible with both Android and iOS?
[Male Voice]
Absolutely! It works seamlessly with both platforms.
"""
    print("Generating TTS audio...")
    out = generate_tts_audio(demo_script, "demo_tts_output.mp3")
    print(f"Done! Audio saved as {out}") 