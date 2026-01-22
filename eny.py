import os
from dotenv import load_dotenv as _load_dotenv
from pathlib import Path


def load_env():
    env_path = Path(__file__).parent / ".env"
    _load_dotenv(env_path)

    if not os.getenv("GOOGLE_VISION_API_KEY"):
        raise RuntimeError("GOOGLE_VISION_API_KEY missing")

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY missing")
    
    
