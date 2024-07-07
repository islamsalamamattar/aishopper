from typing import List, Optional
from pydantic import BaseModel

class ChoiceDelta(BaseModel):
    content: str
    function_call: Optional[str]
    role: Optional[str]
    tool_calls: Optional[List[str]]

class Choice(BaseModel):
    delta: ChoiceDelta
    finish_reason: Optional[str]
    index: int
    logprobs: Optional[dict]

class ChatCompletionChunk(BaseModel):
    id: str
    choices: List[Choice]
    created: int
    model: str
    object: str
    system_fingerprint: Optional[str]
