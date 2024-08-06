from typing import List, Tuple
from datetime import datetime

# Register current date and time, ready to be included in the prompt
now = datetime.now()
date_time = now.strftime("%Y-%m-%d__%H:%M")

# Function to format the prompt for "completions" api call
def CompletionsPrompt(
        chat_history: List[Tuple[str, str]],
        username: str = "user",
        assistant_name: str = "assistant",
        system_prompt: str = "You are a helpful assistant named {assistant_name}.",
        frugal: bool = False,
) -> str:
    """
    Generate a template prompt based on the chat history.

    Args:
        - chat_history (List[Tuple[str, str]]): List of chat history tuples containing user messages and assistant responses.
        - username (str, optional): The user's name. Defaults to "user".
        - assistant_name (str, optional): The assistant's name. Defaults to "assistant".
        - system_prompt (str, optional): The initial system prompt. Defaults to "You are a helpful assistant named {assistant_name}".
        - frugal (bool, optional): If True, include only the last 5 messages in the prompt. Defaults to False.

    Returns:
        - str: The generated template prompt.
    """
    prompt = system_prompt

    if frugal:
        if len(chat_history) < 5:
            # Iterate and add conversation history to the messages
            for message, response in chat_history:
                if message:
                    chat = f"\n{username}: {message}"
                    prompt += chat
                if response:
                    reply = f"\n{assistant_name}: {response}"
                    prompt += reply
        else:
            # Iterate and add the last 5 messages of the conversation history to the prompt
            for message, response in chat_history[-5:-1]:
                if message:
                    chat = f"\n{username}: {message}"
                    prompt += chat
                if response:
                    reply = f"\n{assistant_name}: {response}"
                    prompt += reply
    else:
        # Iterate and add the entire conversation history to the prompt
        for message, response in chat_history[:-1]:
            if message:
                chat = f"\n{username}: {message}"
                prompt += chat
            if response:
                reply = f"\n{assistant_name}: {response}"
                prompt += reply
    last_prompt = chat_history[-1][0]
    prompt += f"🕒 *Current Date/Time:* {date_time}\n\n{username}: {last_prompt}\n{assistant_name}: "

    return prompt

# Function to format the prompt for "chat completions" api call
def ChatCompletionsPrompt(
        chat_history: List[Tuple[str, str]],
        username: str = "user",
        assistant_name: str = "assistant",
        system_prompt: str = "You are a helpful assistant named {assistant_name}.",
        frugal: bool = False,
) -> str:
    """
    Generate a template prompt for chat completions based on the chat history.

    Args:
        - chat_history (List[Tuple[str, str]]): List of chat history tuples containing user messages and assistant responses.
        - username (str, optional): The user's name. Defaults to "user".
        - assistant_name (str, optional): The assistant's name. Defaults to "assistant".
        - system_prompt (str, optional): The initial system prompt. Defaults to "You are a helpful assistant named {assistant_name}".
        - frugal (bool, optional): If True, include only the last 5 messages in the prompt. Defaults to False.

    Returns:
        - List[Dict[str, str]]: List of message dictionaries for the chat completions API.
    """
    # Initialize messages list with the system prompt
    messages = [{'role': 'system', 'content': system_prompt}]

    if frugal:
        if len(chat_history) < 5:
            # Iterate and add conversation history to the messages
            for user, assistant in chat_history:
                message = [
                    {'role': 'user', 'content': user},
                    {'role': 'assistant', 'content': assistant}
                ]
                messages.extend(message)

            return messages
        else:
            # Iterate and add the last 5 messages of the conversation history to the messages
            for user, assistant in chat_history[-5:]:
                message = [
                    {'role': 'user', 'content': user},
                    {'role': 'assistant', 'content': assistant}
                ]
                messages.extend(message)

            return messages
    else:
        # Iterate and add the entire conversation history to the messages
        for user, assistant in chat_history:
            message = [
                {'role': 'user', 'content': user},
                {'role': 'assistant', 'content': assistant}
            ]
            messages.extend(message)

        return messages

# Function to format session messages in a prompt for "completions" api call    
def SessionSummaryPrompt(
        messages: List[str],
        summarize_prompt: str,
        datetime: datetime,
        username: str = 'user',
        assistant_name: str = 'assistant',
) -> str:
    """
    Generate a template prompt for summarizing a chat session.

    Args:
        - messages (List[str]): List of messages from the chat session.
        - summarize_prompt (str): The initial prompt for summarizing the session.
        - datetime (datetime): The date and time of the session.
        - username (str, optional): The user's name. Defaults to 'user'.
        - assistant_name (str, optional): The assistant's name. Defaults to 'assistant'.

    Returns:
        - str: The generated template prompt for summarizing the session.
    """
    prompt = summarize_prompt + f"\nUser: {username} \nSession: \nDateTime: {datetime}"
    for message in messages:
        prompt += f"\n{username}: {message.prompt}"
        prompt += f"\n{assistant_name}: {message.response}"
    return prompt
