# fun_server.py
# ---------------------------
# Purpose:
#   - Provide lighthearted tools:
#       1) get_quote() -> random motivational quote (ZenQuotes).
#       2) get_joke() -> random joke (Official Joke API).
#       3) get_activity() -> random activity (Bored API).
# ---------------------------

import httpx  # async HTTP client
from typing import Optional  # typing helper
from mcp.server.fastmcp import FastMCP  # MCP server

# Instantiate the MCP server with a logical name
mcp = FastMCP("fun")  # server name used by the client

# Helper to fetch JSON with basic error handling
async def _get_json(url: str, params: Optional[dict] = None) -> Optional[dict | list]:
    """
    Helper to GET JSON with simple error handling.
    """
    async with httpx.AsyncClient(timeout=15) as client:  # create client
        try:  # attempt GET
            r = await client.get(url, params=params)  # perform request
            r.raise_for_status()  # raise HTTPError on 4xx/5xx
            return r.json()  # parse JSON
        except Exception:  # swallow network/API errors
            return None  # signal failure

@mcp.tool()
async def get_quote() -> str:
    """
    Tool: get_quote
    Returns:
      - A short quote and author if available.
    """
    data = await _get_json("https://zenquotes.io/api/random")  # call ZenQuotes
    if not data or not isinstance(data, list):  # validate response shape
        return "Could not fetch a quote right now."  # fallback
    q = data[0]  # first item
    return f"“{q.get('q','...')}” — {q.get('a','Unknown')}"  # format nicely

@mcp.tool()
async def get_joke() -> str:
    """
    Tool: get_joke
    Returns:
      - A simple two-line joke setup + punchline.
    """
    data = await _get_json("https://official-joke-api.appspot.com/jokes/random")  # joke API
    if not data or not isinstance(data, dict):  # validate
        return "No jokes right now, sorry."  # fallback
    return f"{data.get('setup','...')}\n{data.get('punchline','')}"  # two lines

@mcp.tool()
async def get_activity() -> str:
    """
    Tool: get_activity
    Returns:
      - A random activity suggestion (from Bored API).
    """
    data = await _get_json("https://www.boredapi.com/api/activity")  # bored API
    if not data or not isinstance(data, dict):  # validate
        return "Couldn't find an activity right now."  # fallback
    return f"Try this: {data.get('activity','Something interesting')}"  # format

# Start MCP server
if __name__ == "__main__":  # only when run directly
    mcp.run(transport="stdio")  # run stdio loop
