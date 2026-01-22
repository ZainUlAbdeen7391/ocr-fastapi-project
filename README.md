📄 OCR API – Image & PDF Text Extraction

A powerful OCR backend built with FastAPI that supports:

📷 Image OCR

📄 PDF OCR (multi-page)

🌍 English, Urdu, and Arabic text

🤖 GPT-based structured data extraction

🚀 Ready for cloud deployment

🚀 Features

Google Vision OCR integration

Image and PDF OCR support

Multi-language support (English, Urdu, Arabic)

GPT-powered structured JSON extraction

Clean and scalable FastAPI architecture

Production-ready APIs

🧠 Tech Stack

Python 3.10+

FastAPI

Google Vision API

OpenAI API

pdf2image

arabic_reshaper

python-bidi

Uvicorn

📁 Project Structure
DEVMINDS OCR PRODUCT/
│
├── app.py
├── ocr_service.py
├── urdu_json.py
├── eny.py
├── .env
├── requirements.txt
└── README.md

🔐 Environment Variables

Create a .env file in the project root:

GOOGLE_VISION_API_KEY=your_google_vision_api_key
OPENAI_API_KEY=your_openai_api_key


⚠️ Do NOT commit .env to GitHub.

📦 Installation
1. Clone the repository
git clone https://github.com/your-username/ocr-project.git
cd ocr-project

2. Create virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

3. Install dependencies
pip install -r requirements.txt

▶️ Run Locally
uvicorn main:app --reload


Application will run at:

http://127.0.0.1:8000


Swagger documentation:

http://127.0.0.1:8000/docs

🔎 API Endpoints
📷 Image OCR
POST /extract-images


Form-data

files: image files (jpg, png, jpeg)


Response

{
  "image1.jpg": "Extracted text"
}

📄 PDF OCR
POST /extract-pdfs


Form-data

files: PDF files


Response

{
  "file.pdf": "Extracted text"
}

🧠 OCR + Structured Data (GPT)
POST /ocr/structure


Form-data

files: image or PDF (multiple allowed)
structuring_prompt: GPT prompt containing {text}


Example Prompt

Extract name, father name, CNIC number, and date of birth from the following text:

{text}

Return ONLY valid JSON.


Response

{
  "raw_ocr_text": "...",
  "structured_output": {
    "name": "Zain Ul Abdeen",
    "father_name": "Abdul Razzaq",
    "date_of_birth": "1998-02-28"
  }
}

📝 Text Processing Rules
Clean OCR Text

Used before sending text to GPT:

clean_text(text)


Removes extra whitespace

Normalizes OCR formatting

Removes invalid symbols

Urdu / Arabic Handling
fix_rtl_text(text)


⚠️ Important:

Use ONLY for UI display or PDF rendering

DO NOT use for JSON, database storage, or GPT input

This ensures Urdu and Arabic remain machine-readable.

🌍 Supported Languages

English

Urdu

Arabic

(Google Vision language hints enabled)

⚠️ Common Issues
Urdu appears reversed?

This is expected in raw OCR output.
Apply fix_rtl_text() only for visual display.

GPT returns invalid JSON?

Always enforce prompt:

Return ONLY valid JSON without markdown or explanation.


Optionally clean the response before parsing.

☁️ Deployment (Free Options)

Recommended platforms:

Render

Railway

Fly.io

Render Start Command
uvicorn main:app --host 0.0.0.0 --port 10000


Add environment variables from the Render dashboard.

🔒 Security Notes

Never expose API keys

Always use environment variables

Validate file types

Limit upload file size

📌 Use Cases

CNIC OCR

Passport OCR

Contract digitization

HR onboarding automation

Document processing systems

AI data extraction pipelines

📈 Future Enhancements

Table extraction

Layout detection

OCR confidence scoring

Language auto-detection

Frontend dashboard

Bulk OCR processing

👨‍💻 Author

Developed by:
Zain Ch
OCR & AI Automation Engineer