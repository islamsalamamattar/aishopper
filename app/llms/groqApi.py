from dotenv import load_dotenv
import os
import logging
from typing import List, Any

from groq import AsyncGroq
from app.schemas.chatcompletion import ChatCompletionResponse, ChatCompletionRequest


# Load environment variables from the .env file
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or "sk-XXXX"

# Setup Error handling
class OpenAIError(Exception):
    pass

def handle_openai_error(e):
    logging.error(f"OpenAI API Error: {e}")
    raise OpenAIError(f"OpenAI API Error: {e}")

# Using Chat Completions API
async def create_chat_completions(
        messages: List[str],
        model: str, # = "mixtral-8x7b-32768"
        stop: List[str], # = ["<</SYS>>", "User:"],
        stream: bool, # = False,
        temperature: float, # = 0.7,
        top_p: float, # = 0.8,
        max_tokens: int, # = 2000,
):
    # Set your OpenAI API key & API URL
    client = AsyncGroq(
        api_key=GROQ_API_KEY
    )
        # Make the API request and return the full response
    response = await client.chat.completions.create(
        messages=messages,
        model=model,
        stop=stop,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
    )
    print(response)
    return response
"""
    try:
        # Make the API request and return the full response
        response = await client.chat.completions.create(
            messages=messages,
            model=model,
            stop=stop,
            stream=stream,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
        )
        print(response)
        return response
    except:
        # Error handling
        raise Exception(f"Error making API request")
"""