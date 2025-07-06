import replicate
import os
from typing import Optional

def generate_image(prompt: str, output_path: str = "output.png") -> Optional[str]:
    try:
        input = {"prompt": prompt}
        output = replicate.run(
            "google/imagen-4",
            input=input
        )
        with open(output_path, "wb") as file:
            file.write(output.read())
        return output_path
    except Exception as e:
        print(f"Error generating image: {e}")
        return None 