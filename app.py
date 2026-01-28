from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import List
import re
from starlette.concurrency import run_in_threadpool
from Prompt_analyzer_agent import structure_with_gpt
from validation_file import validate_ocr_file
from input_module import ocr_image_bytes, ocr_pdf_bytes
from dotenv import load_dotenv

load_dotenv()

def clean_text(text: str, keep_newlines: bool = False) -> str:
    if not text:
        return ""
    text = text.replace("\t", " ").replace("\r", " ")
    if not keep_newlines:
        text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("<", "").replace(">", "")

    return text.strip()

# FastAPI

app = FastAPI(
    title="Devminds OCR 🚀",
    description="Advanced Multi-language OCR API (Images & PDFs)",
    version="2.0.0"
)


@app.get("/")
async def root():
    return {
        "service": "Devminds OCR",
        "languages": ["English", "Urdu", "Arabic"],
        "formats": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"],
        "docs": "PDFs Files"
    }
@app.get("/health")
async def health_check():
    return {"status": "healthy, PLease visit documentation:"}

# For Images without GPT Model 

@app.post("/extract-images")
async def extract_images(
    files: List[UploadFile] = File(..., description="Upload multiple image files:")
):
    for file in files:

        validation = validate_ocr_file(file.filename)

        if validation["type"] != "image":
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": validation.get("type"),
                "message": "Unsupported file format",
                "allowed_image_formats": validation.get("allowed_image_formats", [])
            })

        try:
            image_bytes = await file.read()
            raw_text = await run_in_threadpool(ocr_image_bytes, image_bytes)
            cleaned_text = clean_text(raw_text, keep_newlines=True)
            return JSONResponse(content={
                "success": True,
                "valid": True,
                "type": "image",
                "message": "OCR extracted successfully",
                "text": cleaned_text
            })

        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": "image",
                "message": f"OCR failed: {str(e)}"
            })

# For PDF without GPT Model 

@app.post("/extract-pdfs")
async def extract_pdfs(
    files: List[UploadFile] = File(..., description="Upload multiple PDF files:")
):
    combined_texts = []

    for file in files:

        validation = validate_ocr_file(file.filename)

        if validation.get("type") != "pdf":
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": validation.get("type"),
                "message": "Unsupported file format",
                "allowed_document_formats": validation.get("allowed_document_formats", [])
            })

        try:
            pdf_bytes = await file.read()
            
            raw_text = await run_in_threadpool(ocr_pdf_bytes, pdf_bytes)
            cleaned_text = clean_text(raw_text, keep_newlines=True)
            combined_texts.append(cleaned_text)

        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": "pdf",
                "message": f"OCR failed: {str(e)}"
            })

    return JSONResponse(content={
        "success": True,
        "valid": True,
        "type": "pdf",
        "message": "OCR extracted successfully",
        "data": "\n\n".join(combined_texts)
    })
    
# This Endpoint is using for text extraction with structing data

@app.post("/ocr/structure")
async def structure_text(
    files: List[UploadFile] = File(..., description="Upload images or PDFs for text extraction:"),
    structuring_prompt: str = Form(None, description="Write what you want to extract text from the images and PDFs files:")
):
    combined_texts = []
    processed_types = set()

    for file in files:
        validation = validate_ocr_file(file.filename)

        if not validation["valid"]:
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": validation.get("type"),
                "message": "Unsupported file format",
                "allowed_image_formats": validation.get("allowed_image_formats", []),
                "allowed_document_formats": validation.get("allowed_document_formats", [])
            })

        processed_types.add(validation.get("type"))

        try:
            file_bytes = await file.read()

            if validation["type"] == "image":
                raw_text = await run_in_threadpool(ocr_image_bytes, file_bytes)
            elif validation["type"] == "pdf":
                raw_text = await run_in_threadpool(ocr_pdf_bytes, file_bytes)

            cleaned_text = clean_text(raw_text, keep_newlines=True)
            combined_texts.append(cleaned_text)

        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": validation.get("type"),
                "message": f"OCR failed: {str(e)}"
            })

    full_text = "\n\n".join(combined_texts).strip()

    if not full_text:
        return JSONResponse(content={
            "success": False,
            "valid": False,
            "type": ", ".join(processed_types) if processed_types else None,
            "message": "No valid OCR text extracted"
        })

    gpt_response = await run_in_threadpool(
        structure_with_gpt,
        full_text,
        structuring_prompt
    )

    if not gpt_response.get("success"):
        return JSONResponse(content=gpt_response)

    return JSONResponse(content={
        "success": True,
        "valid": True,
        "type": ", ".join(processed_types),
        "message": "OCR and structuring completed successfully",
        "data": {
            "raw_text": full_text,
            "structured_json": gpt_response["data"]
        }
    })
    
    
    
    
