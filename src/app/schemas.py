from pydantic import BaseModel
from typing import Optional

class NewAccountVerification(BaseModel):
    email: str
    api_key: str
    secret_key: Optional[str] = None