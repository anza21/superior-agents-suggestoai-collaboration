import os
import requests
import base64
import subprocess
import time

def generate_image_with_webui(prompt, output_path="output.png"):
    url = "http://172.30.224.1:7860/sdapi/v1/txt2img"
    payload = {
        "prompt": prompt,
        "steps": 20,
        "width": 512,
        "height": 512
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        result = response.json()
        image_data = result["images"][0]
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(image_data))
        print(f"Image saved as {output_path}")
        return output_path
    else:
        print("Error:", response.text)
        return None

def generate_video_with_deforum(prompt, output_folder="/mnt/c/Users/anza-/stable-diffusion-webui/outputs/deforum"):
    # Δημιουργία settings file για Deforum
    settings_content = f"""
[general]
prompt_schedule = {{0: '{prompt}'}}
max_frames = 100
width = 512
height = 512
"""
    settings_path = "deforum_settings.txt"
    with open(settings_path, "w") as f:
        f.write(settings_content)
    # Τρέξε το Deforum script μέσω command line στα Windows
    print("Running Deforum for video generation...")
    process = subprocess.Popen([
        "python", "scripts/deforum_render.py", "--settings", settings_path
    ], cwd="/mnt/c/Users/anza-/stable-diffusion-webui")
    process.wait()
    # Βρες το πιο πρόσφατο .mp4 αρχείο στο output folder
    video_files = [f for f in os.listdir(output_folder) if f.endswith(".mp4")]
    if not video_files:
        print("No video found in output folder.")
        return None
    latest_video = max(video_files, key=lambda x: os.path.getctime(os.path.join(output_folder, x)))
    video_path = os.path.join(output_folder, latest_video)
    print(f"Video saved as {video_path}")
    return video_path

if __name__ == "__main__":
    # Παράδειγμα χρήσης για εικόνα
    img_prompt = "A futuristic smartwatch, product photo, white background, high detail"
    generate_image_with_webui(img_prompt, output_path="output_smartwatch.png")

    # Παράδειγμα χρήσης για βίντεο
    video_prompt = "A futuristic smartwatch spinning on a white background, product animation, high detail"
    generate_video_with_deforum(video_prompt, output_folder="C:/Users/anza-/stable-diffusion-webui/outputs/deforum") 