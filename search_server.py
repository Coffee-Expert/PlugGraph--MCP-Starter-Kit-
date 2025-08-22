# search_server.py
# ---------------------------
# Purpose:
#   - Provide a simple live web search tool the agent can call.
#   - Uses DuckDuckGo Instant Answer API for lightweight JSON results.
#   - NOTE: This is not a full web browser; it's enough to fetch snippets and links.
# ---------------------------

import httpx  # async HTTP client
from typing import Optional, List  # typing
from mcp.server.fastmcp import FastMCP  # MCP server

# Instantiate MCP server
mcp = FastMCP("search")  # logical server name

# Simple JSON helper
async def _get_json(url: str, params: Optional[dict] = None) -> Optional[dict]:
    """
    Helper to GET JSON with modest error handling.
    """
    async with httpx.AsyncClient(timeout=15) as client:  # client
        try:  # attempt request
            r = await client.get(url, params=params)  # GET
            r.raise_for_status()  # raise on 4xx/5xx
            return r.json()  # parse JSON
        except Exception:  # swallow errors
            return None  # failure

@mcp.tool()
async def web_search(query: str) -> List[dict]:
    """
    Tool: web_search
    Args:
      - query: search string
    Returns:
      - A small list of {title, url, abstract} items to reference in answers.
    """
    # DuckDuckGo Instant Answer API (does not require API key)
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}  # practical params
    data = await _get_json("https://api.duckduckgo.com/", params=params)  # call API
    if not data:  # handle failure
        return []  # empty list
    # Try to harvest items from RelatedTopics; sometimes 'Abstract' is present at top-level
    out = []  # results list
    # include top-level abstract if meaningful
    abstract = data.get("AbstractText") or ""  # abstract text
    abstract_url = data.get("AbstractURL") or ""  # source URL
    heading = data.get("Heading") or ""  # title
    if abstract and abstract_url:  # if present
        out.append({"title": heading or "Result", "url": abstract_url, "abstract": abstract})  # add item
    # parse related topics for more links
    for item in data.get("RelatedTopics", []):  # iterate related topics
        # items may be either a dict or a dict group with subtopics
        if "Text" in item and "FirstURL" in item:  # single item shape
            out.append({"title": item.get("Text", "").split(" - ")[0], "url": item.get("FirstURL"), "abstract": item.get("Text")})
        elif "Topics" in item:  # group shape
            for sub in item["Topics"][:3]:  # sample a few to limit verbosity
                out.append({"title": sub.get("Text","").split(" - ")[0], "url": sub.get("FirstURL"), "abstract": sub.get("Text")})
        # Limit total to keep outputs readable
        if len(out) >= 5:  # cap results
            break  # stop once we have enough
    # Return compact list
    return out  # list of dicts

# Start MCP stdio loop
if __name__ == "__main__":  # entrypoint
    mcp.run(transport="stdio")  # run server
