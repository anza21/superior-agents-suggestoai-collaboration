import os
import requests
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from PIL import Image
import numpy as np

# Pillow compatibility for resampling
if hasattr(Image, 'Resampling'):
    RESAMPLE = Image.Resampling.LANCZOS
else:
    RESAMPLE = Image.LANCZOS

def download_images(image_urls, output_folder="slideshow_images"):
    os.makedirs(output_folder, exist_ok=True)
    local_paths = []
    for i, url in enumerate(image_urls):
        ext = url.split(".")[-1].split("?")[0]
        local_path = os.path.join(output_folder, f"img_{i}.{ext}")
        try:
            r = requests.get(url, timeout=10)
            with open(local_path, "wb") as f:
                f.write(r.content)
            local_paths.append(local_path)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
    return local_paths

def make_slideshow(image_paths, audio_path=None, output_path="slideshow.mp4", duration_per_image=2.5):
    def resize_clip(img):
        return ImageClip(img).set_duration(duration_per_image).resize(width=720)
    # Patch moviepy's resize to use the correct resample
    from moviepy.video.fx import resize as mp_resize
    orig_resizer = mp_resize.resizer
    def patched_resizer(pic, newsize):
        pilim = Image.fromarray(pic)
        resized_pil = pilim.resize(tuple(int(x) for x in newsize[::-1]), RESAMPLE)
        return np.array(resized_pil)
    mp_resize.resizer = patched_resizer
    clips = [resize_clip(img) for img in image_paths]
    video = concatenate_videoclips(clips, method="compose")
    if audio_path:
        audio = AudioFileClip(audio_path)
        video = video.set_audio(audio)
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    mp_resize.resizer = orig_resizer  # Restore original
    return output_path

if __name__ == "__main__":
    # Demo usage
    image_urls = [
        "https://ae-pic-a1.aliexpress-media.com/kf/Se51bf07b1d564b89b0149f61060f9d20W.jpg",
        "https://ae-pic-a1.aliexpress-media.com/kf/Sab9ab2ac52194d28b77ec4b036a71b430.jpg",
        "https://ae-pic-a1.aliexpress-media.com/kf/Sc18cb7f55aff4778914f39a0d5d8db09v.jpg"
    ]
    print("Downloading images...")
    imgs = download_images(image_urls)
    print("Making slideshow...")
    out = make_slideshow(imgs, audio_path=None, output_path="slideshow_demo.mp4")
    print(f"Done! Video saved as {out}") 