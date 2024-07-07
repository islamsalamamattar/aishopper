from pydantic import BaseModel
from typing import List


class Message(BaseModel):
    role: str
    content: str

class Messages(BaseModel):
    messages: List[Message]

class Prompt(BaseModel):
    messages: Messages
    model: str = 'mixtral-8x7b-32768'
    max_tokens: int = 1000
    temperature: float = 0.4
    top_p: float = 0.85
    stop_phrases: List[str] = [
        "User Response:", "[USER]", "[/USER]", "[INST]", "[/INST]", "[SYS]", "[/SYS]", "<<SYS>>"
    ]
    stream: bool = False