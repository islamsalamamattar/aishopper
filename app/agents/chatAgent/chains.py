import json
import random
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundException
from app.llms.inferenceCall import llmApiCall
from app.agents.chatAgent.prompts import newMessagePrompt, topPicksPrompt
from app.agents.chatAgent.tools import available_tools
from app.models import Interaction, User, Chatsession, Product

from app.utils.scrapers.scrapingfish import amazon_search, amazon_products_details, noon_search
#from app.utils.scrapers.scraperapi import amazon_search, amazon_products_details
from app.utils.productUtils import display_products, add_to_cart, create_products

llm_model = "gpt-4o-mini"  # "llama-3.1-405b-reasoning", "llama3-groq-8b-8192-tool-use-preview", "llama3-groq-70b-8192-tool-use-preview", "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gpt-4o-mini"

async def fetch_llm_response(messages, model, tools):
    response = await llmApiCall(
        model=model,
        messages=messages,
        tools=tools,
    )
    return response.choices[0].message


class ConversationState:
    """
    Maintains the state of the conversation and related interactions.
    """
    def __init__(self):
        self.messages = []
        self.tool_calls = []
        self.amazon_products = []
        self.noon_products = []
        self.added_to_cart = []
        self.search_keywords = []


def process_tool_call(tool_calls, messages, tool_call, response):
    """
    Processes a tool call by adding it to the tool_calls and messages lists.

    Args:
        tool_calls (list): List of tool call details.
        messages (list): Chat history messages.
        tool_call (dict): The tool call dictionary with details like id, name, and arguments.
        response (str): Response content to associate with the tool call.
    """
    tool_calls.append(
        {
            'id': tool_call.id,
            'name': tool_call.function.name,
            'arguments': json.loads(tool_call.function.arguments),
            'response': response,
        }
    )
    messages.append(
        {
            "role": "tool",
            "content": response,
            "tool_call_id": tool_call.id,
        }
    )
    
class ToolHandler:
    """
    Handles interactions with tools, processes tool calls, and stores results.
    """
    def __init__(self, db, country, user_id, session_id):
        self.db = db
        self.country = country
        self.user_id = user_id
        self.session_id = session_id
        self.amazon_products = []
        self.noon_products = []
        self.added_to_cart = []
        self.tool_calls = []
        self.messages = []
        self.search_keywords = []

    async def handle_tool_call(self, tool_call):
        """
        Routes tool calls to the appropriate handler.
        """
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)

        handlers = {
            "search_products": self.search_products,
            "display_products": self.display_products,
            "get_product_details": self.get_product_details,
            "add_to_cart": self.add_to_cart,
        }

        if tool_name in handlers:
            return await handlers[tool_name](tool_call, tool_args)
        else:
            return self.unknown_tool(tool_call)

    async def search_products(self, tool_call, tool_args):
        products = await amazon_search(country=self.country, **tool_args)
        formatted_results = self.format_results(products)
        self.amazon_products.extend(products)
        process_tool_call(self.tool_calls, self.messages, tool_call, formatted_results)
        return formatted_results

    async def display_products(self, tool_call, tool_args):
        products = await display_products(self.db, **tool_args)
        process_tool_call(self.tool_calls, self.messages, tool_call, "Products Displayed Successfully")
        self.amazon_products.extend(products)

    async def get_product_details(self, tool_call, tool_args):
        details = await amazon_products_details(db=self.db, country=self.country, **tool_args)
        process_tool_call(self.tool_calls, self.messages, tool_call, details)

    async def add_to_cart(self, tool_call, tool_args):
        cart_response = await add_to_cart(db=self.db, user_id=self.user_id, **tool_args)
        process_tool_call(self.tool_calls, self.messages, tool_call, cart_response)
        self.added_to_cart.extend(tool_args["productIds"])

    def unknown_tool(self, tool_call):
        response = f"Tool {tool_call.function.name} not found"
        process_tool_call(self.tool_calls, self.messages, tool_call, response)
        return response

    @staticmethod
    def format_results(products, platform):
        """
        Formats the search results for better presentation.
        """
        formatted = f"## {platform} Search Results:\n"
        for product in products:
            formatted += f"Title: {product['name']}, Price: {product['price']}\n"
        return formatted

async def finalize_interaction(db, session_id, state, message, response):
    """
    Finalizes the interaction by storing it in the database and returning the results.
    """
    # Create the interaction entry in the database
    _interaction = await Interaction.create(
        db=db,
        session_id=session_id,
        model=llm_model,
        prompt=message,
        tool_calls=state.tool_calls,
        search_keywords=state.search_keywords,
        amazon_products=state.amazon_products,
        noon_products=state.noon_products,
        added_to_cart=state.added_to_cart,
        response=response,
        next="completed",  # Mark the interaction as completed
        prompt_tokens=response.usage.prompt_tokens,
        completion_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.prompt_tokens + response.usage.completion_tokens,
    )

    # Return the final response data
    return {
        "interactionId": _interaction.id,
        "amazonProducts": state.amazon_products,
        "noonProducts": state.noon_products,
        "message": response,
        "next": False  # No further steps are needed
    }


