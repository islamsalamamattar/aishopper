import json
from typing import List, Dict
#from app.llms.groqApi import create_chat_completions
from app.llms.openaiApi import create_chat_completions

async def llmApiCall(
        messages: str,
        tools: List[Dict],
        model: str, # 'gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4-turbo' # = "llama3-70b-8192",  # "llama3-8b-8192", # "mixtral-8x7b-32768",
        stop: List[str] = ["[USER]", "[/USER]", "[SYS]", "[/SYS]"],
        stream: bool = False,
        temperature: float = 0.7,
        top_p: float = 0.8,
        max_tokens: int = 5000,
):
    params = {
        'messages': messages,
        'model': model,
        'stop': stop,
        'stream': stream,
        'temperature': temperature,
        'top_p': top_p,
        'max_tokens': max_tokens,
        'tools': tools
    }
    response = await create_chat_completions(**params)
    return response
