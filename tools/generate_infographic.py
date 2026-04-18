import argparse
import base64
import os
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import io

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)


def get_env(key):
    val = os.getenv(key)
    if not val or not val.strip():
        raise ValueError(f"Missing env var: {key}")
    return val.strip()


def generate_infographic(prompt: str, filename_hint: str = "infographic") -> str:
    api_key = get_env('NANOBANANA_API_KEY')
    tmp_dir = os.path.join(os.path.dirname(__file__), '..', '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    client = genai.Client(api_key=api_key)

    print(f"[generate_infographic] Generating image for: {prompt[:80]}...")

    response = client.models.generate_images(
        model="imagen-4.0-fast-generate-001",
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="16:9",
            output_mime_type="image/png",
        ),
    )

    if not response.generated_images:
        raise ValueError(
            "No image returned by Imagen. "
            "Try simplifying the prompt (avoid specific people, logos, or copyrighted content)."
        )

    image_bytes = response.generated_images[0].image.image_bytes

    slug = re.sub(r'[^a-z0-9]+', '_', filename_hint.lower())[:30]
    timestamp = int(time.time())
    out_path = os.path.join(tmp_dir, f"infographic_{slug}_{timestamp}.png")

    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)

    img = Image.open(io.BytesIO(image_bytes))
    img.save(out_path, "PNG")

    print(f"[generate_infographic] Image saved ({img.size[0]}x{img.size[1]}px) → {out_path}")
    return os.path.abspath(out_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate an infographic using Gemini")
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument("--hint", default="infographic", help="Filename hint for output file")
    args = parser.parse_args()

    path = generate_infographic(args.prompt, args.hint)
    print(f"Output: {path}")
