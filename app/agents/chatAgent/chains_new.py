import json
import uuid
import logging
import sys
from typing import Optional
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.llms.inferenceCall import llmApiCall
from app.agents.chatAgent.prompts import newMessagePrompt, topPicksPrompt
from app.agents.chatAgent.tools import available_tools
from app.models import Interaction, User, Chatsession, Product

from app.utils.scrapers.scrapingfish import amazon_search, amazon_products_details, noon_search
#from app.utils.scrapers.scraperapi import amazon_search, amazon_products_details
from app.utils.productUtils import display_products, add_to_cart, create_products


# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Adjust the level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Logs to stdout (captured by systemd)
        logging.FileHandler('/home/admin/arobah/arobah_api/logger.log'),  # Optional file logging
    ]
)

logger = logging.getLogger(__name__)

llm_model = "gpt-4o-mini"  # "llama-3.1-405b-reasoning", "llama3-groq-8b-8192-tool-use-preview", "llama3-groq-70b-8192-tool-use-preview", "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gpt-4o-mini"

class ConversationState:
    """
    Maintains the state of the conversation and related interactions.
    The state is linked to a specific session in the database.
    """

    def __init__(self, db: AsyncSession, session_id: str):
        self.db: AsyncSession = db
        self.session_id: str = session_id
        self.history: list[list] = []
        self.messages: list[str] = []
        self.search_keywords: list[str] = []
        self.tool_calls: list[dict] = []
        self.amazon_products: list[dict] = []
        self.noon_products: list[dict] = []
        self.added_to_cart: list[dict] = []
        self.usage: list = []
        self.interaction_id: str = ""
        self.user_id: str = ""  # Set to empty string initially
        self.country: str = ""  # Set to empty string initially
        self._initialize()

    async def _initialize(self):
        """
        Asynchronously initializes the user_id and country by loading them from the database.
        Raises an error if the session or user does not exist.
        """
        logger.info(f"Initializing ConversationState for session_id: {self.session_id}")
        try:
            logger.debug(f"Attempting to find session with session_id: {self.session_id}")
            session = await Chatsession.find_by_id(self.db, self.session_id)
            if not session:
                logger.error(f"No session found for session_id: {self.session_id}")
                raise ValueError(f"No session found for session_id: {self.session_id}")
            
            self.user_id = session.user_id
            logger.debug(f"Found session. user_id: {self.user_id}")
            
            logger.debug(f"Attempting to find user with user_id: {self.user_id}")
            user = await User.find_by_id(self.db, self.user_id)
            if not user:
                logger.error(f"No user found for user_id: {self.user_id}")
                raise ValueError(f"No user found for user_id: {self.user_id}")
            
            self.country = user.country
            logger.info(f"Successfully initialized ConversationState for user_id: {self.user_id}, country: {self.country}")
        except ValueError as ve:
            logger.warning(f"Validation error during initialization for session_id {self.session_id}: {ve}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during initialization for session_id {self.session_id}: {e}", exc_info=True)
            raise

async def load_session_history(state: ConversationState):
    """
    Loads the session's interaction history and updates the state with the conversation history.
    The history includes user prompts, tool calls, and assistant responses.

    Args:
        state (ConversationState): The current conversation state object which holds session information.

    Returns:
        ConversationState: The updated state with the loaded interaction history.
    """

    
    # Fetch the interaction history for the given session using the session_id from the state
    history = await Interaction.find_by_session_id(db=state.db, session_id=state.session_id)
    for interaction in history:
        # Add the user prompt to the messages list
        state.messages.append({'role': 'user', 'content': interaction.prompt})
        state.history.append((interaction.prompt, interaction.response))
        
        # Add tool call details to the messages list, if any
        for tool_call in interaction.tool_calls:
            state.messages.extend([
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "id": tool_call['id'],
                            "function": {
                                "name": tool_call['name'],
                                "arguments": str(tool_call['arguments']),
                            },
                            "type": "function",
                        }
                    ],
                },
                {
                    "role": "tool",
                    "content": str(tool_call['response']),
                    "tool_call_id": tool_call['id'],
                }
            ])
        
        # Add the assistant's response to the messages list, if any
        if interaction.response:
            state.messages.append({'role': 'assistant', 'content': interaction.response})

    # Update the state object with the loaded messages history
    # state.messages = messages

    # Return the updated state containing the loaded history
    return state

