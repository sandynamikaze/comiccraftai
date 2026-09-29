import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


# --------------------------------------------------
# Load .env
# --------------------------------------------------

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN is missing from .env")


# --------------------------------------------------
# Project paths
# --------------------------------------------------

# Get the main ComicCraftAI folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# static/panels folder
OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "static",
    "panels"
)

# Create folder if it does not exist
os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


# --------------------------------------------------
# Hugging Face
# --------------------------------------------------

client = InferenceClient(
    api_key=HF_TOKEN,
    provider="auto"
)

MODEL_NAME = "black-forest-labs/FLUX.1-schnell"


# --------------------------------------------------
# Generate image
# --------------------------------------------------

def generate_image(prompt, panel_number):

    final_prompt = f"""
    Comic book illustration.
    High quality.
    Detailed composition.
    Clear main character.
    Expressive face.
    Consistent comic art style.
    Strong visual storytelling.
    No text inside the image.

    {prompt}
    """

    print(f"Generating image for panel {panel_number}...")

    image = client.text_to_image(
        prompt=final_prompt,
        model=MODEL_NAME
    )

    filename = f"panel_{panel_number}.png"

    filepath = os.path.join(
        OUTPUT_DIR,
        filename
    )

    image.save(filepath)

    print(f"Panel {panel_number} saved:")
    print(filepath)

    return "/static/panels/" + filename