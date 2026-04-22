from fastapi import FastAPI
from pydantic import BaseModel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import openai
import os
import json

# MODEL_NAME = "google/gemma-4-26b-a4b-it:free"
MODEL_NAME =  "openai/gpt-oss-20b:free"
# MODEL_NAME = "meta-llama/llama-3.3-70b-instruct:free"

app = FastAPI()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)


class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str


@app.get("/health")
async def check_health():
    return {"status": "ok"}


@app.post("/query")
async def query_agent(request: QueryRequest) -> QueryResponse:
    server_params = StdioServerParameters(
        command="uv",
        args=["run","python", "src/mcp_server/server.py"]
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            tools_list = result.tools

            print(f"[DEBUG] Found {len(tools_list)} tools from MCP server")

            toolbox = []
            for the_tool in tools_list:
                openai_tool = {
                    "type": "function",
                    "function": {
                        "name": the_tool.name,
                        "description": the_tool.description,
                        "parameters": the_tool.inputSchema
                    }
                }
                toolbox.append(openai_tool)

            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": request.query}],
                tools=toolbox
            )

            print(f"[DEBUG] LLM response: {response}")

            llm_answer = response.choices[0].message

            if not llm_answer.tool_calls:
                return QueryResponse(response=llm_answer.content or "No response")

            tool_call = llm_answer.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            print(f"[DEBUG] Calling tool '{tool_name}' with args: {tool_args}")

            result = await session.call_tool(tool_name, tool_args)
            tool_result = result.content[0].text

            print(f"[DEBUG] Tool result: {tool_result}")

            final_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "user", "content": request.query},
                    {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                        ]
                    },
                    {"role": "tool", "tool_call_id": tool_call.id, "content": tool_result}
                ]
            )

            print(f"[DEBUG] Final LLM response: {final_response}")

            return QueryResponse(response=final_response.choices[0].message.content)















