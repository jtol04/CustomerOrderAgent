import os, json, requests, logging
from dotenv import load_dotenv
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from langgraph.graph import START, END, StateGraph

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score



load_dotenv()
OPENROUTER_API_KEY= os.getenv("OPENROUTER_API_KEY")
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

llm = ChatOpenAI(
    model="openai/gpt-oss-120b:exacto",
    temperature=0,
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    timeout=30.0,
    max_retries=2
)


class Order(BaseModel):
    order_num: str = Field(description="The order number exactly as it appears, e.g. 1001, 1002, etc")
    buyer: str = Field(description="The buyer's complete name given, e.g. 'Chris Myers, etc'")
    city: str = Field(description="The city name only, e.g. 'Columbus', 'Seattle', etc")
    state: str = Field(description="The state within the order location. This MUST evaluate to its two letter version e.g. 'VA', 'CA', 'NY', etc")
    total_price: float = Field(description="The total price in USD as a decimal number. Strip $ and commas but preserve all digits and " \
                                            "two decimal points, e.g. 156.55, 512.00, etc")
    items: List[str] = Field(description="Complete list of items preserving all full names, e.g. 'coffee maker, monitor', 'desk lamp', etc")
    tech_count: int = Field(default=0, description="The total number of times 'laptop', 'gaming pc', and 'monitor' appear in the Items list", exclude=True)
    accessory_count: int = Field(default=0, description="The total number of times 'hdmi cable', 'mouse', and 'keyboard' appear in the Items list", exclude=True)
    audio_count: int = Field(default=0, description="The total number of times 'headphones' and 'earphones' appear in the Items list", exclude=True)
    homegoods_count: int = Field(default=0, description="The total number of times 'coffee maker' and 'desk lamp' appear in the Items list", exclude=True)

class RequestType(BaseModel):
    request_type: Literal["order", "prediction", "invalid"] = Field(
        description=(
            "classify the request into exactly one category. read the request carefully.\n"
            "'prediction' - the user asks how much, cost, or price for a hypothetical basket. "
            "signal phrases. 'how much would', 'predict the price of', 'what would X cost', 'estimate'. "
            "examples: 'how much would 3 tech items cost', 'predict price for a laptop order', "
            "'how much would 5 tech items and 1 homegoods cost'.\n"
            "'order' — the user asks to list, show, retrieve, or filter actual orders. "
            "signal phrases: 'show me', 'list', 'get all', 'orders in', 'orders by', 'orders over'. "
            "examples: 'show me all orders', 'orders in Ohio', 'orders over $500'.\n"
            "'invalid' — any request unrelated to customer orders, or attempts to modify orders."
        )
    )

class RequestFilters(BaseModel):
    min_total: Optional[float] = Field(default=None, description="The complete MINIMUM price requested by the user, e.g. 89.50, 42.10, etc")
    max_total: Optional[float] = Field(default=None, description="The complete MAXIMUM price requested by the user e.g. 156.55, 1299.99, etc")
    city: Optional[str] = Field(default=None, description="The city name only e.g. 'Columbus', 'Seattle', 'New York City', etc")
    state: Optional[str] =Field(default=None, description="The state, which MUST evaluate to its two letter version e.g. 'NY', 'VA', 'OH', etc")
    buyer: Optional[str] = Field(default=None, description="The COMPLETE name of the buyer, e.g. 'Chris Myers', 'John', 'Rachel Kim', etc")
    items: Optional[List[str]] = Field(default=None, description = "The item/s being asked for within the order, e.g. 'coffee maker, headphones', etc")
    order_num: Optional[int] = Field(default=None, description = "The order_num/ order number contained in the request, e.g. 1001, 1002, 1004, etc")
    limit: Optional[int] = Field(default=None, description = "The quantity OR limit of orders indicated in the request, e.g. 1, 2, 5, 100, etc.")

