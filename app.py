from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import List
import re
from starlette.concurrency import run_in_threadpool
from Prompt_analyzer_agent import structure_with_gpt
from validation_file import validate_ocr_file
from input_module import ocr_image_bytes, ocr_pdf_bytes
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database_config.users_table import User
from database_config.api_usage_table import APISummary, to_pkt
from auth_api_key import verify_api_key_only, verify_structure_access
from database_config.main import get_db
from security import hash_password
from schema.login_schema import RegisterSchema
from fastapi import HTTPException
from datetime import date  
from database_config.plan_table import Plan
from fastapi import HTTPException
from security import verify_password
from jwt_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from schema.login_schema import LoginSchema
from sqlalchemy import func
import secrets
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
    files: List[UploadFile] = File(..., description="Upload multiple image files:"),
    _: APISummary = Depends(verify_api_key_only)
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
    files: List[UploadFile] = File(..., description="Upload multiple PDF files:"),
    _:APISummary = Depends(verify_api_key_only)
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
    structuring_prompt: str = Form(None, description="Write what you want to extract text from the images and PDFs files:"),
    _: APISummary = Depends(verify_structure_access)
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
    

# This endpoint is using for register the new user and generate a new api key
# by default it will gives you 5 api hits free with structuring data

from datetime import date, timedelta
import secrets
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

@app.post("/auth/register", status_code=201)
def register(user: RegisterSchema, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    free_plan = db.query(Plan).filter(Plan.name == "free").first()
    if not free_plan:
        raise HTTPException(status_code=500, detail="Free plan not configured")

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        password=hash_password(user.password),
        plan_id=free_plan.id
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    free_api_key = secrets.token_urlsafe(32)

    api_key = APISummary(
        user_id=new_user.user_id,
        api_key=free_api_key,
        used_hits=0,
        last_reset=date.today(),
        is_active=True
    )

    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    api_key.api_end_date = api_key.created_at + timedelta(days=30)
    db.commit()

    # 6️⃣ Response
    return {
        "success": True,
        "message": "User registered successfully",
        "plan": free_plan.name,
        "monthly_limit": free_plan.monthly_hit_limit,
        "api_key": free_api_key,
        "api_issue_date": to_pkt(api_key.created_at),
        "api_end_date": to_pkt(api_key.api_end_date)
    }


# This endpoint is using for login to varify the user is register or not...

@app.post("/auth/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    api_key = db.query(APISummary).filter(
        APISummary.user_id == user.user_id,
       APISummary.is_active == True
    ).first()

    if not api_key:
        raise HTTPException(status_code=403, detail="No active API key found")

    today = date.today()
    if (
        api_key.last_reset.year != today.year
        or api_key.last_reset.month != today.month
    ):
        api_key.used_hits = 0
        api_key.last_reset = today
        db.commit()
        db.refresh(api_key)

    token = create_access_token({"user_id": user.user_id})

    return {
        
        "success": True,
        "message": "You are Logged in successful",
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "user": {
            "user_id": user.user_id
        },
    "api_usage": {
                "monthly_limit": api_key.monthly_limit,
                "used_hits": api_key.used_hits,
                "remaining_hits": api_key.remaining_hits,
                "allow_hits": api_key.allow_hits(),
                "api_issue_date": to_pkt(api_key.created_at),
                "api_end_date": to_pkt(api_key.api_end_date)
                }

            }
    
    
    
    