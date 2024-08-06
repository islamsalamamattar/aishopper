import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.llms.apiCall import llmApiCall
from app.agents.chatAgent.prompts import instructionsPrompt
from app.agents.chatAgent.tools import available_tools
from app.models import Interaction, User, Chatsession, Product

from app.utils.scraperUtils import (
    search_products,
    extract_top_n,
    display_products,
    get_products_details,
    add_to_cart
)

llm_model = "gpt-4o-mini" #"llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768"

async def chatChain(
        db: AsyncSession,
        country: str,
        session_id: str,
        message: str
        ):

    messages = [{'role': 'system', 'content': instructionsPrompt}]

    # _________________retrieve chat_session history messages
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
            messages.append({'role': 'assistant', 'content': interaction.response})
    messages.append({'role': 'user', 'content': message})

    products_frontend = None
    images_frontend = None

    tool_calls = []
    displayed_products = None
    displayed_images = None
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

        #__________FINAL RESPONSE - MESSAGE, NO TOOL CALLS__________
        if not _tool_calls:
            _interaction = await Interaction.create(
                db=db,
                session_id=session_id,
                model=llm_model,
                prompt=message,
                tool_calls= tool_calls,
                displayed_products=displayed_products,
                displayed_images=displayed_images,
                added_to_cart=products_added_to_cart,
                response=reply,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens= response.usage.prompt_tokens + response.usage.completion_tokens
            )
            return {
                "products": products_frontend,
                "images":images_frontend,
                "message": reply,
                "interactionId": _interaction.id,
                "alerts": None
            }
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

        #__________LLM RESPONSE CONTAINS TOOL CALL__________
        for tool_call in _tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print("============= Arobah TOOL CALL =============\n")
            print(f"Tool name: {tool_name}")
            print(f"Tool args: {tool_args}")
            print("\n===========================================")

            #__________SEARCH PRODUCTS - TOOL CALL__________
            if tool_name == "search_products":
                _products = await search_products(country=country, **tool_args)
                top_results = await extract_top_n(db=db, products=_products, country=country, n=12)
                
                tool_calls.append(
                        {
                            'id': tool_call.id,
                            'name': tool_name,
                            'arguments': tool_args,
                            'response': top_results
                        }
                    )
                messages.append(
                    {
                        "role": "tool",
                        "content": str(top_results),
                        "tool_call_id": tool_call.id,
                    }
                )


            #__________DISPLAY PRODUCTS - TOOL CALL__________
            elif tool_name == "display_products":
                
                _display = await display_products(db, **tool_args)
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
                        "content": "Products Displayed Successfully",
                        "tool_call_id": tool_call.id,
                    }
                )
                products_frontend = _display
                displayed_products = tool_args


            #__________GET PRODUCT DETAILED - TOOL CALL__________
            elif tool_name == "get_product_details":
                _details = await get_products_details(db=db, country=country, **tool_args)
                tool_calls.append(
                        {
                            'id': tool_call.id,
                            'name': tool_name,
                            'arguments': tool_args,
                            'response': _details
                        }
                    )
                messages.append(
                    {
                        "role": "tool",
                        "content": str(_details),
                        "tool_call_id": tool_call.id,
                    }
                )


            #__________DISPLAY PRODUCT IMAGES - TOOL CALL__________
            elif tool_name == "display_product_images":
                await get_products_details(db, country=country, **tool_args)
                asin = tool_args["productId"]
                _display_images = await Product.find_by_asin(db, asin)
                tool_calls.append(
                        {
                            'id': tool_call.id,
                            'name': tool_name,
                            'arguments': tool_args,
                            'response': "Images displayed successfully"
                        }
                    )
                messages.append(
                    {
                        "role": "tool",
                        "content": "Images displayed successfully",
                        "tool_call_id": tool_call.id,
                    }
                )
                images_frontend = _display_images.images
                displayed_images = tool_args["productId"]


            #__________ADD TO CART - TOOL CALL__________
            elif tool_name == "add_to_cart":
                _cart = await add_to_cart(**tool_args)
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
                products_added_to_cart.extend(tool_args["productId"])
                

            else:
                #__________TOOL NAME NOT FOUND__________
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
