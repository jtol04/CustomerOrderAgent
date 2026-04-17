import os, json, requests, logging
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import START, END, StateGraph


load_dotenv()
OPENROUTER_API_KEY= os.getenv("OPENROUTER_API_KEY")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

llm = ChatOpenAI(
    model="openai/gpt-oss-120b:exacto",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    timeout=15,
    max_retries=4
)

class Order(BaseModel):
    order_num: str = Field(description="The order number exactly as it appears, e.g. 1001, 1002, etc")
    buyer: str = Field(description="The buyer's complete name given, e.g. 'Chris Myers, etc'")
    city: str = Field(description="The city name only, e.g. 'Columbus', 'Seattle', etc")
    state: str = Field(description="The state within the order location. This MUST evaluate to its two letter version e.g. 'VA', 'CA', 'NY', etc")
    total_price: float = Field(description="The total price in USD as a decimal number. Strip $ and commas but preserve all digits, e.g. 156.55, 512.00, etc")
    items: List[str] = Field(description="Complete list of items preserving all full names, e.g. 'coffee maker, monitor', 'desk lamp', etc")

class RequestFilters(BaseModel):
    min_total: Optional[float] = Field(default=None, description="The complete MINIMUM price requested by the user, e.g. 89.50, 42.10, etc")
    max_total: Optional[float] = Field(default=None, description="The complete MAXIMUM price requested by the user e.g. 156.55, 1299.99, etc")
    city: Optional[str] = Field(default=None, description="The city name only e.g. 'Columbus', 'Seattle', 'New York City', etc")
    state: Optional[str] =Field(default=None, description="The state, which MUST evaluate to its two letter version e.g. 'NY', 'VA', 'OH', etc")
    buyer: Optional[str] = Field(default=None, description="The COMPLETE name of the buyer, e.g. 'Chris Myers', 'John', 'Rachel Kim', etc")
    items: Optional[List[str]] = Field(default=None, description = "The item/s being asked for within the order, e.g. 'coffee maker, headphones', etc")
    order_num: Optional[int] = Field(default=None, description = "The order_num/ order number contained in the request, e.g. 1001, 1002, 1004, etc")
    limit: Optional[int] = Field(default=None, description = "The quantity OR limit of orders indicated in the request, e.g. 2, 5, 100")
    invalid: bool = Field(
        default=False, 
        description ="""Classify whether the request can be answered with supported filters.
Rules:
1. Set False if the request asks for all orders: 'show all orders', 'list orders', 'get orders', 'show me orders'.
2. Set False if the request mentions: a price, price range, US city, US state, buyer name, item keyword, order number, or order num.
3. Set True if the request mentions non-US locations (e.g. 'Japan', 'Europe').
4. Set True if the request mentions time or dates (e.g. 'last week', 'yesterday').
5. Set True if the request mentions attributes not in the schema (e.g. color, shipping method).
6. When uncertain, default to False."""
        )
    

class AgentState(BaseModel):
    user_request: str
    raw_orders: List[str] = []
    parsed_filters: Optional[RequestFilters] = None
    parsed_orders: List[Order] = []
    filtered_orders: List[Order]= []


def parse_request_filters(state: AgentState):
    """Use the LLM to get request filters"""
    structured_llm = llm.with_structured_output(RequestFilters)

    prompt = f"""
Analyze this customer request and get the filters being passed:
Request: {state.user_request}
Rules:
1. min_total is the complete MINIMUM price requested by the user, e.g. 89.50, 42.10, etc.
2. max_total is the complete MAXIMUM price requested by the user e.g. 156.55, 1299.99, etc.
3. city is a US city name e.g. 'Columbus', 'Seattle', 'New York City', etc.
4. state is a US state. this MUST evaluate to its two letter version e.g. 'VA', 'CA', 'NY', etc
5. buyer is the COMPLETE name of the buyer. If it is just a first name or last name, parse this name still.
as a buyer e.g. 'Chris Myers', 'Chris', 'Myers', 'John', 'Rachel Kim', etc.
6. items is the items being asked for within the order, e.g. 'coffee maker', 'headphones', etc.
7. invalid classifies whether the request can be answered with supported filters (True or False).
8. order_num is the rder_num/ order number contained in the request, e.g. 1001, 1002, 1004, etc
9. limit is the quantity OR limit of orders indicated in the request, e.g. 2, 5, 100")
10. these filters are optional, except for invalid bool which is default to False.
    """

    parsed_filters = structured_llm.invoke(prompt)

    if parsed_filters.invalid:
        logging.warning("INVALID REQUEST: Does not include a valid min_total, max_total, city, state, buyer, items, order_num or quantity filter.")
        next_node = END
    else:
        next_node = "get_orders"

    # add error check and validation here
    logging.info(f"parsed_filters: {parsed_filters}")
    return Command(
        update={"parsed_filters": parsed_filters},
        goto=next_node
    )

