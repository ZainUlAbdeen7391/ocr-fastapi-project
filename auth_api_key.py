from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from database_config.main import get_db
from database_config.api_usage_table import APISummary
from database_config.users_table import User


def verify_api_key_only(
    x_api_key: str = Header(..., description="Enter your generated API"),
    db: Session = Depends(get_db)
):
    api = (
        db.query(APISummary)
        .join(User, User.user_id == APISummary.user_id)
        .filter(
            APISummary.api_key == x_api_key,
            APISummary.is_active == True
        )
        .first()
    )

    if not api:
        raise HTTPException(status_code=401, detail={
            "success": False,
            "valid": False,
            "message": "Invalid API key"
        })

    if api.is_expired():
        raise HTTPException(status_code=403, detail={
            "success": False,
            "valid": False,
            "message": "API key expired"
        })

    # Monthly reset
    today = date.today()
    if api.last_reset.month != today.month or api.last_reset.year != today.year:
        db.query(APISummary).filter(APISummary.id == api.id).update({
            APISummary.used_hits: 0,
            APISummary.last_reset: today
        })
        db.commit()
        db.refresh(api)

    if not api.allow_hits():
        raise HTTPException(status_code=429, detail={
            "success": False,
            "valid": False,
            "message": "Monthly quota exceeded"
        })

    db.query(APISummary).filter(APISummary.id == api.id)\
        .update({APISummary.used_hits: APISummary.used_hits + 1})

    db.commit()
    db.refresh(api)

    remaining = api.monthly_limit - api.used_hits
    percent = (api.used_hits / api.monthly_limit) * 100

    warning = None
    if percent >= 90:
        warning = f"{remaining} hits remaining"

    return {
        "success": True,
        "valid": True,
        "warning": warning,
        "remaining_hits": remaining,
        "api": api
    }


def verify_structure_access(
    x_api_key: str = Header(..., description="Enter generated key if it allow structure data"),
    db: Session = Depends(get_db)
):

    api = (
        db.query(APISummary)
        .join(User, User.user_id == APISummary.user_id)
        .filter(
            APISummary.api_key == x_api_key,
            APISummary.is_active == True
        )
        .first()
    )

    if not api:
        raise HTTPException(status_code=401, detail={
            "success": False,
            "valid": False,
            "message": "Invalid API key"
        })

    if api.is_expired():
        raise HTTPException(status_code=403, detail={
            "success": False,
            "valid": False,
            "message": "API key expired"
        })

    # Monthly reset
    today = date.today()
    if api.last_reset.month != today.month or api.last_reset.year != today.year:
        db.query(APISummary).filter(APISummary.id == api.id).update({
            APISummary.used_hits: 0,
            APISummary.last_reset: today
        })
        db.commit()
        db.refresh(api)

    # Quota check (IMPORTANT)
    if not api.allow_hits():
        raise HTTPException(status_code=429, detail={
            "success": False,
            "valid": False,
            "message": "Monthly quota exceeded"
        })

    # Plan permission check
    if not api.user.plan.allow_structure:
        raise HTTPException(status_code=405, detail={
            "success": False,
            "valid": False,
            "message": "Your plan does not allow structured OCR"
        })

    return {
        "success": True,
        "valid": True,
        "message": "Access granted",
        "api": api
    }
