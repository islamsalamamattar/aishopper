from pydantic import BaseModel

class ChatRequest(BaseModel):
    token: str
    session_id: str
    message: str