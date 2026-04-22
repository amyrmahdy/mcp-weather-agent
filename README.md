# MCP Weather Agent

A FastAPI-based agentic system that uses the Model Context Protocol (MCP) to provide weather information through LLM tool calling.

## Architecture

- **MCP Server** (`src/mcp_server/server.py`): Exposes `get_current_weather` tool using `wttr.in` API
- **Agent Layer** (`src/agent/main.py`): FastAPI app that orchestrates LLM + MCP server communication
- **LLM Provider**: OpenRouter (OpenAI-compatible API)

## Setup

```bash
uv sync
```

# Set API key

```bash
export OPENROUTER_API_KEY="your_key_here"
```


# Run agent

```bash
uv run uvicorn src.agent.main:app --reload
```


## Testing MCP Server Standalone

Use the official MCP Inspector to test the server directly:

```bash
npx @modelcontextprotocol/inspector uv run python src/mcp_server/server.py
```

This opens a web UI where you can:
1. See available tools (`get_current_weather`)
2. Call the tool with test inputs (e.g., `{"city": "London"}`)
3. Inspect raw MCP protocol messages

**Note**: Increase timeout in Inspector settings if `wttr.in` is slow.

## Testing Agent API

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Paris?"}'
```

## What We Built

1. **MCP Server**: Implements MCP protocol over stdio, registers weather tool, fetches data from `wttr.in`
2. **Agent Loop**: FastAPI endpoint that:
   - Spawns MCP server as subprocess
   - Converts MCP tools to OpenAI function calling format
   - Sends user query + tools to LLM
   - Executes tool via MCP if LLM requests it
   - Returns final natural language response
3. **Dependencies**: Managed with `uv` for reproducibility

## Branch Strategy

- `main`: Stable releases
- `dev`: Integration branch
- `feat/*`: Feature branches (e.g., `feat/mcp-server`, `feat/agent-layer`)
