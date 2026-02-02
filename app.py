from fastapi import FastAPI, UploadFile, File, Form, Depends
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
    
from sqlalchemy.orm import Session
from database_config.models import User
from database_config.api_key_table import APIKey
from database_config.main import get_db
from security import hash_password
from schema.login_schema import RegisterSchema
from fastapi import HTTPException
import secrets

@app.post("/auth/register", status_code=201)
def register(user: RegisterSchema, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        return {
            "success": False,
            "message": "Email already registered"
        }

    hashed = hash_password(user.password)

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hashed
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    free_api_key = secrets.token_urlsafe(32)

    api_key = APIKey(
        user_id=new_user.user_id,
        api_key=free_api_key,
        total_hits=2,
        used_hits=0
    )

    db.add(api_key)
    db.commit()

    return {
        "success": True,
        "message": "User registered successfully",
        "free_api_key": free_api_key,
        "free_hits": 2
    }



from fastapi import HTTPException
from security import verify_password
from jwt_utils import create_access_token
from schema.login_schema import LoginSchema


@app.post("/auth/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.user_id})

    return {
        "Login": "You are logged in successfully",
        "access_token": token,
        "token_type": "bearer"
    }








