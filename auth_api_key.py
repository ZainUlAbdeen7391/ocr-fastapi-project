from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from database_config.main import get_db
from database_config.api_usage_table import APISummary


def verify_api_key(
    x_api_key: str = Header(...),
    db: Session = Depends(get_db)
):

    api = db.query(APISummary).filter(
        APISummary.api_key == x_api_key,
        APISummary.is_active == True
    ).first()

    if not api:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Expiry check
    if api.api_end_date and api.api_end_date < api.created_at:
        raise HTTPException(status_code=403, detail="API key expired")

    # Monthly reset
    today = date.today()
    if api.last_reset.month != today.month:
        api.used_hits = 0
        api.last_reset = today
        db.commit()

    if not api.allow_hits():
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")

    api.used_hits += 1
    db.commit()

    return api
