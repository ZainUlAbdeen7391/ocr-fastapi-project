from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List
from starlette.concurrency import run_in_threadpool
import re
import os
from openai import OpenAI
from urdu_json import parse_gpt_json
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
        "formats": ["PNG", "JPG", "PDF"],
        "docs": "PDFs Files"
    }
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# For Images

@app.post("/extract-images")
async def extract_images(
    files: List[UploadFile] = File(..., description="Upload multiple image files:")
):
    results = {}

    for file in files:
        if not file.content_type.startswith("image/"):
            results[file.filename] = "Unsupported image format"
            continue

        try:
            image_bytes = await file.read()

            raw_text = await run_in_threadpool(
                ocr_image_bytes, image_bytes
            )

            
            cleaned_text = clean_text(raw_text, keep_newlines=True)

            results[file.filename] = cleaned_text

        except Exception as e:
            results[file.filename] = f"OCR failed: {str(e)}"

    return JSONResponse(content=results)


# for pdfs

@app.post("/extract-pdfs")
async def extract_pdfs(
    files: List[UploadFile] = File(..., description="Upload multiple PDF files:")
):
    results = {}

    for file in files:
        if file.content_type != "application/pdf":
            results[file.filename] = "Unsupported PDF format"
            continue

        try:
            pdf_bytes = await file.read()

            raw_text = await run_in_threadpool(
                ocr_pdf_bytes, pdf_bytes
            )

            
            cleaned_text = clean_text(raw_text, keep_newlines=True)

            results[file.filename] = cleaned_text

        except Exception as e:
            results[file.filename] = f"OCR failed: {str(e)}"

    return JSONResponse(content=results)


# This Code is using for Structured Output 

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def structure_with_gpt(ocr_text: str, prompt: str) -> dict:

    final_prompt = prompt.replace("{text}", ocr_text)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You extract structured data from OCR text."},
            {"role": "user", "content": final_prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


# this endpoint is using for Structuring Extraction

@app.post("/ocr/structure")
async def structure_text(
    files: List[UploadFile] = File(..., description="Load an images and PDFs:"),
    structuring_prompt: str = Form(...,description="Write a prompt for structuring Output:")
):
    combined_ocr_text = []

    for file in files:
        file_bytes = await file.read()

        if file.content_type.startswith("image/"):
            raw_text = await run_in_threadpool(
                ocr_image_bytes, file_bytes
            )

        elif file.content_type == "application/pdf":
            raw_text = await run_in_threadpool(
                ocr_pdf_bytes, file_bytes
            )

        else:
            continue
        
        cleaned_text = clean_text(raw_text, keep_newlines=True)
        combined_ocr_text.append(cleaned_text)

    full_text = "\n\n".join(combined_ocr_text).strip()

    if not full_text:
        raise HTTPException(400, "No OCR text extracted")

    gpt_response = await run_in_threadpool(
        structure_with_gpt,
        full_text,
        structuring_prompt
    )
    structured_json = parse_gpt_json(gpt_response)
    return JSONResponse(
        content={
            "raw_ocr_text": full_text,
            "structured_json": structured_json,
            "display_json": structured_json
                    
        }
    )








