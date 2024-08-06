from pydantic import BaseModel

class NewSessionRequest(BaseModel):
    token: str
    title: str
