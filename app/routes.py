from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf


router = APIRouter()

templates = Jinja2Templates(
    directory="templates"
)


class PromptRequest(BaseModel):

    story_prompt: str
    character_name: str
    setting: str
    tone: str
    art_style: str


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@router.get("/")
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request
        }
    )


# --------------------------------------------------
# GENERATE COMIC FROM HTML FORM
# --------------------------------------------------

@router.post("/generate")
async def generate_comic(
    request: Request,

    story_prompt: str = Form(...),
    character_name: str = Form(...),
    setting: str = Form(...),
    tone: str = Form(...),
    art_style: str = Form(...)
):

    try:

        # Step 1: Generate outline
        outline = generate_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        # Step 2: Generate story
        story = generate_story(
            outline=outline,
            character_name=character_name,
            tone=tone
        )

        # Step 3: Generate images
        images = []

        for panel in outline:

            image_path = generate_image(
                panel["image_prompt"],
                panel["panel_number"]
            )

            images.append(image_path)

        # Step 4: Build comic layout
        layout = build_comic_layout(
            outline=outline,
            story=story,
            images=images
        )

        # Step 5: Create PDF
        pdf_path = save_pdf(layout)

        # Step 6: Show preview
        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "request": request,
                "layout": layout,
                "pdf_path": pdf_path
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------------------------
# GENERATE COMIC FROM JSON
# --------------------------------------------------

@router.post("/generate-comic/json")
async def generate_comic_json(
    data: PromptRequest
):

    try:

        # Step 1: Generate outline
        outline = generate_outline(
            story_prompt=data.story_prompt,
            character_name=data.character_name,
            setting=data.setting,
            tone=data.tone,
            art_style=data.art_style
        )

        # Step 2: Generate story
        story = generate_story(
            outline=outline,
            character_name=data.character_name,
            tone=data.tone
        )

        # Step 3: Generate images
        images = []

        for panel in outline:

            image_path = generate_image(
                panel["image_prompt"],
                panel["panel_number"]
            )

            images.append(image_path)

        # Step 4: Build layout
        layout = build_comic_layout(
            outline=outline,
            story=story,
            images=images
        )

        # Step 5: Create PDF
        pdf_path = save_pdf(layout)

        return {
            "success": True,
            "layout": layout,
            "pdf_path": pdf_path
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------------------------
# TEST IMAGE
# --------------------------------------------------

@router.get("/test-image")
async def test_image():

    try:

        image_path = generate_image(
            "A cute fox in a magical forest, comic book style",
            999
        )

        return {
            "success": True,
            "image": image_path
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------------------------
# EXPORT SUCCESS PAGE
# --------------------------------------------------

@router.get("/export-success")
async def export_success(
    request: Request
):

    return templates.TemplateResponse(
        request=request,
        name="export_success.html",
        context={
            "request": request
        }
    )