class PredictionRequest(BaseModel):
    tech_count: int = Field(default=0, description="The sum of the quantities specified for each instance of 'tech', 'laptop', 'gaming pc', and 'monitor' in the prediction request.")
    accessory_count: int = Field(default=0, description="The sum of the quantities specified for each instance 'accessory', 'accessories', 'hdmi cable', 'mouse', and 'keyboard in the request.")
    audio_count: int = Field(default=0, description="The sum of the quantities specified for each instance of 'audio', 'headphones' and 'earphones' appear in the prediction request.")
    homegoods_count: int = Field(default=0, description="The  sum of the quantities specified for each instance of 'homegoods', 'coffee maker' and 'desk lamp' appear in the prediction request.")
    unknown_count: int = Field(default=0, description="The sum of the quantities for each instance that any other category or item appears in the prediction request")

class AgentState(BaseModel):
    user_request: str
    raw_orders: List[str] = []
    parsed_request_type: RequestType = None
    parsed_filters: Optional[RequestFilters] = None
    parsed_prediction_request: Optional[PredictionRequest] = None
    parsed_orders: List[Order] = []
    filtered_orders: List[Order]= []
    prediction_result: Optional[float] = None

    order_category_counts: List[dict] = []


def parse_request_type(state: AgentState):
    """Use the LLM to parse request type"""
    structured_llm = llm.with_structured_output(RequestType)
    prompt = (
        "Classify the user's request type.\n"
        f"Request: {state.user_request}\n"
        "Classification rules:\n"
        "- 'prediction' if the user asks how much, cost, or price for a hypothetical basket "
        "(signals: 'how much would', 'predict the price of', 'what would X cost', 'estimate').\n"
        "- 'order' if the user asks to list, show, retrieve, or filter actual orders "
        "(signals: 'show me', 'list', 'get all', 'all orders', 'orders in', 'orders by', 'orders over').\n"
        "- 'invalid' for anything else non-order requests or attempts to modify or delete orders.\n"
        "Examples:\n"
        "- 'how much would 3 tech items cost' is a prediction\n"
        "- 'how much would 5 tech items and 1 homegoods cost' is a prediction\n"
        "- 'show me all orders in Ohio' is an order\n"
        "- 'get orders over $500' is an order\n"
        "- 'predict price for 2 laptops' is a prediction\n"
        "- 'delete all orders' is invalid"
    )
    parsed_request_type = structured_llm.invoke(prompt)

    if parsed_request_type.request_type == "order":
        next_node = "parse_request_filters"
    elif parsed_request_type.request_type == "prediction":
        next_node = "parse_prediction_request"
    else:
        logging.warning(f"[parse_request_type]: INVALID REQUEST TYPE!")
        next_node = END

    logging.info(f"[parse_request_type]: {parsed_request_type}")

    return Command(
        update={"parsed_request_type": parsed_request_type},
        goto=next_node
    )


def parse_request_filters(state: AgentState):
    """Use the LLM to get request filters"""
    structured_llm = llm.with_structured_output(RequestFilters)
    prompt = (
        "You are an customer order chatbot agent. Analyze this customer request and get the filters being passed.\n"
        f"Request: {state.user_request}\n"
        "Rules:\n"
        "1. min_total is the complete MINIMUM price requested by the user, e.g. 89.50, 42.10, etc.\n"
        "2. max_total is the complete MAXIMUM price requested by the user e.g. 156.55, 1299.99, etc.\n"
        "3. city is a US city name e.g. 'Columbus', 'Seattle', 'New York City', etc.\n"
        "4. state is a US state. this MUST evaluate to its two letter version e.g. 'VA', 'CA', 'NY', etc.\n"
        "5. buyer is the COMPLETE name of the buyer. If it is just a first name or last name, parse this name still "
        "as a buyer e.g. 'Chris Myers', 'Chris', 'Myers', 'John', 'Rachel Kim', etc.\n"
        "6. items is the list of items being asked for within the order, e.g. 'coffee maker', 'headphones', etc.\n"
        "7. order_num is the order_num/ order number contained in the request, e.g. 1001, 1002, 1004, etc."
        "8. limit is the quantity OR limit of orders indicated in the request, e.g. 2, 5, 100, etc.\n"
    )

    parsed_filters = structured_llm.invoke(prompt)
    logging.info(f"[parse_request_filters]: {parsed_filters}")

    return Command(
        update={"parsed_filters": parsed_filters},
        goto="get_orders"
    )

