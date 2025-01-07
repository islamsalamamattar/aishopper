import logging
import sys
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Interaction, User, Chatsession, Product
from app.utils.scrapers.scrapingfish import amazon_search, amazon_products_details, noon_search
from app.llms.inferenceCall import llmApiCall
from app.agents.chatAgent.tools import available_tools
from app.agents.chatAgent.prompts import newMessagePrompt


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


class DatabaseManager:
    """
    Handles all database-related operations.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_session_by_id(self, session_id: str):
        return await Chatsession.find_by_id(self.db, session_id)

    async def find_user_by_id(self, user_id: str):
        return await User.find_by_id(self.db, user_id)

    async def find_products_by_asin(self, asin: str):
        return await Product.find_by_asin(self.db, asin)

    async def save_product(self, product_data: dict):
        await Product.create(self.db, **product_data)

    async def update_session_title(self, session_id: str, title: str):
        await Chatsession.update_title(self.db, session_id, title)

    async def create_interaction(self, interaction_data: dict):
        return await Interaction.create(self.db, **interaction_data)


class ProductService:
    """
    Manages product-related operations including search and save products.
    """

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
        
    @staticmethod
    async def save_products(db_manager: DatabaseManager, products: list):
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
            existing_product = await db_manager.find_products_by_asin(product["asin"])
            if not existing_product:
                await db_manager.save_product(result)


class InteractionManager:
    """
    Manages interactions, including loading history and saving interactions.
    """
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def load_session_history(self, state: ConversationState):
        history = await Interaction.find_by_session_id(db=self.db_manager.db, session_id=state.session_id)
        for interaction in history:
            state.messages.append({'role': 'user', 'content': interaction.prompt})
            state.history.append((interaction.prompt, interaction.response))

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

            if interaction.response:
                state.messages.append({'role': 'assistant', 'content': interaction.response})

        return state

    async def save_interaction(self, state: ConversationState, next_step: str):
        reply = ""
        if state.history and len(state.history[-1]) > 1:
            reply = state.history[-1][1]

        interaction_data = {
            "session_id": state.session_id,
            "model": llm_model,
            "prompt": state.history[-1][0],
            "tool_calls": state.tool_calls,
            "search_keywords": state.search_keywords,
            "amazon_products": state.amazon_products,
            "noon_products": state.noon_products,
            "added_to_cart": state.added_to_cart,
            "response": reply,
            "next": next_step,
            "prompt_tokens": state.usage[0],
            "completion_tokens": state.usage[1],
            "total_tokens": state.usage[0] + state.usage[1],
        }
        interaction = await self.db_manager.create_interaction(interaction_data)
        state.interaction_id = interaction.id
        logger.info(f"INTERACTION SAVED:{interaction.id}")
        return state


async def fetch_llm_response(messages: list, model: str, tools: list):
    response = await llmApiCall(
        model=model,
        messages=messages,
        tools=tools,
    )
    return response


class Formatter:
    """
    Formats messages and states for interactions with the app or LLM.
    """
    @staticmethod
    def add_new_message_to_state(message: str, state: ConversationState):
        formatted_message = {'role': 'user', 'content': message}
        state.messages.append(formatted_message)
        state.history.append([message])
        return state

    @staticmethod
    def add_tool_call_to_state(state, tool_call, response):
        state.tool_calls = {
            'id': tool_call.id,
            'name': tool_call.function.name,
            'arguments': json.loads(tool_call.function.arguments),
            'response': response,
        }
        return state

    @staticmethod
    def format_state_for_app(state: ConversationState):
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
        return interaction


async def MessageChain(db: AsyncSession, session_id: str, message: str):
    """
    Handles the message chain, managing state, interactions, tool calls, and responses.

    Args:
        db: AsyncSession for database operations.
        session_id: The current session's ID.
        message: The message sent by the user.

    Returns:
        A formatted response for the app.
    """
    # Initialize database manager and state
    db_manager = DatabaseManager(db)
    state = ConversationState(db, session_id)
    await state._initialize()

    # Initialize InteractionManager
    interaction_manager = InteractionManager(db_manager)

    # Load session history
    state = await interaction_manager.load_session_history(state)

    # Add the user's new message to the state
    if message:
        state = Formatter.add_new_message_to_state(message, state)


    # Initialize the messages list with a system message
    state.messages = [{'role': 'system', 'content': newMessagePrompt}] + state.messages
    # Fetch response from the LLM
    response = await fetch_llm_response(
        model=llm_model,
        messages=state.messages,
        tools=available_tools
    )

    # Parse the LLM response
    tool_calls = response.choices[0].message.tool_calls
    reply = response.choices[0].message.content
    state.usage = (response.usage.prompt_tokens, response.usage.completion_tokens)

    # Add the assistant's reply to the state history
    if reply:
        state.history[-1].append(reply)

    # If there are no tool calls, save interaction and return formatted response
    if not tool_calls:
        state = await interaction_manager.save_interaction(state, "top_picks")
        return Formatter.format_state_for_app(state)


    # Extract the first tool call for processing
    tool_call = tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = json.loads(tool_call.function.arguments)

    # Handle "search_products" tool call
    if tool_name == "search_products":
        try:
            # Update session name with keywords
            session = await db_manager.find_session_by_id(session_id)
            if session.title == "New Session":
                state.search_keywords = tool_args['keywords']
                new_title = (" ".join(tool_args['keywords'])[:20] + " ...") if len(" ".join(tool_args['keywords'])) > 20 else " ".join(tool_args['keywords'])
                await db_manager.update_session_title(session_id, new_title)

            # Search Amazon and Noon for products
            state = await ProductService.search_products(tool_args, state)

            # Save products to the database
            new_products = state.amazon_products + state.noon_products
            await ProductService.save_products(db_manager, new_products)

            # Add tool calls to the state
            state = Formatter.add_tool_call_to_state(state, tool_call, new_products)

            # Save the interaction
            state = await interaction_manager.save_interaction(state, "top_picks")

            # Format and return the response for the app
            return Formatter.format_state_for_app(state)

        except Exception as e:
            logger.error(f"Error during 'search_products' tool call: {e}", exc_info=True)
            # Format and return a fallback response
            return Formatter.format_state_for_app(state)

    # Handle other tool calls (if necessary)
    # Example: Add additional tool call handlers here as needed

    # If no recognized tool call was found, save interaction and return the state
    state = await interaction_manager.save_interaction(state, "unknown_tool_call")
    return Formatter.format_state_for_app(state)