def add_new_message_to_state(message: str, state: ConversationState):
    """
    Adds a new user message to the state and formats it according to the conversation history structure.
    
    Args:
        message (str): The content of the new message from the user.
        state (ConversationState): The current conversation state object which holds the session's messages.

    Returns:
        ConversationState: The updated state with the newly added message.
    """
    # Format the new message with the 'user' role
    formatted_message = {'role': 'user', 'content': message}
    
    # Append the formatted message to the state's prompt and messages list
    state.messages.append(formatted_message)
    state.history.append([message])
    
    # Return the updated state
    return state

async def fetch_llm_response(messages: list, model: str, tools: list):
    response = await llmApiCall(
        model=model,
        messages=messages,
        tools=tools,
    )
    return response

def add_tool_calls_to_state(state: ConversationState, tool_calls: dict):
    formatted_tool_calls = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": tool_call.id,
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
                "type": tool_call.type,
            }
            for tool_call in tool_calls
        ],
    }
    state.messages.append(formatted_tool_calls)
    return state

async def save_products(db: AsyncSession, products: list):
    for product in products:
        result = {
            "platform": product['platform'],
            "country": product['country'],
            "asin": product['asin'],
            "name": product['name'],
            "images": product['images'],
            "price_symbol": product['currency'],
            "price": product['price'],
            "rating": product['rating']
        }
        saved_product = await Product.find_by_asin(db, product["asin"])
        if not saved_product:
            await Product.create(db=db, **result)
        else:
            await Product.patch(db=db, **result)

async def save_interaction(db: AsyncSession, state: ConversationState, next):
    """
    Finalizes the interaction by storing it in the database and returning the results.
    """
    # Safely extract the message from state.history
    reply = ""
    if state.history and len(state.history[-1]) > 1:
        reply = state.history[-1][1]    # Create the interaction entry in the database
    _interaction = await Interaction.create(
        db=db,
        session_id=state.session_id,
        model=llm_model,
        prompt=state.history[-1][0],
        tool_calls=state.tool_calls,
        search_keywords=state.search_keywords,
        amazon_products=state.amazon_products,
        noon_products=state.noon_products,
        added_to_cart=state.added_to_cart,
        response=reply,
        next=next,
        prompt_tokens=state.usage[0],
        completion_tokens=state.usage[1],
        total_tokens=state.usage[0] + state.usage[1],
    )
    state.interaction_id = _interaction.id
    # Return the final response data
    return state

async def format_state_for_app(state: ConversationState):
    logger.info(f"FORMAT STATE INPUTS: state.interaction_id {state.interaction_id}\nstate.amazon_products {state.amazon_products}\nstate.history[-1][1]{state.history[-1][-1]}")
   
    # Safely extract the message from state.history
    reply = ""
    if state.history and len(state.history[-1]) > 1:
        reply = state.history[-1][1]
    
    interaction = {
        "interactionId": state.interaction_id,
        "amazonProducts": state.amazon_products,
        "noonProducts": state.noon_products,
        "message": reply,
        "next": True
    }
    logger.info(f"APP REPLY: {interaction}")
    return interaction

async def search_products(tool_args: dict, state: ConversationState):
    """
    Searches for products from Amazon and Noon in parallel and updates the state.

    Args:
        tool_call: The tool call containing necessary information for the search.
        tool_args: Arguments required to perform the search (e.g., search query, filters).
        state: The current conversation state object containing country and product lists.

    Returns:
        state: Updated state with product lists fetched from Amazon and Noon.
    """
    try:
        # Run both Amazon and Noon searches in parallel
        results = await asyncio.gather(
            amazon_search(country=state.country, **tool_args),
            noon_search(country=state.country, **tool_args),
            return_exceptions=True
        )

        # Process results and update the state
        amazon_result, noon_result = results

        if isinstance(amazon_result, Exception):
            # Log the error for Amazon search
            logger.error(f"Amazon search failed: {amazon_result}", exc_info=True)
        else:
            # Update the state with products from Amazon
            state.amazon_products.extend(amazon_result)

        if isinstance(noon_result, Exception):
            # Log the error for Noon search
            logger.error(f"Noon search failed: {noon_result}", exc_info=True)
        else:
            # Update the state with products from Noon
            state.noon_products.extend(noon_result)
        # Return the updated state
        return state
    except Exception as e:
        # Log any unforeseen errors
        logger.error(f"Unexpected error occurred during product search: {e}", exc_info=True)
        return state

