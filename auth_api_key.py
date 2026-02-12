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

    # ---------------- MONTHLY RESET ---------------- #
    today = date.today()
    if api.last_reset.month != today.month or api.last_reset.year != today.year:
        api.used_hits = 0
        api.last_reset = today
        db.commit()
        db.refresh(api)

    # ---------------- QUOTA CHECK ---------------- #
    if not api.allow_hits():
        raise HTTPException(status_code=429, detail={
            "success": False,
            "valid": False,
            "message": "Monthly quota exceeded"
        })

    # ---------------- INCREMENT HITS ---------------- #
    api.used_hits += 1
    db.commit()
    db.refresh(api)
    remaining = api.remaining_hits

    warning = None

    if remaining == 3:
        warning = ("You are approaching your allocated monthly request quota."
                   "You currently have 3 remaining requests available for this billing cycle.")

    elif remaining == 2:
        warning = ("Your account has nearly reached its monthly request limit."
                   "Only 2 requests remain before the quota resets.")

    elif remaining == 1:
        warning = (
            "This is your last request for this month. "
            "Consider upgrading to Pro for uninterrupted access."
        )
        

    elif remaining <= 0:
        raise HTTPException(
            status_code=429,
            detail="You’ve reached your monthly quota. Kindly upgrade to Pro."
        )

    return {
        "api": api,
        "warning": warning
    }


def verify_structure_access(
    x_api_key: str = Header(..., description="Enter generated key if it allows structured data"),
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

    # ---------------- MONTHLY RESET ---------------- #
    today = date.today()
    if api.last_reset.month != today.month or api.last_reset.year != today.year:
        api.used_hits = 0
        api.last_reset = today
        db.commit()
        db.refresh(api)

    # ---------------- QUOTA CHECK ---------------- #
    if not api.allow_hits():
        raise HTTPException(status_code=429, detail={
            "success": False,
            "valid": False,
            "message": "Monthly quota exceeded"
        })

    # ---------------- PLAN PERMISSION ---------------- #
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



