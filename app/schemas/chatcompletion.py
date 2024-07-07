from typing import List, Optional, Dict
from pydantic import BaseModel

class Message(BaseModel):
    content: str
    role: str

class MessageResponse(BaseModel):
    content: str
    role: str
    function_call: Optional[str]
    tool_calls: Optional[List[str]]

class Choice(BaseModel):
    finish_reason: str
    index: int
    logprobs: Optional[dict]
    message: Message

class Usage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: str
    temperature: float = 0.5
    max_tokens: int = 1024
    top_p: float = 1
    stop: Optional[str] = ["User Response:", "[USER]", "[/USER]", "[INST]", "[/INST]", "[SYS]", "[/SYS]", "<<SYS>>"]
    stream: bool = False

class ChatCompletionResponse(BaseModel):
    id: str
    choices: List[Choice]
    created: int
    model: str
    object: str
    system_fingerprint: Optional[str]
    usage: Usage
