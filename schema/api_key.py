from pydantic import BaseModel

class APIKeyCreateSchema(BaseModel):
    pass

class APIKeyResponseSchema(BaseModel):
    api_key: str
    created_at: str

    class Config:
        from_attributes = True
