from pydantic import BaseModel, EmailStr, field_validator
import re


class RegisterSchema(BaseModel):
    full_name: str
    email: EmailStr
    password: str

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("Full name must not be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):

        if not v or not v.strip():
            raise ValueError("Password must not be empty")



        pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$"

        if not re.match(pattern, v):
            raise ValueError(
                "Password must be at least 8 characters and contain letters, numbers, and special characters"
            )

        return v


class LoginSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_login_password(cls, v):
        if not v or not v.strip():
            raise ValueError("Password must not be empty")
        return v
