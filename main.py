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
    order_num: str = Field(description="The order number")
    buyer: str = Field(description="The buyer's name")
    location: str = Field(description="The location")
    total_price: float = Field(description="The total price")
    items: List[str] = Field(description="The list of items")

class RequestFilters(BaseModel):
    min_total: Optional[float] = None
    max_total: Optional[float] = None
    location: Optional[str] = None
    buyer: Optional[str] = None
    items: Optional[List[str]] = None

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
    #print(response.status_code)
    #print(data["raw_orders"])
    
    return Command(
        update={"raw_orders": data["raw_orders"]},
        goto="parse_orders"
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
        and (state.parsed_filters.max_total is None or item.total_price <= state.parsed_filters.max_total)
        and (state.parsed_filters.location is None or item.location == state.parsed_filters.location)
        and (state.parsed_filters.buyer is None or item.buyer == state.parsed_filters.buyer)
        and (state.parsed_filters.items is None or item.items in state.parsed_filters.items)
    ]
    
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

    print(result["filtered_orders"])

if __name__ == "__main__":
    main()