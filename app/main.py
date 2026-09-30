import os
import json
import re
import time
import base64
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
GENERATED_DIR = STATIC_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TEXT_MODEL = os.getenv("TEXT_MODEL", "gemini-3.8-flash")
TEXT_FALLBACK_MODEL = os.getenv("TEXT_FALLBACK_MODEL", "gemini-3.8-flash")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gemini-3.1-flash-image")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is missing from the environment.")

client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="ComicCraft AI", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class ComicRequest(BaseModel):
    story_prompt: str = Field(min_length=3, max_length=4000)
    character_name: str = Field(default="Alex", min_length=1, max_length=80)
    setting: str = Field(default="Magical forest", max_length=200)
    tone: str = Field(default="Adventure", max_length=100)
    art_style: str = Field(default="colorful comic book style", max_length=200)


def retry_call(fn):
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return fn()
        except Exception as exc:
            last_error = exc
            message = str(exc)
            retryable = any(x in message for x in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "temporarily"))
            if not retryable or attempt == MAX_RETRIES - 1:
                raise
            time.sleep(2 ** attempt)
    raise last_error


def parse_json(text: str) -> Any:
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.I)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def generate_story(req: ComicRequest) -> list[dict]:
    prompt = f"""
Create a 5-panel comic story.

Story idea: {req.story_prompt}
Main character: {req.character_name}
Setting: {req.setting}
Tone: {req.tone}
Art style: {req.art_style}

Return ONLY valid JSON with this exact shape:
{{
  "title": "short title",
  "panels": [
    {{
      "panel": 1,
      "caption": "short narration",
      "dialogue": "short dialogue or empty string",
      "image_prompt": "detailed visual prompt for this panel"
    }}
  ]
}}

Rules:
- Exactly 5 panels.
- Keep the same main character appearance in every image.
- Each panel should move the story forward.
- Keep dialogue short enough for a comic speech bubble.
- Image prompts must describe composition, characters, environment, lighting and emotion.
- Do not put long written text inside the generated image.
"""
    models = [TEXT_MODEL]
    if TEXT_FALLBACK_MODEL and TEXT_FALLBACK_MODEL not in models:
        models.append(TEXT_FALLBACK_MODEL)

    last_error = None
    for model in models:
        try:
            response = retry_call(lambda: client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    max_output_tokens=2500,
                    response_mime_type="application/json",
                ),
            ))
            data = parse_json(response.text)
            panels = data.get("panels", [])
            if len(panels) != 5:
                raise ValueError("Gemini did not return exactly 5 panels.")
            return panels
        except Exception as exc:
            last_error = exc
    raise last_error


def generate_image(prompt: str, output_path: Path) -> bool:
    full_prompt = f"""
Create a single comic-book panel illustration.

Style: colorful polished comic book art.
{prompt}

Important:
- One coherent scene.
- Strong expressive characters.
- Clear foreground, middle ground and background.
- No watermark.
- Avoid large blocks of text.
- Keep the character visually consistent with the story.
- Landscape composition suitable for a comic panel.
"""
    try:
        interaction = retry_call(lambda: client.interactions.create(
            model=IMAGE_MODEL,
            input=full_prompt,
            response_format={
                "type": "image",
                "mime_type": "image/png",
                "aspect_ratio": "4:3",
                "image_size": "1K",
            },
        ))

        image_data = getattr(getattr(interaction, "output_image", None), "data", None)
        if not image_data:
            # Some SDK versions expose the image inside model_output steps.
            for step in getattr(interaction, "steps", []) or []:
                if getattr(step, "type", None) == "model_output":
                    for block in getattr(step, "content", []) or []:
                        if getattr(block, "type", None) == "image":
                            image_data = getattr(block, "data", None)
                            if image_data:
                                break
                if image_data:
                    break

        if not image_data:
            raise RuntimeError("Image model returned no image data.")

        output_path.write_bytes(base64.b64decode(image_data))
        return True
     except Exception as exc:
        print(f"IMAGE ERROR TYPE: {type(exc).__name__}")
        print(f"IMAGE ERROR: {repr(exc)}")
        return False


def make_placeholder(path: Path, panel_no: int, caption: str):
    img = Image.new("RGB", (1200, 900), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((15, 15, 1185, 885), outline="black", width=8)
    draw.text((60, 60), f"COMIC PANEL {panel_no}", fill="black")
    draw.text((60, 140), "Image generation temporarily unavailable.", fill="black")
    draw.text((60, 220), caption[:180], fill="black")
    img.save(path)


def add_bubble(draw, text, box):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=25, fill="white", outline="black", width=4)
    # Simple line wrapping without external font dependencies.
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if len(test) > 34:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    y = y1 + 18
    for line in lines[:5]:
        draw.text((x1 + 18, y), line, fill="black")
        y += 28


