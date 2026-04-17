import os
import requests
from dotenv import load_dotenv
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langgraph.types import Command
from langgraph.graph import START, END, StateGraph


load_dotenv()
OPENROUTER_API_KEY= os.getenv("OPENROUTER_API_KEY")

llm = ChatOpenAI(
    model="openai/gpt-oss-120b:exacto",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

class Order(BaseModel):
    order_num: int = Field(description="The order number")
    buyer: str = Field(description="The buyer's name")
    location: str = Field(description="The location")
    total_price: int = Field(description="The total price")
    items: List[str] = Field(description="The list of items")

class RequestFilters(BaseModel):
    min_total: Optional[int] = None
    max_total: Optional[int] = None
    location: Optional[str] = None
    buyer: Optional[str] = None
    items: Optional[List[str]] = None

class AgentState(BaseModel):
    # Raw request data
    user_request: str
    raw_orders: List[str]
    parsed_filters: RequestFilters
    parsed_orders: List[Order]

request = input("What would you like to do? ")

def read_request(state: AgentState) -> dict:
    """Extract and parse request content"""

    state.user_request = request
    return {
        "messages": [HumanMessage(content=f"Processing request: {state.user_request}")]
    }

def parse_request_filters(state: AgentState):
    """Use the LLM to get request filters"""
    structured_llm = llm.with_structured_output(RequestFilters)

    prompt = f"""
    Analyze this customer request and get the filters being passed:

    Request: {state.user_request}
    
    Provide filters passed, which may include min_total, max_total, location,
    buyer, and items. Note that these are optional.
    """

    parsed_filters = structured_llm.invoke(prompt)

    # add error check and validation here

    return Command(
        update={"parsed_filters": parsed_filters},
        goto="get_orders"
    )

def get_orders(state: AgentState):
    response = requests.get('http://localhost:5001/api/orders')
    data = response.json()
    print(response.status_code)
    print(data["raw_orders"])
    
    return Command(
        update={"raw_orders": data["raw_orders"]},
        goto=parse_orders
    )

def parse_orders(state: AgentState):
    """Use the LLM to structure orders"""
    structured_llm = llm.with_structured_output(Order)
    parsed_orders = []
    for raw_order in state.raw_orders:
        prompt = f"""
        Analyze this order.

        Order: {raw_order}
        
        Provide the order_num, buyer, location, total_price,
        and the list of items.
        """
        parsed_orders.append(structured_llm.invoke(prompt))
    
    return Command(
        update={"parsed_orders": parsed_orders},
        goto="filter_orders"
    )


def filter_orders(state: AgentState):
    filtered_orders = [
        item for item in state.parsed_orders
        if (state.parsed_filters.min_total is None or item.total_price >= state.parsed_filters.min_total)
        and (state.parsed_filters.max_total is None or item.total_price <= state.parsed_filtersmax_total)
        and (state.parsed_filters.location is None or item.location == state.parsed_filters.location)
        and (state.parsed_filters.buyer is None or item.buyer == state.parsed_filters.buyer)
        and (state.parsed_filters.items is None or item.items in state.parsed_filters.items)
    ]
    
    return Command(
        update={filtered_orders},
        goto=END
    )