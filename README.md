# Raft Customer Order Agent

A LangGraph-based extraction agent that translates natural-language queries into structured order data. Given a natural-language request (e.g. “Show me all orders where the buyer was located in Ohio and total value was over 500.”), the agent calls a customer API to fetch raw data, structures and parses it into typed objects, and returns a clean JSON output.

## Quick start

**Prerequisites:** Python 3.10+, an OpenRouter API key.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# 3. Start the dummy customer API in one terminal
python dummy_customer_api.py

# 4. Run the agent in another terminal
python main.py
```

## Architecture

```
┌─────────┐
│  START  │  user query: "orders in Ohio over $500"
└────┬────┘
     │
     ▼
┌───────────────────────┐
│ parse_request_filters │   LLM → RequestFilters schema
└──────────┬────────────┘   (state, min_total, max_total, etc.)
           │
           ▼
┌───────────────────────┐
│      get_orders       │   HTTP GET /api/orders
└──────────┬────────────┘   (timeout + error handling)
           │
           ▼
┌───────────────────────┐
│     parse_orders      │   LLM per-order → Order schema
└──────────┬────────────┘ 
           │
           ▼
┌───────────────────────┐
│     filter_orders     │   Pure Python, deterministic
└──────────┬────────────┘   
           │
           ▼
     { "orders": [...] }    JSON Output
           │
           ▼
        ┌─────┐
        │ END │
        └─────┘
```

The agent is built as a LangGraph state machine with four nodes. Each node has a single responsibility and writes to a shared `AgentState` Pydantic model.


## File structure

```
├── main.py                    # LangGraph agent + entry point
├── dummy_customer_api.py      # Provided by Raft (not modified)
├── requirements.txt
└── README.md
```

---

## Tech stack

- LangGraph for agent orchestration (state machine with typed nodes)
- LangChain (ChatOpenAI) for the OpenRouter-compatible LLM interface
- Pydantic for schema definition and validation
- Python's requests for the HTTP client
- python-dotenv for environment variable management

Model: openai/gpt-oss-120b:exacto