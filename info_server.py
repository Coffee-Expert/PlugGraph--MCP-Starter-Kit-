# info_server.py
# ---------------------------
# Purpose:
#   - Provide informational tools:
#       1) search_universities(country, name?) -> list basic matches (Hipolabs Universities API).
#       2) country_info(query) -> basic country facts (REST Countries).
#       3) image_of(query) -> first image URL from Wikipedia/Wikimedia.
# ---------------------------

import httpx  # async HTTP client
from typing import Optional, List  # typing helpers
from mcp.server.fastmcp import FastMCP  # MCP server helper

# Instantiate the MCP server
mcp = FastMCP("info")  # server name

# Generic JSON helper
async def _get_json(url: str, params: Optional[dict] = None, headers: Optional[dict] = None, timeout: float = 20.0):
    """
    Helper to GET JSON with basic error handling and optional headers.
    """
    hdrs = {"User-Agent": "mcp-info/1.0"}  # polite UA
    if headers:  # merge any custom headers
        hdrs.update(headers)  # update dict
    async with httpx.AsyncClient(timeout=timeout) as client:  # client
        try:  # request
            r = await client.get(url, params=params, headers=hdrs)  # GET
            r.raise_for_status()  # error on 4xx/5xx
            return r.json()  # parse JSON
        except Exception:  # swallow errors
            return None  # indicate failure

@mcp.tool()
async def search_universities(country: str, name: str = "") -> List[dict]:
    """
    Tool: search_universities
    Args:
      - country: country name (e.g., "India")
      - name: optional partial university name filter
    Returns:
      - list of dicts with {name, country, web_pages[0]} truncated to top few results
    """
    params = {"country": country}  # mandatory param
    if name:  # if filter present
        params["name"] = name  # add name filter
    data = await _get_json("http://universities.hipolabs.com/search", params=params)  # call API
    if not data or not isinstance(data, list):  # validate
        return []  # empty list on failure
    # Return top 5 simplified entries
    res = []  # output list
    for uni in data[:5]:  # first five results
        res.append({
            "name": uni.get("name"),
            "country": uni.get("country"),
            "website": (uni.get("web_pages") or [""])[0]
        })  # keep compact
    return res  # return list

@mcp.tool()
async def country_info(query: str) -> dict:
    """
    Tool: country_info
    Args:
      - query: country name (e.g., "Japan")
    Returns:
      - basic facts: official name, capital, population, region, currencies, languages.
    """
    data = await _get_json(f"https://restcountries.com/v3.1/name/{query}", params={"fullText": "false"})  # call API
    if not data or not isinstance(data, list):  # validate
        return {"error": "Country not found."}  # error payload
    c = data[0]  # take first match
    # Build a compact dict of interesting facts
    return {
        "name": (c.get("name") or {}).get("official"),
        "capital": (c.get("capital") or ["N/A"])[0],
        "population": c.get("population"),
        "region": c.get("region"),
        "currencies": list((c.get("currencies") or {}).keys()),
        "languages": list((c.get("languages") or {}).values())
    }  # summary

@mcp.tool()
async def image_of(query: str) -> str:
    """
    Tool: image_of
    Args:
      - query: thing/person/place to search on Wikipedia/Wikimedia
    Returns:
      - A single best-effort image URL (thumbnail) or a message if not found.
    """
    # First, use Wikipedia search API to get a page ID for the query
    search = await _get_json(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "list": "search", "srsearch": query, "format": "json"}  # search params
    )  # call API
    if not search or not search.get("query", {}).get("search"):  # no results
        return "No image found."  # fallback
    page_title = search["query"]["search"][0]["title"]  # top page title
    # Then, request page image (thumbnail) via another API call
    page = await _get_json(
        "https://en.wikipedia.org/w/api.php",
        params={
            "action": "query",
            "prop": "pageimages",
            "piprop": "thumbnail",
            "pithumbsize": 600,
            "titles": page_title,
            "format": "json"
        }  # image params
    )  # call API
    # Parse the thumbnail URL from the response
    pages = (page or {}).get("query", {}).get("pages", {})  # pages dict keyed by pageid
    for _, v in pages.items():  # iterate pages
        thumb = v.get("thumbnail", {})  # thumb dict
        if "source" in thumb:  # if URL exists
            return thumb["source"]  # return image URL
    # If no thumbnail found, say so
    return "No image found."  # fallback

# Start MCP server
if __name__ == "__main__":  # entrypoint guard
    mcp.run(transport="stdio")  # run stdio loop
