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

async def newMesssageChain(
        db: AsyncSession,
        country: str,
        user_id: str,
        session_id: str,
        message: str
):

    messages = [{'role': 'system', 'content': newMessagePrompt}]

    # Retrieve chat_session history messages
    history = await Interaction.find_by_session_id(db=db, session_id=session_id)
    for interaction in history:
        messages.append({'role': 'user', 'content': interaction.prompt})
        for tool_call in interaction.tool_calls:

            messages.append(
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
                }
            )
            messages.append(
                {
                    "role": "tool",
                            "content": str(tool_call['response']),
                            "tool_call_id": tool_call['id'],
                }
            )
            if interaction.response:
                messages.append({'role': 'assistant', 'content': interaction.response})
    
    # Append new user's message to history
    messages.append({'role': 'user', 'content': message})

    # Intialize lists
    tool_calls = []
    search_keywords = []
    amazon_products = []
    noon_products = []
    products_added_to_cart = []

    while True:
        # Api call formatting and request
        response = await llmApiCall(
            model=llm_model,
            messages=messages,
            tools=available_tools,
        )
        _tool_calls = response.choices[0].message.tool_calls
        reply = response.choices[0].message.content

        # __________FINAL RESPONSE - MESSAGE, NO TOOL CALLS__________
        if not _tool_calls:
            _interaction = await Interaction.create(
                db=db,
                session_id=session_id,
                model=llm_model,
                prompt=message,
                tool_calls=tool_calls,
                search_keywords=search_keywords,
                amazon_products=amazon_products,
                noon_products=noon_products,
                added_to_cart=products_added_to_cart,
                response=reply,
                next="completed",
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.prompt_tokens + response.usage.completion_tokens
            )
            return {
                "interactionId": _interaction.id,
                "amazonProducts": amazon_products,
                "noonProducts": noon_products,
                "message": reply,
                "next": False
            }

        # __________LLM RESPONSE CONTAINS TOOL CALL__________
        messages.append(
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
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # __________SEARCH PRODUCTS - TOOL CALL__________
            if tool_name == "search_products":
                amazonProducts = await amazon_search(country=country, **tool_args)

                await create_products(db, amazonProducts)
                _session = await Chatsession.find_by_id(db, session_id)
                if _session.title == "New Session":
                    new_title = (" ".join(tool_args['keywords'])[:20] + " ...") if len(" ".join(tool_args['keywords'])) > 20 else " ".join(tool_args['keywords'])
                    await Chatsession.update_title(db, session_id, new_title)
                
                formatted_results  =f"## TOP RESULTS FROM amazon.{country}:"
                for result in amazonProducts:
                    formatted_results  += f"\n\nTitle: {result['name']}\nasin: {result['asin']}\nPrice: {result['currency']} {result['price']}\nRating: {result['rating']}"

                amazon_products.extend(amazonProducts)
                search_keywords.append(tool_args['keywords'])
                tool_calls.append(
                    {
                        'id': tool_call.id,
                        'name': tool_name,
                        'arguments': tool_args,
                        'response': formatted_results
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": formatted_results,
                        "tool_call_id": tool_call.id,
                    }
                )
                _interaction = await Interaction.create(
                    db=db,
                    session_id=session_id,
                    model=llm_model,
                    prompt=message,
                    tool_calls=tool_calls,
                    next="noon_search",
                    search_keywords=search_keywords,
                    amazon_products=amazon_products,
                    noon_products=noon_products,
                    added_to_cart=products_added_to_cart,
                    response=reply,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.prompt_tokens + response.usage.completion_tokens
                )
                return {
                    "interactionId": _interaction.id,
                    "amazonProducts": amazon_products,
                    "noonProducts": None,
                    "message": reply,
                    "next": True
                }

            # __________DISPLAY PRODUCTS - TOOL CALL__________
            elif tool_name == "display_products":
                _displayed_products = await display_products(db, **tool_args)
                tool_calls.append(
                    {
                        'id': tool_call.id,
                        'name': tool_name,
                        'arguments': tool_args,
                        'response': "Products Displayed Successfully"
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": f"Products Displayed Successfully:\n\n{_displayed_products}",
                        "tool_call_id": tool_call.id,
                    }
                )
                amazon_products.extend(_displayed_products)

            # __________GET PRODUCT DETAILED - TOOL CALL__________
            elif tool_name == "get_product_details":
                _product = await amazon_products_details(db=db, country=country, **tool_args)
                
                tool_calls.append(
                    {
                        'id': tool_call.id,
                        'name': tool_name,
                        'arguments': tool_args,
                        'response': _product
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": str(_product),
                        "tool_call_id": tool_call.id,
                    }
                )

            # __________ADD TO CART - TOOL CALL__________
            elif tool_name == "add_to_cart":
                _cart = await add_to_cart(db=db,user_id=user_id,**tool_args)
                tool_calls.append(
                    {
                        'id': tool_call.id,
                        'name': tool_name,
                        'arguments': tool_args,
                        'response': _cart
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": str(_cart),
                        "tool_call_id": tool_call.id,
                    }
                )
                products_added_to_cart.extend(tool_args["productIds"])

            else:
                # __________TOOL NAME NOT FOUND__________
                tool_calls.append(
                    {
                        'id': tool_call.id,
                        'name': tool_name,
                        'arguments': tool_args,
                        'response': f"Tool {tool_name} not found"
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "content": f"Tool {tool_name} not found",
                        "tool_call_id": tool_call.id,
                    }
                )
            
            if reply:
                _interaction = await Interaction.create(
                    db=db,
                    session_id=session_id,
                    model=llm_model,
                    prompt=message,
                    tool_calls=tool_calls,
                    next="complete",
                    amazon_products=amazon_products,
                    noon_products=noon_products,
                    added_to_cart=products_added_to_cart,
                    response=reply,
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.prompt_tokens + response.usage.completion_tokens
                )
                return {
                    "interactionId": _interaction.id,
                    "amazonProducts": amazon_products,
                    "noonProducts": noon_products,
                    "message": reply,
                    "next": False
                } 
            
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