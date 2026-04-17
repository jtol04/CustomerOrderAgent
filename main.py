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
    timeout=30,
    max_retries=2
)

class Order(BaseModel):
    order_num: str = Field(description="The order number exactly as it appears, e.g. 1001, 1002, etc")
    buyer: str = Field(description="The buyer's complete full name given, e.g. 'Chris Myers, etc'")
    city: str = Field(description="The city name only, e.g. 'Columbus', 'Seattle', etc")
    state: str = Field(description="The state within the order location. This MUST evaluate to its two letter version e.g. 'VA', 'CA', 'NY', etc")
    total_price: float = Field(description="The total price in USD as a decimal number. Strip $ and commas but preserve all digits, e.g. '156.55', '512.00', etc")
    items: List[str] = Field(description="Complete list of items preserving all full names, e.g. 'coffee maker, monitor', 'desk lamp', etc")

class RequestFilters(BaseModel):
    min_total: Optional[float] = Field(default=None, description="The complete MINIMUM price requested by the user, e.g. '89.50', '742.10', etc")
    max_total: Optional[float] = Field(default=None, description="The complete MAXIMUM price requested by the user e.g. '156.55', '1299.99', etc")
    city: Optional[str] = Field(default=None, description="The city name only e.g. 'Columbus', 'Seattle', etc")
    state: Optional[str] =Field(default=None, description="The state, which MUST evaluate to its two letter version e.g. 'NY', 'VA', 'OH', etc")
    buyer: Optional[str] = Field(default=None, descrption="The COMPLETE name of the buyer, e.g. 'Chris Myers', 'John', 'Rachel Kim', etc")
    items: Optional[List[str]] = Field(default=None, description = "The item/s being asked for within the order, e.g. 'coffee maker, headphones', etc")

class AgentState(BaseModel):
    # Raw request data
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
    
    Provide filters passed, which may include min_total, max_total, city,
    state (two letters), buyer, and items. Note that these are optional.
    """

    parsed_filters = structured_llm.invoke(prompt)

    # add error check and validation here
    logging.info(f"parsed_filters: {parsed_filters}")
    return Command(
        update={"parsed_filters": parsed_filters},
        goto="get_orders"
    )

def get_orders(state: AgentState):
    response = requests.get('http://localhost:5001/api/orders')
    data = response.json()
    logging.info(response.status_code)
    raw_orders = data["raw_orders"]

    logging.info(f"raw_orders: {raw_orders}")
    
    return Command(
        update={"raw_orders": raw_orders},
        goto="parse_orders"
    )

def parse_orders(state: AgentState):
    """Use the LLM to structure orders"""
    structured_llm = llm.with_structured_output(Order)
    parsed_orders = []
    for raw_order in state.raw_orders:
        logging.info(f"current raw order being parsed: {raw_order}")
        prompt = f"""
        Analyze this order.

        Order: {raw_order}
        
        Provide the order number, buyer name, city, state, total_price,
        and the list of items.
        """
        
        try: 
            order = structured_llm.invoke(prompt)
            parsed_orders.append(order)
            logging.info(f"parsed order: {order}")
        except Exception as e:
            logging.warning(f"Failed to parse order for {raw_order} | Error: {e}")
    
    #logging.info(f"parsed_orders: {parsed_orders}")
    
    return Command(
        update={"parsed_orders": parsed_orders},
        goto="filter_orders"
    )


def filter_orders(state: AgentState):
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

        filtered_orders.append(item)
    
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
    request = input("What would you like to do? ")
    initial_state = AgentState(user_request = request)
    result = app.invoke(initial_state)

    filtered_orders = result["filtered_orders"]
    output = {"orders": [order.model_dump() for order in filtered_orders]}

    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()