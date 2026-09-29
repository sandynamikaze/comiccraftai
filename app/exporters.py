import os
import unicodedata
from datetime import datetime

from fpdf import FPDF


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


OUTPUT_DIR = os.path.join(
    BASE_DIR,
    "static",
    "exports"
)


os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)


def clean_text(text):
    """
    Convert Unicode text into text supported
    by the built-in PDF font.
    """

    if text is None:
        return ""

    text = str(text)

    # Replace common Unicode characters
    replacements = {
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "…": "...",
        "•": "-",
        "→": "->",
        "←": "<-",
        "★": "*",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove any remaining unsupported Unicode characters
    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = text.encode(
        "ascii",
        "ignore"
    ).decode(
        "ascii"
    )

    return text


def save_pdf(layout):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    filename = f"comic_{timestamp}.pdf"

    filepath = os.path.join(
        OUTPUT_DIR,
        filename
    )


    pdf = FPDF()


    for panel in layout:

        pdf.add_page()


        # Panel title
        pdf.set_font(
            "Arial",
            "B",
            18
        )


        title = clean_text(
            f"Panel {panel['panel_number']}: "
            f"{panel['title']}"
        )


        pdf.cell(
            0,
            12,
            title,
            ln=True
        )


        # Image
        image_path = panel["image"]


        if image_path.startswith("/"):
            image_path = image_path[1:]


        image_path = os.path.join(
            BASE_DIR,
            image_path.replace(
                "/",
                os.sep
            )
        )


        if os.path.exists(image_path):

            pdf.image(
                image_path,
                x=15,
                y=30,
                w=180
            )


        pdf.ln(115)


        # Scene description
        pdf.set_font(
            "Arial",
            "I",
            11
        )


        scene_description = clean_text(
            panel["scene_description"]
        )


        pdf.multi_cell(
            0,
            7,
            scene_description
        )


        pdf.ln(5)


        # Caption
        pdf.set_font(
            "Arial",
            "B",
            11
        )


        caption = clean_text(
            "Caption: " + panel["caption"]
        )


        pdf.multi_cell(
            0,
            7,
            caption
        )


        pdf.ln(3)


        # Narration
        pdf.set_font(
            "Arial",
            "",
            11
        )


        narration = clean_text(
            "Narration: " + panel["narration"]
        )


        pdf.multi_cell(
            0,
            7,
            narration
        )


        pdf.ln(3)


        # Dialogue
        dialogue = clean_text(
            "Dialogue: " + panel["dialogue"]
        )


        pdf.multi_cell(
            0,
            7,
            dialogue
        )


    pdf.output(filepath)


    return "/" + os.path.relpath(
        filepath,
        BASE_DIR
    ).replace(
        "\\",
        "/"
    )