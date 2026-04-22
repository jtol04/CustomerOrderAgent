# Customer Order Agent

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

## Testing the Agent
```bash
# Filter by state and price (combined filters)
> Show me all orders in Ohio over $500
# Filter by buyer name
> Show me orders from Rachel Kim
# Filter by item
> Which orders have a laptop?
# Single order lookup
> Show me order 1001
# Limit results
> Show me 2 orders
```

## Architecture

```
![My Image](architecture)
```

The agent is built as a LangGraph state machine with four nodes. Each node has a single responsibility and writes to a shared `AgentState` Pydantic model.


## File structure

```
├── main.py                    # LangGraph agent + entry point
├── dummy_customer_api.py      # Provided by Raft (not modified)
├── requirements.txt           # requirements for running the agent
├── .env.example                       
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