async def formatAppState(response: dict):
    messages = []

    if response.amazon_products:
        products = {
                    "type": "amazonProducts",
                    "id": uuid.uuid4(),
                    "interaction_id": response['interactionId'],
                    "role": "assistant",
                    "createdAt": int(datetime.now().timestamp() * 1000),
                    "products": response['amazonProducts'],
                }
        messages.append(products)

    if response.noon_products:
        products = {
                    "type": "noonProducts",
                    "id": uuid.uuid4(),
                    "interaction_id": response['interactionId'],
                    "role": "assistant",
                    "createdAt": int(datetime.now().timestamp() * 1000),
                    "products": response['noonProducts'],
                }
        messages.append(products)
    
    if response.messages:
        message = {
            "type": "text",
            "id": uuid.uuid4(),
            "interaction_id": response['interactionId'],
            "role": "assistant",
            "createdAt": int(datetime.now().timestamp() * 1000),
            "text": response['message']
        }
        messages.append(message)
        
    return messages


async def MesssageChain(
        db: AsyncSession,
        session_id: str,
        message: str
):
    # Initiate Converstatoin state
    state = ConversationState(db, session_id)
    await state._initialize()

    # Load session history
    state = await load_session_history(state)
    # Load user message
    if message:
        state = add_new_message_to_state(message, state)   

    # Initialize the messages list with a system message
    state.messages = [{'role': 'system', 'content': newMessagePrompt}] + state.messages
    # Fetch LLM response for state.messages
    response = await fetch_llm_response(
        model=llm_model,
        messages=state.messages,
        tools=available_tools,
    )
    tool_calls = response.choices[0].message.tool_calls
    reply = response.choices[0].message.content
    logger.info(f"TOOL CALL FROM LLM: {tool_calls}\nREPLY: {reply}")
    usage = response.usage
    state.usage = (usage.prompt_tokens, usage.completion_tokens)
    if reply:
        state.history[-1].append(reply)

    if not tool_calls:
        # Save interaction to DB
        state = await save_interaction(db, state, "top_picks")
        app_response = await format_state_for_app(state)
        return app_response
    
    # Add tool calls to state messages
    state = add_tool_calls_to_state(state, tool_calls)

    # Extract first tool call data
    tool_call  = tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    # __________SEARCH PRODUCTS - TOOL CALL__________
    if tool_name == "search_products":
        try:
            # Update session name with keywords
            _session = await Chatsession.find_by_id(db, session_id)
            if _session.title == "New Session":
                state.search_keywords = tool_args['keywords']
                new_title = (" ".join(tool_args['keywords'])[:20] + " ...") if len(" ".join(tool_args['keywords'])) > 20 else " ".join(tool_args['keywords'])
                await Chatsession.update_title(db, session_id, new_title)
            
            # search Amazon and Noon for products
            state = await search_products(tool_args, state)
            # Save products to DB
            new_products = state.amazon_products + state.noon_products
            await save_products(db, new_products)

            # Save interaction to DB
            state = await save_interaction(db, state, "top_picks")

            # Format response for app api response
            app_response = await format_state_for_app(state)
            return app_response  
        except:
            logger.info(f"SEARCH FAILED {tool_args}")
            # Format response for app api response
            app_response = await format_state_for_app(state)
            return app_response 



# NOT USED
def format_results(products, platform):
    """
    Formats the search results for better presentation.
    """
    formatted = f"## {platform} Search Results:\n"
    for product in products:
        formatted += f"Title: {product['name']}, Price: {product['price']}\n"
    return formatted


# NOT USED
def format_products_for_llm(products: dict):
    """
    Formats the search results for better presentation.
    """
    formatted = "## Search Results:\n"
    for product in products:
        formatted += f"Title: {product['name']}, Price: {product['price']}\n"
    return formatted
# NOT USED
def unknown_tool(tool_call):
        response = f"Tool {tool_call.function.name} not found"
        return response
# NOT USED
async def handle_tool_call(db, tool_call, state):
    """
    Routes tool calls to the appropriate handler.
    """
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    user = state.user_id
    country = state.country

    handlers = {
        "search_products": search_products,
        "display_products": display_products,
        "get_product_details": amazon_products_details,
        "add_to_cart": add_to_cart,
    }

    if tool_name in handlers:
        return await handlers[tool_name](tool_args)
    else:
        return unknown_tool(tool_call)