def build_comic(panel_paths: list[Path], panels: list[dict], title: str, output_path: Path):
    W, H = 1600, 2100
    canvas_img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(canvas_img)

    draw.text((70, 35), title[:60], fill="black")
    panel_w, panel_h = 700, 560
    positions = [(70, 150), (830, 150), (70, 780), (830, 780), (450, 1410)]

    for idx, (path, panel) in enumerate(zip(panel_paths, panels)):
        x, y = positions[idx]
        img = Image.open(path).convert("RGB")
        img.thumbnail((panel_w, panel_h))
        px = x + (panel_w - img.width) // 2
        py = y + (panel_h - img.height) // 2
        canvas_img.paste(img, (px, py))
        draw.rectangle((x, y, x + panel_w, y + panel_h), outline="black", width=8)
        dialogue = str(panel.get("dialogue", "")).strip()
        if dialogue:
            add_bubble(draw, dialogue, (x + 25, y + 25, x + min(panel_w - 25, 440), y + 150))
        caption = str(panel.get("caption", "")).strip()
        if caption:
            draw.rectangle((x + 20, y + panel_h - 75, x + panel_w - 20, y + panel_h - 20), fill="white", outline="black", width=2)
            draw.text((x + 35, y + panel_h - 58), caption[:85], fill="black")

    canvas_img.save(output_path, quality=95)


def build_pdf(comic_path: Path, pdf_path: Path):
    c = canvas.Canvas(str(pdf_path), pagesize=A4)
    page_w, page_h = A4
    c.drawImage(ImageReader(str(comic_path)), 20, 20, width=page_w - 40, height=page_h - 40, preserveAspectRatio=True, anchor="c")
    c.save()


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ComicCraft AI"}

@app.get("/test-image")
def test_image():
    test_path = GENERATED_DIR / "test_image.png"

    ok = generate_image(
        "A cute fox in a magical forest, colorful comic book style",
        test_path
    )

    if not ok:
        raise HTTPException(
            status_code=500,
            detail="Image generation failed. Check Render logs."
        )

    return {
        "success": True,
        "image": "/static/generated/test_image.png"
    }


@app.post("/generate")
def generate(req: ComicRequest, request: Request):
    try:
        panels = generate_story(req)
        title = "ComicCraft AI"

        # Title can be generated separately without making the main request fragile.
        try:
            title_prompt = f"Give a short 3-6 word comic title for: {req.story_prompt}. Return only the title."
            title_resp = retry_call(lambda: client.models.generate_content(
                model=TEXT_MODEL,
                contents=title_prompt,
                config=types.GenerateContentConfig(max_output_tokens=30, temperature=0.7),
            ))
            title = title_resp.text.strip().replace('"', "")[:80] or title
        except Exception:
            pass

        panel_paths = []
        public_images = []
        for i, panel in enumerate(panels, start=1):
            filename = f"panel_{int(time.time())}_{i}.png"
            path = GENERATED_DIR / filename
            ok = generate_image(str(panel.get("image_prompt", "")), path)
            if not ok:
                make_placeholder(path, i, str(panel.get("caption", "")))
            panel_paths.append(path)
            public_images.append(str(request.base_url).rstrip("/") + f"/static/generated/{filename}")

        comic_filename = f"comic_{int(time.time())}.png"
        pdf_filename = comic_filename.replace(".png", ".pdf")
        comic_path = GENERATED_DIR / comic_filename
        pdf_path = GENERATED_DIR / pdf_filename

        build_comic(panel_paths, panels, title, comic_path)
        build_pdf(comic_path, pdf_path)

        base = str(request.base_url).rstrip("/")
        return {
            "success": True,
            "title": title,
            "panels": panels,
            "images": public_images,
            "comic_url": f"{base}/static/generated/{comic_filename}",
            "pdf_url": f"{base}/static/generated/{pdf_filename}",
        }

    except Exception as exc:
        message = str(exc)
        if "503" in message or "UNAVAILABLE" in message:
            raise HTTPException(
                status_code=503,
                detail="Gemini is temporarily busy. Please try again in a few seconds."
            )
        raise HTTPException(status_code=500, detail=message)
