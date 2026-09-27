import os
import json
import time

from dotenv import load_dotenv
from google import genai


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )


# Create Gemini client
client = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_story(
    outline,
    character_name,
    tone
):

    prompt = f"""
Create the narration and dialogue for a five-panel comic.

Character name:
{character_name}

Tone:
{tone}

Comic outline:
{json.dumps(outline, indent=2)}

Return ONLY valid JSON.

The JSON must be an array containing exactly 5 objects.

Each object must contain:

- panel_number
- caption
- narration
- dialogue

Example format:

[
  {{
    "panel_number": 1,
    "caption": "The adventure begins.",
    "narration": "The hero enters the mysterious forest.",
    "dialogue": "Where am I?"
  }}
]

Keep the narration and dialogue suitable for a comic.
"""


    response = None


    # Try Gemini up to 4 times
    for attempt in range(4):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            break


        except Exception as e:

            print(
                f"Gemini attempt {attempt + 1} failed: {e}"
            )


            if attempt == 3:
                raise


            wait_time = 5 * (2 ** attempt)

            print(
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)


    text = response.text.strip()


    # Remove markdown code fences if Gemini adds them
    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()


    try:

        story = json.loads(text)


    except json.JSONDecodeError as e:

        raise RuntimeError(
            f"Gemini returned invalid JSON:\n{text}"
        ) from e


    if not isinstance(story, list):

        raise RuntimeError(
            "Gemini story response is not a list."
        )


    if len(story) != 5:

        raise RuntimeError(
            f"Expected 5 story panels, "
            f"but Gemini returned {len(story)}."
        )


    return story