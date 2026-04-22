import asyncio

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx

server = Server("mcp-weather-agent")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_current_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_current_weather":
        city = arguments["city"]
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(f"https://wttr.in/{city}?format=j1")
            current_condition = response.json()["current_condition"][0]
            temperature = current_condition["temp_C"]
            description = current_condition["weatherDesc"][0]["value"]

        return [TextContent(
            type="text",
            text=f"Temperature in {city} is {temperature}°C, {description}"
        )]

    raise ValueError(f"Unknown tool {name}")

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())












