from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ADD THIS
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from typing import List
from text_cleaner.clearner import clean_text
from starlette.concurrency import run_in_threadpool
from middleware.Prompt_analyzer_agent import structure_with_gpt
from middleware.validation_file import validate_ocr_file
from controllers.image_pdf_controller import ocr_image_bytes, ocr_pdf_bytes
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from tables.users_table import User
from tables.api_usage_table import APISummary, to_pkt
from middleware.auth_api_key import verify_api_key_only, verify_structure_access
from tables.main import get_db
from middleware.security import hash_password, verify_password
from schema.login_schema import RegisterSchema, LoginSchema
from datetime import date, timedelta
from tables.plan_table import Plan
from Connections.jwt_utils import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi import Request
import secrets
import os 

load_dotenv()

# ---------------- FastAPI ---------------- #

app = FastAPI(
    title="Devminds OCR 🚀",
    description="Advanced Multi-language OCR API (Images & PDFs)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",  # For local development (Live Server)
        "http://127.0.0.1:5500",
        "https://your-frontend-domain.com",  # Your production frontend
        "https://ocr-fastapi-project.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "Devminds OCR",
        "languages": ["English", "Urdu", "Arabic"],
        "formats": [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"],
        "docs": "PDFs Files"
    }

# ---------------- OCR Endpoints ---------------- #




@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    if request.method == "POST":
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return JSONResponse(status_code=413, content={"message": "File too large"})
    return await call_next(request)

@app.post("/extract-images")
async def extract_images(
    files: List[UploadFile] = File(..., description="Upload image files for OCR processing"),
    api_data = Depends(verify_api_key_only)
):

    api = api_data["api"]
    warning = api_data["warning"]

    for file in files:
        validation = validate_ocr_file(file.filename)

        if validation["type"] != "image":
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": validation.get("type"),
                "message": "Unsupported file format"
            })

        image_bytes = await file.read()
        raw_text = await run_in_threadpool(ocr_image_bytes, image_bytes)
        cleaned_text = clean_text(raw_text, keep_newlines=True)

        return JSONResponse(content={
            "success": True,
            "valid": True,
            "type": "image",
            "message": "OCR extracted successfully",
            "text": cleaned_text,
            "remaining_hits": api.remaining_hits,
            "warning": warning
        })

# PDF Endpoint OCR

@app.post("/extract-pdfs")
async def extract_pdfs(
    files: List[UploadFile] = File(..., description="Upload PDF files for OCR processing"),
    api_data = Depends(verify_api_key_only)
):

    api = api_data["api"]
    warning = api_data["warning"]

    combined_texts = []

    for file in files:
        validation = validate_ocr_file(file.filename)

        if validation["type"] != "pdf":
            return JSONResponse(content={
                "success": False,
                "valid": False,
                "type": validation.get("type"),
                "message": "Unsupported file format"
            })

        pdf_bytes = await file.read()
        raw_text = await run_in_threadpool(ocr_pdf_bytes, pdf_bytes)
        cleaned_text = clean_text(raw_text, keep_newlines=True)
        combined_texts.append(cleaned_text)

    return JSONResponse(content={
        "success": True,
        "valid": True,
        "type": "pdf",
        "message": "OCR extracted successfully",
        "data": "\n\n".join(combined_texts),
        "remaining_hits": api.remaining_hits,
        "warning": warning
    })

# Structured Output OCR

@app.post("/ocr/structure")
async def structure_text(
    files: List[UploadFile] = File(..., description="Upload image or PDF files for structured OCR processing"),
    structuring_prompt: str = Form(None),
    api: APISummary = Depends(verify_structure_access)

):

    combined_texts = []
    processed_types = set()

    for file in files:
        validation = validate_ocr_file(file.filename)
        processed_types.add(validation.get("type"))
        file_bytes = await file.read()

        if validation["type"] == "image":
            raw_text = await run_in_threadpool(ocr_image_bytes, file_bytes)
        else:
            raw_text = await run_in_threadpool(ocr_pdf_bytes, file_bytes)

        cleaned_text = clean_text(raw_text, keep_newlines=True)
        combined_texts.append(cleaned_text)

    full_text = "\n\n".join(combined_texts).strip()

    gpt_response = await run_in_threadpool(
        structure_with_gpt,
        full_text,
        structuring_prompt
    )

    return JSONResponse(content={
        "success": True,
        "valid": True,
        "type": ", ".join(processed_types),
        "data": gpt_response.get("data"),
        "remaining_hits": api.remaining_hits,
        "warning": api.warning
    })

# ---------------- Auth Endpoints ---------------- #

@app.post("/auth/register", status_code=201)
async def register(user: RegisterSchema, db: Session = Depends(get_db)):
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

    return {
        "success": True,
        "message": "User registered successfully",
        "plan": free_plan.name,
        "monthly_limit": free_plan.monthly_hit_limit,
        "api_key": free_api_key,
        "api_issue_date": to_pkt(api_key.created_at),
        "api_end_date": to_pkt(api_key.api_end_date)
    }

@app.post("/auth/login")
async def login(data: LoginSchema, db: Session = Depends(get_db)):
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
    if api_key.last_reset.year != today.year or api_key.last_reset.month != today.month:
        api_key.used_hits = 0
        api_key.last_reset = today
        db.commit()
        db.refresh(api_key)

    token = create_access_token({"user_id": user.user_id})

    return {
        "success": True,
        "message": "You are logged in successfully",
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "user": {"user_id": user.user_id, "email": user.email},
        "api_usage": {
            "monthly_limit": api_key.user.plan.monthly_hit_limit,
            "used_hits": api_key.used_hits,
            "remaining_hits": api_key.remaining_hits,
            "allow_hits": api_key.allow_hits(),
            "warning": api_key.warning,
            "api_key": api_key.api_key,
            "api_issue_date": to_pkt(api_key.created_at),
            "api_end_date": to_pkt(api_key.api_end_date)
        }
    }




# Get the directory where app.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve static files (your HTML, CSS, JS)
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Serve index.html at the root URL
@app.get("/")
async def serve_frontend():
    index_path = os.path.join(BASE_DIR, "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend not found. Please place index.html in static/ folder"}

# Catch-all route for SPA (Single Page Application) behavior
@app.get("/{path:path}")
async def catch_all(path: str):
    # Don't catch API routes
    if path.startswith(("extract-", "auth/", "ocr/", "docs", "openapi.json")):
        raise HTTPException(status_code=404)
    
    # Try to serve index.html for all other routes
    index_path = os.path.join(BASE_DIR, "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    raise HTTPException(status_code=404)