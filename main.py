import os
from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage
from typing import Optional, List
from pydantic import BaseModel

load_dotenv()
OPENROUTER_API_KEY= os.getenv("OPENROUTER_API_KEY")

model = ChatOpenAI(
    model="openai/gpt-oss-120b:exacto",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

class Order(BaseModel):
    order_num: int
    buyer: str
    location: str
    total_price: int
    items: List[str]

class RequestFilters(BaseModel):
    min_total: Optional[int] = None
    max_total: Optional[int] = None
    location: Optional[str] = None
    buyer: Optional[str] = None
    items: Optional[List[str]] = None

class AgentState(BaseModel):
    # Raw request data
    user_request: str
    filters: RequestFilters
    orders: List[Order]

request = input("What would you like to do? ")

def read_request(request) -> dict:
    """Extract and parse request content"""

    return {
        "messages": [HumanMessage(content=f"Processing request: {request}")]
    }

def 