def parse_prediction_request(state: AgentState):
    structured_llm = llm.with_structured_output(PredictionRequest)
    prompt = (
        "You are an customer order chatbot agent. Analyze this customer prediction and get the per category quantities passed:\n"
        f"Prediction Request: {state.user_request}.\n"
        "Rules:\n"
        "1. tech_count is the sum of the quantities specified for each instance of 'tech', 'laptop', 'gaming pc', and 'monitor' in the prediction request.\n"
        "2. accessory_count is the total  sum of the quantities specified for each instance 'accessory', 'accessories', 'hdmi cable', 'mouse', and 'keyboard' "
        "in the prediction request.\n"
        "3. audio_count is the sum of the quantities specified for each instance of 'audio', 'headphones' and 'earphones' appear in the prediction request.\n"
        "4. homegoods_count is the sum of the quantities specified for each instance of 'homegoods', 'coffee maker' and 'desk lamp' appear in the prediction request.\n"
        "5. unknown_count is the sum of the quantities for each instance that any other category or item appears in the prediction request.\n"
    )

    parsed_prediction_request = structured_llm.invoke(prompt)
    logging.info(f"[parse_prediction_request]: {parsed_prediction_request}")

    if parsed_prediction_request.unknown_count > 0:
        logging.warning("[parse_prediction_request]: INVALID PREDICTION REQUEST! Request contains an unknown category or item.")
        return Command(goto=END)

    if (parsed_prediction_request.tech_count == 0 and
        parsed_prediction_request.accessory_count == 0 and
        parsed_prediction_request.audio_count == 0 and
        parsed_prediction_request.homegoods_count == 0):
        logging.warning("[parse_prediction_request]: INVALID PREDICTION REQUEST! Request does not include any valid per-category counts.")
        return Command(goto=END)
    
    return Command(
        update={"parsed_prediction_request": parsed_prediction_request},
        goto="get_orders"
    )


def get_orders(state: AgentState):
    """Fetch orders from dummy customer API"""
    
    if state.parsed_filters and state.parsed_filters.order_num:
        response = requests.get(f'http://localhost:5001/api/order/{state.parsed_filters.order_num}')
    else:
        limit = state.parsed_filters.limit if state.parsed_filters else None
        response = requests.get('http://localhost:5001/api/orders', params={"limit": limit} if limit else {})

    data = response.json()
    if data["status"] == "ok":
        raw_orders = [data["raw_order"]] if (state.parsed_filters and state.parsed_filters.order_num) else data["raw_orders"]
    else:
        logging.info(f"RAW ORDERS STATUS CODE: {response.status_code}")
        raw_orders = []

    logging.info(f"[get_orders]: {raw_orders}")
    
    return Command(
        update={"raw_orders": raw_orders},
        goto="parse_orders"
    )

