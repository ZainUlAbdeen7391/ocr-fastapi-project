import os
import json
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
def extract_requested_fields(user_prompt: str) -> list[str] | None:

    system_prompt = """
You are an OCR Intent Detection Agent.

Your job is to understand what fields the user wants to extract from a document.

Rules:
- If the user asks for specific fields, return ONLY those fields.
- If the user asks to extract all information, return null.
- If the user prompt is irrelevant to OCR extraction, return "invalid".

Examples:

"extract name" → ["name"]
"get father name and id number" → ["father_name", "id_number"]
"read passport details" → null
"extract all data" → null
"summarize document" → "invalid"
"translate text" → "invalid"

Return ONLY valid JSON:

{
  "fields": ["field1", "field2"] | null | "invalid"
}

No explanation.
No markdown.
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    )

    try:
        parsed = json.loads(response.choices[0].message.content)
        return parsed.get("fields")
    except:
        return "invalid"



DEFAULT_OCR_STRUCTURING_PROMPT = """
You are an intelligent OCR-based document data extraction system.

Your task is to extract ALL meaningful structured information found in the OCR text.

Rules:
- Use ONLY the information explicitly present in the OCR text.
- Do NOT guess, infer, assume, or generate missing values.
- If a value is unclear or not present, return null.
- Preserve original wording of field names where possible.
- Normalize dates to ISO format (YYYY-MM-DD) when clearly identifiable.
- Normalize numbers by removing commas and symbols when applicable.
- Do NOT add information that does not exist in the OCR text.
- Do NOT include explanations, markdown, or comments.
- Return ONLY valid JSON.

Extraction Instructions:

1. Identify document type if clearly mentioned (e.g., ID Card, Passport, Invoice).
2. Extract all personal, identification, and document-related fields such as:
   - name
   - father_name
   - mother_name
   - date_of_birth
   - date_of_issue
   - date_of_expiry
   - id_number
   - passport_number
   - nationality
   - gender
   - address (current or permanent if stated)
   - any other clearly labeled fields

3. Extract financial fields if present:
   - total_amount
   - tax
   - currency
   - invoice_number
   - reference_number

4. Extract tabular or repeated data as arrays when detected.

Output format:

{
  "document_type": "",
  "fields": {
    "<field_name>": "<value or null>"
  },
  "line_items": [
    {
      "description": "",
      "quantity": "",
      "unit_price": "",
      "total": ""
    }
  ]
}

Only include line_items if they exist.

OCR TEXT:
{text}
"""
def build_structuring_prompt(ocr_text: str, requested_fields):
    if requested_fields is None:
        return DEFAULT_OCR_STRUCTURING_PROMPT.replace("{text}", ocr_text)

    fields_schema = ",\n".join(
        [f'"{field}": null' for field in requested_fields]
    )

    return f"""
You are an OCR-based structured data extraction engine.

Rules:
- Extract ONLY the fields listed below.
- Do NOT extract extra information.
- Use ONLY OCR text.
- Do NOT guess values.
- If field not found, return null.
- Return ONLY valid JSON.

Fields to extract:
{", ".join(requested_fields)}

Output JSON:

{{
  "fields": {{
    {fields_schema}
  }}
}}

OCR TEXT:
{ocr_text}
"""
def structure_with_gpt(ocr_text: str, user_prompt: str | None):

    if not user_prompt or not user_prompt.strip():
        final_prompt = DEFAULT_OCR_STRUCTURING_PROMPT.replace("{text}", ocr_text)

    else:
        intent = extract_requested_fields(user_prompt)

        if intent == "invalid":
            return {
                "success": False,
                "valid": False,
                "message": "Invalid prompt. This prompt is not relevant for OCR extraction."
            }

        final_prompt = build_structuring_prompt(ocr_text, intent)

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a professional OCR document data extraction engine."
            },
            {
                "role": "user",
                "content": final_prompt
            }
        ],
    )

    try:
        return {
            "success": True,
            "valid": True,
            "data": json.loads(response.choices[0].message.content)
        }
    except:
        return {
            "success": False,
            "valid": False,
            "message": "Invalid json. This prompt is not relevant for structured OCR Extraction"
        }
        
        

