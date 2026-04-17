import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from langgraph.types import Command
from typing import Optional, List
from pydantic import BaseModel, Field

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
    filters: RequestFilters
    parsed_orders: List[Order]

request = input("What would you like to do? ")

def read_request(state: AgentState) -> dict:
    """Extract and parse request content"""

    state['user_request'] = request
    return {
        "messages": [HumanMessage(content=f"Processing request: {state['user_request']}")]
    }

def get_request_filters(state: AgentState):
    """Use the LLM to get request filters"""
    structured_llm = llm.with_structured_output(RequestFilters)

    prompt = f"""
    Analyze this customer request and get the filters being passed:

    Request: {state['user_request']}
    
    Provide optional filters passed including min_total, max_total, location,
    buyer, and items.
    """

    filters = structured_llm.invoke(prompt)

    # add error check and validation here

    return Command(
        update={"filters": filters},
        goto="parse_orders"
    )

def parse_orders(state: AgentState):
    """Use the LLM to structure orders"""
    structured_llm = llm.with_structured_output(Order)
    parsed_orders = []
    for raw_order in state['raw_orders']:
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

