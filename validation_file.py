import os


ALLOWED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
ALLOWED_DOCUMENT_FORMATS = {".pdf"}

def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename.lower())[1]
def validate_ocr_file(filename: str) -> dict:
    ext = get_file_extension(filename)  
    file_type = ext.replace(".", "") if ext else "unknown"

    if ext in ALLOWED_IMAGE_FORMATS:
        return {
            "success": True,
            "valid": True,
            "type": "image",
            "message": "Valid image format",
            "allowed_image_formats": sorted(ALLOWED_IMAGE_FORMATS)
            
        }

    if ext in ALLOWED_DOCUMENT_FORMATS:
        return {
            "success": True,
            "valid": True,
            "type": "pdf",
            "message": "Valid PDF format",
            "allowed_document_formats": sorted(ALLOWED_DOCUMENT_FORMATS)
        }

    return {
        "success": False,
        "valid": False,
        "type": file_type,  
        "message": "Unsupported file format",
        "allowed_image_formats": sorted(ALLOWED_IMAGE_FORMATS),
        "allowed_document_formats": sorted(ALLOWED_DOCUMENT_FORMATS)
    }



