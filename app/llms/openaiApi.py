from dotenv import load_dotenv
import os
import json
import logging
import copy
import openai
from sse_starlette import EventSourceResponse
from typing import List, Dict

# Load environment variables from the .env file
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or "sk-XXXX"
BASE_URL = "https://api.openai.com/v1"

_model = 'gpt-4o-mini' # 'gpt-3.5-turbo', 'gpt-4o', 'gpt-4-turbo'

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
    tools: List[Dict]
):
    """
    Generates a chat response using the OpenAI API with a custom base host URL.

    Args:
    - messages (list): List of messages in the chat conversation. Each message should be a dictionary with 'role' and 'content' keys.
    - model (str, optional): The OpenAI model to use. Defaults to 'gpt-3.5-turbo'.
    - max_tokens (int, optional): Controls the response length. Defaults to 500.
    - temperature (float, optional): Controls the randomness of the response. Defaults to 0.7.
    - top_p (float, optional): Controls the diversity of the response. Defaults to 0.8.
    - stop_phrases (list, optional): List of stop phrases. Defaults to ["User Response:"].
    - stream (bool, optional): Whether to use streaming or not. Defaults to True.

    Returns:
    - async generator: An async generator that yields the full response from the OpenAI Chat API, including information such as 'id', 'object', 'created', 'model', 'usage', and 'choices'.
    """
    # Set your OpenAI API key & API URL
    client = openai.AsyncOpenAI(
        api_key=API_KEY
    )

    # Make the API request and return the full response or yield the response stream
    response = await client.chat.completions.create(
        messages=messages,
        model=model,
        stop=stop,
        stream=stream,
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens,
        tool_choice="auto",
        tools=tools
    )
    print(response)
    return response

async def generate_chat_response_stream(
    messages: list,
    model: str = _model,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    top_p: float = 0.8,
    stop_phrases: list = ["User Response:", "[INST]", "[/INST]", "[SYS]", "[/SYS]", "<<SYS>>"],
):
    """
    Generates a chat response using the OpenAI API with streaming enabled.

    Args:
    - messages (list): List of messages in the chat conversation. Each message should be a dictionary with 'role' and 'content' keys.
    - model (str, optional): The OpenAI model to use. Defaults to 'gpt-3.5-turbo'.
    - max_tokens (int, optional): Controls the response length. Defaults to 500.
    - temperature (float, optional): Controls the randomness of the response. Defaults to 0.7.
    - top_p (float, optional): Controls the diversity of the response. Defaults to 0.8.
    - stop_phrases (list, optional): List of stop phrases. Defaults to ["User Response:"].

    Yields:
    - dict: A dictionary representing a part of the chat response from the OpenAI API, including information such as 'id', 'object', 'created', 'model', 'usage', and 'choices'.
    """
    # Set your OpenAI API key & API URL
    client = openai.OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
    )

    # Prepare the API request parameters for the Chat API
    params = {
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature' : temperature,
        'top_p': top_p,
        'stop': stop_phrases,
        'stream': True,  # Enabling streaming
    }

    try:
        # Make the API request and get the response stream
        response_stream = client.chat.completions.create(**params)

        # Read from the stream
        async def async_generator():
            for item in response_stream:
                yield item
        async def server_sent_events():
            text = ""
            async for item in async_generator():
                result = copy.deepcopy(item)
                if result.choices[0].delta.content == None:
                    pass
                else:
                    text += str(result.choices[0].delta.content)
                yield text
        return EventSourceResponse(server_sent_events())

    # Error handling
    except Exception as e:
        raise Exception(f"Error making API request: {params}")


