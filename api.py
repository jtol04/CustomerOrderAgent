from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import AgentState, agent

app = FastAPI()

origins = []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Request(BaseModel):
    request: str

@app.post("/request/")
async def create_request(request: Request):
    initial_state = AgentState(user_request = request)
    result = agent.invoke(initial_state)

    request_type = result["parsed_request_type"].request_type
    
    if request_type == "order":
        filtered_orders = result["filtered_orders"]
        if not filtered_orders:
            return {"Error": "Order not found."}
        else:
            output = {"orders": [order.model_dump(exclude={'tech_count, accessory_count, audio_count, homegoods_count'}) for order in filtered_orders]}
            return output
    elif request_type == "prediction":
        prediction_result = result["prediction_result"]
        if not prediction_result:
            return {"Error": "Prediction failed."}
        else:
            return {"predicted_total": round(float(prediction_result[0]), 2)}
    else:
        return {"Error": "Invalid Request!"}
    