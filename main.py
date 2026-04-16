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

request = input("What would you like to do? ")

class AgentState(BaseModel):
    # Raw request data
    user_request: str
    filters: RequestFilters
    orders: List[Order]

def read_request(request) -> dict:
    """Extract and parse request content"""

    return {
        "messages": [HumanMessage(content=f"Processing request: {request}")]
    }

def get_request_filters(state: AgentState):
    """Use the LLM to get request filters"""
    structured_llm = llm.with_structured_output(Order)

    prompt = f"""
    Analyze this customer request and get the filters being passed:

    Request: {state['user_request']}
    
    Provide optional filters passed including min_total, max_total, location,
    total_price, and items.
    """

    filters = structured_llm.invoke(prompt)