# Using Ebedding API
def create_embedding(
    text: str,
    model: str = 'text-embedding-ada-002',
    username: str = None,
):
    """
    Generate an embedding using the OpenAI API.

    Args:
    - text (str): The input text for generating the embedding.
    - model (str, optional): ID of the model to use. Defaults to 'text-embedding-ada-002'.
    - username (str, optional): A unique identifier representing your end-user. Defaults to None.

    Returns:
    - list: The embedding vector returned by the OpenAI API.
    """
    # Set your OpenAI API key & API URL
    client = openai.OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
    )
    
    # Replace newline characters with spaces in the input text
    text = text.replace("\n", " ")

    # Make the API request to generate embedding
    response = client.embeddings.create(input=[text], model=model)

    # Check for successful response
    if response.status_code == 200:
        # Extract the embedding vector from the response
        embedding = response.data[0].embedding
        return embedding
    else:
        # Handle unsuccessful response
        logging.error(f"Error making API request: {response}")
        raise Exception(f"Error making API request: {response}")



# Using Completions API
def create_completions(
    prompt: str,
    username: str = "user",
    model: str = 'text-curie-001',
    max_tokens: int = 2000,
    temperature: float = 0.7,
    top_p: float = 0.8,
    stream: bool = True,
    stop: list = ["###Response", "<</SYS>>", "User:", "User Response:"]
):
    """
    Generates a chat response using the OpenAI API with a custom base host URL.

    Args:
    - prompt (str): The input prompt for the chat conversation.
    - username (str, optional): The user's username. Defaults to "user".
    - model (str, optional): The OpenAI model to use. Defaults to 'text-curie-001'.
    - max_tokens (int, optional): Controls the response length. Defaults to 500.
    - temperature (float, optional): Controls the randomness of the response. Defaults to 0.7.
    - top_p (float, optional): Controls the diversity of the response. Defaults to 0.8.
    - stream (bool, optional): Whether to use streaming or not. Defaults to False.
    - stop_phrases (list, optional): List of stop phrases. Defaults to ["###Response", "<</SYS>>", f"{username}: ", "User Response:"].

    Returns:
    - dict: The full response from the OpenAI API, including various information such as 'choices', 'usage', etc.
    
    OR

    Yields:
    - dict: The full response from the OpenAI API, including various information such as 'choices', 'usage', etc.

    Example Output:
    {
    "id": "cmpl-c1774a7e-c414-40d3-bdc8-339e8de96e84",
    "object": "text_completion",
    "created": 1703450314,
    "model": "/models/dolphin-2.1-mistral-7b.Q4_K_M.gguf",
    "choices": [
        {
        "text": "The capital city of France is Paris.",
        "index": 0,
        "logprobs": null,
        "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 22,
        "completion_tokens": 9,
        "total_tokens": 31
    }
    }
    """
    # Set your OpenAI API key & API URL
    client = openai.OpenAI(
        api_key="sk-xxx",
        base_url="http://localhost:8000/v1",
    )

    # Prepare the API request parameters
    params = {
        "model": model,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature" : temperature,
        "top_p": top_p,
        "stream": stream,
        "stop": stop,
    }
    stream=stream

    try:
        # Make the API request and return the full response or yield the response stream
        if stream:
            for response_chunk in client.completions.create(**params):
                yield response_chunk #.choices[0].text
        else:
            response = client.completions.create(**params)
            return response

    except openai.OpenAIError as e:
        # Handle the OpenAIError
        handle_openai_error(e)

def stream_completions(stream):
    """
    Yields tokens from the OpenAI API response stream.

    Args:
    - stream: A generator yielding chunks from the OpenAI API response.

    Yields:
    - str: Tokens from the OpenAI API response.
    """
    buffer = ""

    for chunk in stream:
        # Check if the chunk is a Completion object
        if 'choices' in chunk and chunk:
            # Check if 'text' field is present in the first choice
            if 'text' in chunk.choices[0]:
                tokens = chunk.choices[0].text

                # Check if tokens are not None before yielding
                if tokens is not None:
                    yield tokens
                else:
                    logging.warning("Empty 'text' field in the 'choices' array.")
            else:
                logging.error("Missing 'text' field in the 'choices' array.")
        else:
            logging.error("Missing or empty 'choices' array in the response.")

    if buffer:
        logging.error("Incomplete JSON object at the end of the stream: %s", buffer)