def get_orders(state: AgentState):
    """Fetch orders from dummy customer API"""

    if state.parsed_filters.order_num is not None:
        response = requests.get(f'http://localhost:5001/api/order/{state.parsed_filters.order_num}')
        data = response.json()
        if data["status"] == "ok":
            raw_orders = [data["raw_order"]]
        else :
            raw_orders = []

    else:
        limit = state.parsed_filters.limit
        response = requests.get('http://localhost:5001/api/orders', params={"limit": limit} if limit else {})
        data = response.json()
        if data["status"] == "ok":
            raw_orders = data["raw_orders"]
        else :
            raw_orders = []

    logging.info(response.status_code)
    logging.info(f"raw_orders: {raw_orders}")
    
    return Command(
        update={"raw_orders": raw_orders},
        goto="parse_orders"
    )

def parse_orders(state: AgentState):
    """Use the LLM to parse orders"""
    structured_llm = llm.with_structured_output(Order)
    parsed_orders = []
    for raw_order in state.raw_orders:
        logging.info(f"RAW_ORDER being parsed: {raw_order}")
        prompt = f"""
Extract structured data from this order text. Preserve all values exactly.
Order: {raw_order}
You must get the order_num, buyer, city, state, total_price, and items (list).
        """
        
        try: 
            order = structured_llm.invoke(prompt)

            # preventing hallicination
            raw_lower = raw_order.lower()
            if order.order_num not in raw_order:
                raise ValueError(f"order_num '{order.order_num}' not in RAW_ORDER")
            if order.buyer.lower() not in raw_lower:
                raise ValueError(f"buyer '{order.buyer}' not in RAW_ORDER")
            if order.city.lower() not in raw_lower:
                raise ValueError(f"city '{order.city}' not in RAW_ORDER")
            if f"{order.total_price:.2f}" not in raw_order:
                raise ValueError(f"total_price {order.total_price} not in RAW_ORDER")
            for item in order.items:
                if item.lower() not in raw_lower:
                    raise ValueError(f"item '{item}' not in RAW_ORDER")
                
            parsed_orders.append(order)
            logging.info(f"PARSED_ORDER: {order}")
        except Exception as e:
            logging.warning(f"Failed to parse RAW_ORDER for {raw_order} | Error: {e}")
            
    #logging.info(f"parsed_orders: {parsed_orders}")
    
    return Command(
        update={"parsed_orders": parsed_orders},
        goto="filter_orders"
    )


def filter_orders(state: AgentState):
    """Filter the orders based on filters applied"""
    filtered_orders = []
    for item in state.parsed_orders:
        if state.parsed_filters.min_total is not None and item.total_price < state.parsed_filters.min_total:
            continue
        if state.parsed_filters.max_total is not None and item.total_price > state.parsed_filters.max_total:
            continue
        if state.parsed_filters.city is not None and state.parsed_filters.city.lower() != item.city.lower():
            continue
        if state.parsed_filters.state is not None and state.parsed_filters.state.upper() != item.state.upper():
            continue
        if state.parsed_filters.buyer is not None and state.parsed_filters.buyer.lower() not in item.buyer.lower():
            continue
        if state.parsed_filters.items is not None:
            order_items_lower = {i.lower() for i in item.items}
            requested_lower = {i.lower() for i in state.parsed_filters.items}
            if not requested_lower.intersection(order_items_lower):
                continue
        if state.parsed_filters.order_num is not None and str(state.parsed_filters.order_num) != item.order_num:
            continue

        filtered_orders.append(item)
        logging.info(f"ORDER {item} added to FILTERED_ORDERS")
    
    return Command(
        update={"filtered_orders": filtered_orders},
        goto=END
    )

workflow = StateGraph(AgentState)
workflow.add_node("parse_request_filters", parse_request_filters)
workflow.add_node("get_orders", get_orders)
workflow.add_node("parse_orders", parse_orders)
workflow.add_node("filter_orders", filter_orders)


workflow.add_edge(START, "parse_request_filters")
app = workflow.compile()

def main():
    request = input("Hello! What orders you like to see? ")
    initial_state = AgentState(user_request = request)
    result = app.invoke(initial_state)

    filtered_orders = result["filtered_orders"]

    if not filtered_orders:
        print("Order not found.")
    else:
        output = {"orders": [order.model_dump() for order in filtered_orders]}
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()