async def newMessageChain(db, country, user_id, session_id, message):
    state = ConversationState()
    state.messages.append({'role': 'system', 'content': newMessagePrompt})

    # Load history
    history = await Interaction.find_by_session_id(db=db, session_id=session_id)
    for interaction in history:
        state.messages.append({'role': 'user', 'content': interaction.prompt})
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

    # Append user message
    state.messages.append({'role': 'user', 'content': message})

    handler = ToolHandler(db, country, user_id, session_id)

    while True:
        response = await fetch_llm_response(
            model=llm_model,
            messages=state.messages,
            tools=available_tools,
        )
        _tool_calls = response.tool_calls
        reply = response.content

        if not _tool_calls:
            # Final response
            return await finalize_interaction(
                db=db,
                session_id=session_id,
                state=state,
                message=message,
                response=reply,
            )

        # Handle tool calls
        state.messages.append(
            {
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
                    for tool_call in _tool_calls
                ],
            }
        )
        for tool_call in _tool_calls:
            await handler.handle_tool_call(tool_call)

async def nextNoonSearch(
        db: AsyncSession,
        country: str,
        interaction: Interaction
):

    interaction_id = interaction.id
    search_keywords = interaction.search_keywords[-1]
    tool_calls = interaction.tool_calls

    noonProducts = await noon_search(country, search_keywords, None)
    await create_products(db, noonProducts)

    formatted_results  =f"\n\n## TOP RESULTS FROM noon.com:"
    for result in noonProducts:
        formatted_results  += f"\n\nTitle: {result['name']}\nasin: {result['asin']}\nPrice: {result['currency']} {result['price']}\nRating: {result['rating']}"
    tool_calls[0]['response'] += formatted_results

    _interaction = await Interaction.patch(
        db=db,
        id=interaction_id,
        noon_products= noonProducts,
        tool_calls=tool_calls,
        next="top_picks"
    )
    return {
        "interactionId": _interaction.id,
        "amazonProducts": None,
        "noonProducts": noonProducts,
        "message": None,
        'next': True
    }

async def nextTopPicks(
        db: AsyncSession,
        country: str,
        interaction: Interaction
):

    interaction_id = interaction.id
    session_id = interaction.session_id
    search_keywords = interaction.search_keywords[-1]
    amazonProducts = interaction.amazon_products
    noonProducts = interaction.noon_products

    messages = [{'role': 'system', 'content': topPicksPrompt}]

    # _________________retrieve chat_session history messages
    history = await Interaction.find_by_session_id(db=db, session_id=session_id)
    for interaction in history[:-1]:
        messages.append({'role': 'user', 'content': interaction.prompt})
        if interaction.response:
            messages.append({'role': 'assistant', 'content': interaction.response})

    # __________adding current prompt and tool call/ response__________
    messages.append({'role': 'user', 'content': interaction.prompt})

    messages.append(
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": str(interaction.id),
                    "function": {
                        "name": "search_products",
                        "arguments": str({'keyword': search_keywords}),
                    },
                    "type": "function",
                }

            ],
        }
    )
    search_results = f"###Top results from amazon.{country}\n\n"
    for result in amazonProducts:
        search_results += f"\n\nTitle: {result['name']}\nasin: {result['asin']}\nPrice: {result['currency']} {result['price']}\nRating: {result['rating']}"
    search_results += f"\n\n###Top results from noon.com - {country}"
    for result in noonProducts:
        search_results += f"\n\nTitle: {result['name']}\nasin: {result['asin']}\nPrice: {result['currency']} {result['price']}\nRating: {result['rating']}"

    messages.append(
        {
            "role": "tool",
                    "content": search_results,
                    "tool_call_id": str(interaction.id),
        }
    )
    messages.append(
        {
            'role': 'user',
            'content': "Based on my quiry, what is Arobah's Top Picks?"
        }
    )

    # Api call formatting and request
    response = await llmApiCall(
        model=llm_model,
        messages=messages,
        tools=available_tools[:1]
    )
    reply = response.choices[0].message.content
    await Interaction.patch(db=db, id=interaction_id, response=reply, next='complete')
    return {
        "interactionId": interaction_id,
        "amazonProducts": None,
        "noonProducts": None,
        "message": reply,
        "next": False
    }