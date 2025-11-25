# mcp_client.py
import asyncio
import json
import logging
from typing import Any, Dict

import aiohttp
import websockets

logging.basicConfig(level=logging.INFO)
LITELLM_URL = "http://localhost:8080/v1/chat/completions"   # LiteLLM proxy OpenAI-compatible endpoint
MCP_WS_URL = "wss://your-mcp-server.example.com/ws"          # replace with your MCP server
API_KEY = "your_mcp_client_api_key"                         # if needed for MCP auth

async def call_litellm(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call LiteLLM proxy using OpenAI-style endpoint (synchronous response)."""
    async with aiohttp.ClientSession() as session:
        async with session.post(LITELLM_URL, json=payload, timeout=60) as resp:
            resp.raise_for_status()
            return await resp.json()

async def handle_tool_call(ws, msg: Dict[str, Any]):
    call_id = msg.get("id")
    tool = msg.get("tool")
    user_input = msg.get("input", {})

    logging.info("Tool call %s for tool=%s", call_id, tool)

    # Map MCP tool -> model prompt (adapt to your protocol)
    prompt = user_input.get("prompt") or user_input.get("text") or " "
    litellm_payload = {
        "model": "gpt-4o-mini",           # or your configured model alias
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 512,
        # add other litellm/openai-compatible params (temperature, stream, etc.)
    }

    try:
        result = await call_litellm(litellm_payload)
        # Extract text (OpenAI-compatible shape)
        text = result["choices"][0]["message"]["content"]
        response_msg = {"type": "tool_result", "id": call_id, "result": {"text": text}}
    except Exception as e:
        logging.exception("Error during tool call")
        response_msg = {"type": "tool_result", "id": call_id, "error": str(e)}

    await ws.send(json.dumps(response_msg))

async def mcp_event_loop():
    async with websockets.connect(MCP_WS_URL, extra_headers={"Authorization": f"Bearer {API_KEY}"}) as ws:
        # register / hello if protocol requires it
        await ws.send(json.dumps({"type": "register_client", "name": "my-litellm-mcp-client"}))

        async for raw in ws:
            msg = json.loads(raw)
            typ = msg.get("type")
            if typ == "tool_call":
                # spawn a task so we can continue to listen
                asyncio.create_task(handle_tool_call(ws, msg))
            else:
                logging.info("Unhandled MCP message: %s", msg)

if __name__ == "__main__":
    asyncio.run(mcp_event_loop())
