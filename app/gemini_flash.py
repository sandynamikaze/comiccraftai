import os
import json

from dotenv import load_dotenv
from google import genai


# Load .env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")


# Create Gemini client
client = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_outline(
    story_prompt,
    character_name,
    setting,
    tone,
    art_style
):

    prompt = f"""
Create a five-panel comic outline.

Story prompt:
{story_prompt}

Character name:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

Return ONLY valid JSON.

The JSON must be an array containing exactly 5 objects.

Each object must contain:

- panel_number
- title
- scene_description
- image_prompt

Example format:

[
  {{
    "panel_number": 1,
    "title": "Beginning",
    "scene_description": "Description of the scene",
    "image_prompt": "Detailed prompt for generating the image"
  }}
]
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    text = response.text.strip()

    # Remove markdown code fences if Gemini adds them
    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    try:
        outline = json.loads(text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Gemini returned invalid JSON:\n{text}"
        ) from e

    if not isinstance(outline, list):
        raise RuntimeError("Gemini outline is not a list.")

    if len(outline) != 5:
        raise RuntimeError(
            f"Expected 5 panels, but Gemini returned {len(outline)}."
        )

    return outline