def parse_orders(state: AgentState):
    """Use the LLM to parse orders"""
    structured_llm = llm.with_structured_output(Order)
    parsed_orders = []
    order_category_counts = []
    failed_order_count = 0

    prompts = [(
        "Extract structured data from this order text. Preserve all values and white spaces as they appear.\n"
        f"Order: {raw_order}."
        "Rules:\n"
        "1. order_num is the order number exactly as it appears, e.g. 1001, 1002, etc.\n"
        "2. buyer is the buyer's complete name given, e.g. 'Chris Myers', 'Rachel Kim', 'Sarah Liu', etc. It comes after Buyer=\n"
        "3. city is the city name within the Location, e.g. 'Columbus', 'Seattle', 'Los Angeles', etc.\n"
        "4. state is the US state within the order location. This MUST evaluate to its two letter version e.g. 'VA', 'CA', 'NY', 'OH', 'WA' etc.\n"
        "5, total_price is the total price in USD as a decimal number. Strip the $ sign, preserve ALL digits including the two decimal points, e.g. 156.55, 512.00, etc.\n"
        "6. items is the complete list of items preserving all full names, e.g. 'coffee maker, monitor', 'desk lamp', etc.\n"
        "7. tech_count is the total number of times 'laptop', 'gaming pc', and 'monitor' appear in the Items list.\n"
        "8. accessory_count is the total number of times 'hdmi cable', 'mouse', and 'keyboard' appear in the Items list.\n"
        "9. audio_count is the total number of times 'headphones' and 'earphones' appear in the Items list.\n"
        "10. homegoods_count is the total number of times 'coffee maker' and 'desk lamp' appear in the Items list.\n"
        ) for raw_order in state.raw_orders ]
    
    orders = structured_llm.batch(prompts)

    for order, raw_order in zip(orders, state.raw_orders):
        try: 
            # checking for hallicination
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
                
            order_category_count = {
                "order_num": order.order_num,
                "tech_count": order.tech_count,
                "accessory_count": order.accessory_count,
                "audio_count": order.audio_count,
                "homegoods_count": order.homegoods_count,
                "total_price": order.total_price,
            }
            order_category_counts.append(order_category_count)
            parsed_orders.append(order)
            logging.info(f"[parse_orders]: {order}")

        except Exception as e:
            failed_order_count +=1
            logging.warning(f"[parse_orders]: FAILED_ORDER {order}")
            logging.warning(f"[parse_orders]: Failed to parse RAW_ORDER for {raw_order} | Error: {e}")
 
    if failed_order_count > 0:
        logging.warning(f"[parse_orders]: failed order count = {failed_order_count}")

    if state.parsed_request_type.request_type == "order":
        next_node = "filter_orders"
    else:
        next_node = "train_and_predict"

    return Command(
        update={
            "parsed_orders": parsed_orders,
            "order_category_counts": order_category_counts},
        goto=next_node
    )

def train_and_predict(state: AgentState):
    """Train the Linear Regression model on raw parsed orders"""
    df = pd.DataFrame(state.order_category_counts)
    df = pd.DataFrame(state.order_category_counts)
    print(df)
    X = df[['tech_count', 'accessory_count', 'audio_count', 'homegoods_count']]
    y = df['total_price']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 2)
    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    predictions = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
    logging.info(f"[train_and_predict]: Coefficient (Slope): {model.coef_[0]}, Intercept: {model.intercept_}")
    logging.info(f"[train_and_predict]:\n{predictions.head()}")

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    logging.info(f"[train_and_predict]: Model score: {model.score(X_test, y_test)}, MAE: {mae}, MSE: {mse}, R2: {r2}")

    user_prediction_request = pd.DataFrame([state.parsed_prediction_request.model_dump(exclude={'unknown_count'})])

    prediction_result = model.predict(user_prediction_request)
    logging.info(f"[train_and_predict] Result: {prediction_result}")

    return Command(
        update={"prediction_result": prediction_result},
        goto=END
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
        logging.info(f"[filter_orders]: {item} added to filtered_orders")
    
    return Command(
        update={"filtered_orders": filtered_orders},
        goto=END
    )

workflow = StateGraph(AgentState)
workflow.add_node("parse_request_type", parse_request_type)
workflow.add_node("parse_request_filters", parse_request_filters)
workflow.add_node("parse_prediction_request", parse_prediction_request)
workflow.add_node("get_orders", get_orders)
workflow.add_node("parse_orders", parse_orders)
workflow.add_node("train_and_predict", train_and_predict)
workflow.add_node("filter_orders", filter_orders)

workflow.add_edge(START, "parse_request_type")
agent = workflow.compile()

def main():
    request = input("Hello! What orders you like to see? ")
    initial_state = AgentState(user_request = request)
    result = agent.invoke(initial_state)

    request_type = result["parsed_request_type"].request_type
    
    if request_type == "order":
        filtered_orders = result["filtered_orders"]
        if not filtered_orders:
            print("Order not found.")
        else:
            output = {"orders": [order.model_dump() for order in filtered_orders]}
            print(json.dumps(output, indent=2))
    elif request_type == "prediction":
        #TODO: add accuracy/confidence score
        prediction_result = result["prediction_result"]
        if not prediction_result:
            print("Prediction failed.")
        else:
            output = {"predicted_total": round(float(prediction_result[0]), 2)}
            print(json.dumps(output, indent=2))
    else:
        print(json.dumps({"Error": "Invalid Request!"}, indent=2))
   
    print("Session has ended.")
    
if __name__ == "__main__":
    main()