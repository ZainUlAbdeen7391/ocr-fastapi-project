from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database_config.api_key_table import APIKey
from database_config.main import get_db
from routers.auth_api_key import get_current_user
import secrets
from schema.api_key import APIKeyResponseSchema

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

@router.post("/create", response_model=APIKeyResponseSchema)
def create_api_key(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    key = secrets.token_urlsafe(32)

    api_key_obj = APIKey(
        user_id=current_user.id,
        api_key=key
    )
    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    return api_key_obj


