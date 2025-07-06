import sys
print('PYTHONPATH:', sys.path)
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
import os

# Requires: pip install moviepy
# Για captions: δώσε srt file (μπορείς να το παράγεις από το script)

def compose_video(
    video_path="output.mp4",
    audio_path="output_tts.mp3",
    music_path=None,
    captions_path=None,
    output_path="final_video.mp4"
):
    video = VideoFileClip(video_path)
    audio = AudioFileClip(audio_path)
    clips = [audio]
    if music_path:
        music = AudioFileClip(music_path).volumex(0.2)  # Χαμηλή ένταση
        clips.append(music)
    final_audio = CompositeAudioClip(clips)
    video = video.set_audio(final_audio)
    if captions_path:
        generator = lambda txt: TextClip(txt, font='Arial', fontsize=32, color='white', bg_color='black')
        subs = SubtitlesClip(captions_path, generator)
        video = CompositeVideoClip([video, subs.set_pos(('center','bottom'))])
    video.write_videofile(output_path, codec="libx264", audio_codec="aac")
    return output_path

if __name__ == "__main__":
    # Demo usage
    print("Composing video...")
    out = compose_video(
        video_path="output.mp4",
        audio_path="demo_tts_output.mp3",
        music_path=None,  # π.χ. "background.mp3"
        captions_path=None,  # π.χ. "captions.srt"
        output_path="final_video.mp4"
    )
    print(f"Done! Video saved as {out}") 