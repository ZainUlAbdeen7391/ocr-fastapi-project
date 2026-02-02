import os
import base64
import requests
from pdf2image import convert_from_bytes
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

VISION_URL = "https://vision.googleapis.com/v1/images:annotate"


def _get_api_key():
    api_key = os.getenv("GOOGLE_VISION_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_VISION_API_KEY not set")
    return api_key


# def fix_rtl_text(text: str) -> str:

#     if not text:
#         return ""

#     reshaped = arabic_reshaper.reshape(text)
#     return get_display(reshaped)


# IMAGE OCR 

def ocr_image_bytes(image_bytes: bytes) -> str:

    api_key = _get_api_key()

    encoded = base64.b64encode(image_bytes).decode("utf-8")

    payload = {
        "requests": [{
            "image": {"content": encoded},
            "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            "imageContext": {
                "languageHints": ["ur", "ar", "en"]
            }
        }]
    }

    response = requests.post(
        f"{VISION_URL}?key={api_key}",
        json=payload,
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    raw_text = (
        data["responses"][0]
        .get("fullTextAnnotation", {})
        .get("text", "")
    )

    return raw_text 


# PDF OCR

def ocr_pdf_bytes(pdf_bytes: bytes) -> str:

    full_text = []

    images = convert_from_bytes(pdf_bytes, dpi=300)

    for page_img in images:
        buf = BytesIO()
        page_img.save(buf, format="JPEG")

        page_text = ocr_image_bytes(buf.getvalue())
        full_text.append(page_text)

    return "\n\n".join(full_text).strip()






