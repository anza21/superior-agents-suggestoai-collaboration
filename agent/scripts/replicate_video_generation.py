import replicate
import os
from typing import Optional

def generate_video(prompt: str, output_path: str = "output.mp4") -> Optional[str]:
    try:
        input = {"prompt": prompt}
        output = replicate.run(
            "minimax/video-01",
            input=input
        )
        with open(output_path, "wb") as file:
            file.write(output.read())
        return output_path
    except Exception as e:
        print(f"Error generating video: {e}")
        return None 