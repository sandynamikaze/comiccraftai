import os
import base64

from dotenv import load_dotenv
from google import genai


# --------------------------------------------------
# Load .env
# --------------------------------------------------

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "static",
    "panels"
)

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# --------------------------------------------------
# Gemini
# --------------------------------------------------

client = genai.Client(
    api_key=GEMINI_API_KEY
)

MODEL_NAME = "gemini-3.1-flash-image"


# --------------------------------------------------
# Generate image
# --------------------------------------------------

def generate_image(prompt, panel_number):

    final_prompt = f"""
    Create a high-quality comic book illustration.

    Detailed composition.
    Clear main character.
    Expressive face.
    Consistent comic art style.
    Strong visual storytelling.
    Cinematic lighting.
    No text, captions, speech bubbles, or words inside the image.

    Scene:
    {prompt}
    """

    print(f"Generating image for panel {panel_number}...")

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=final_prompt,
        response_format={
            "type": "image",
            "mime_type": "image/png",
            "aspect_ratio": "1:1",
            "image_size": "1K",
        },
    )

    if not interaction.output_image:
        raise RuntimeError(
            "Gemini did not return an image."
        )

    image_data = base64.b64decode(
        interaction.output_image.data
    )

    filename = f"panel_{panel_number}.png"

    filepath = os.path.join(
        OUTPUT_DIR,
        filename
    )

    with open(filepath, "wb") as f:
        f.write(image_data)

    print(f"Panel {panel_number} saved:")
    print(filepath)

    return "/static/panels/" + filename
