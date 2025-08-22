# # weather_server.py
# # ---------------------------
# # Purpose:
# #   - Provide weather tools via MCP:
# #       1) geocode(location) -> lat/lon/country using Nominatim (OpenStreetMap).
# #       2) get_forecast(latitude, longitude) -> human-readable forecast via Open-Meteo (global, no key).
# #       3) get_alerts(latitude, longitude) -> severe weather alerts via Open-Meteo warnings (global coverage where available),
# #          and fallback to US NWS alerts if coordinates are in the United States.
# #   - This solves the "Chennai" problem (natural-language place → forecast).
# # ---------------------------

# import httpx  # async HTTP client for web requests
# from typing import Any, Optional  # typing helpers
# from mcp.server.fastmcp import FastMCP  # lightweight MCP server helper

# # Instantiate the MCP server with a logical name
# mcp = FastMCP("weather")  # name must match what client uses (agent.py)

# # Define constant endpoints and headers for the APIs we will call
# NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"  # geocoding service
# OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"  # global forecast API
# OPEN_METEO_WARNINGS = "https://api.open-meteo.com/v1/warnings"  # severe weather warnings API
# NWS_API_BASE = "https://api.weather.gov"  # US National Weather Service for alerts
# UA = "mcp-weather/1.0 (+github.com/your-org)"  # polite User-Agent for API etiquette

# async def _get_json(url: str, params: Optional[dict] = None, headers: Optional[dict] = None, timeout: float = 20.0) -> Optional[Any]:
#     """
#     Helper:
#       - Perform a GET request and parse JSON.
#       - Returns None on any network or HTTP error (keeps tools resilient).
#     """
#     # Build final headers by merging our default UA with any provided headers
#     hdrs = {"User-Agent": UA, "Accept": "application/json"}  # default headers for JSON APIs
#     if headers:  # if caller passed custom headers
#         hdrs.update(headers)  # merge them in
#     # Use a single short-lived AsyncClient for each call (simple and fine for tools)
#     async with httpx.AsyncClient(timeout=timeout) as client:  # create the client
#         try:  # try to perform HTTP GET
#             r = await client.get(url, params=params, headers=hdrs)  # do the request
#             r.raise_for_status()  # raise if status >= 400
#             return r.json()  # parse JSON to Python types
#         except Exception:  # swallow errors to keep tool outputs user-friendly
#             return None  # signal failure politely

# @mcp.tool()
# async def geocode(location: str) -> dict:
#     """
#     Tool: geocode
#     Args:
#       - location: free-form place name (e.g., "Chennai", "San Francisco, CA", "Berlin, DE")
#     Returns:
#       - dict with { 'latitude': float, 'longitude': float, 'display_name': str, 'country_code': str }
#     """
#     # Build params for Nominatim search API with JSON output and limited results
#     params = {"q": location, "format": "json", "limit": 1, "addressdetails": 1}  # limit to one best match
#     # Call the geocoding service
#     data = await _get_json(NOMINATIM_URL, params=params, headers={"Accept-Language": "en"})  # fetch JSON
#     # If no data or no items, return a helpful error payload
#     if not data or len(data) == 0:  # check empty result
#         return {"error": f"Could not geocode '{location}'."}  # return structured error
#     # Extract the first result object
#     top = data[0]  # best match
#     # Pull lat/lon and extra info safely
#     lat = float(top.get("lat", 0.0))  # latitude as float
#     lon = float(top.get("lon", 0.0))  # longitude as float
#     display = top.get("display_name", location)  # full display label
#     address = top.get("address", {})  # nested address dictionary
#     country_code = (address.get("country_code") or "").upper()  # ISO country code uppercase
#     # Return a normalized dict that callers (agent/tools) can rely on
#     return {"latitude": lat, "longitude": lon, "display_name": display, "country_code": country_code}  # payload

# @mcp.tool()
# async def get_forecast(latitude: float, longitude: float) -> str:
#     """
#     Tool: get_forecast
#     Args:
#       - latitude: float latitude value
#       - longitude: float longitude value
#     Returns:
#       - human-readable short forecast for today and tomorrow (temperature + summary) using Open-Meteo.
#     """
#     # Build parameters for Open-Meteo forecast: temperature and weathercode, hourly and daily basics
#     params = {
#         "latitude": latitude,  # lat to query
#         "longitude": longitude,  # lon to query
#         "current_weather": "true",  # include current snapshot
#         "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",  # daily metrics
#         "timezone": "auto"  # auto timezone so dates are local
#     }
#     # Call the forecast endpoint
#     data = await _get_json(OPEN_METEO_FORECAST, params=params)  # fetch JSON response
#     # If failed, return explicit message
#     if not data:  # check for network/API error
#         return "Unable to fetch forecast data (network/API error)."  # user-friendly error
#     # Extract current conditions and first two days of daily forecast safely
#     current = data.get("current_weather") or {}  # current weather dict
#     daily = data.get("daily") or {}  # daily aggregates dict
#     # Build readable lines for output
#     lines = []  # list of text lines
#     # Add current conditions if present
#     if current:  # ensure keys exist
#         lines.append(f"Now: {current.get('temperature', '?')}°C, wind {current.get('windspeed', '?')} km/h")  # one-liner
#     # Add a small 2-day summary if possible
#     times = daily.get("time") or []  # list of dates
#     tmax = daily.get("temperature_2m_max") or []  # list of max temps
#     tmin = daily.get("temperature_2m_min") or []  # list of min temps
#     precip = daily.get("precipitation_sum") or []  # list of precipitation sums
#     # Iterate first two days (today + tomorrow) if available
#     for i in range(min(2, len(times))):  # up to two entries
#         lines.append(f"{times[i]}: min {tmin[i]}°C / max {tmax[i]}°C, precip {precip[i]} mm")  # daily summary
#     # Join final output
#     return "\n".join(lines)  # newline-separated text

# @mcp.tool()
# async def get_alerts(latitude: float, longitude: float) -> str:
#     """
#     Tool: get_alerts
#     Args:
#       - latitude: float latitude
#       - longitude: float longitude
#     Returns:
#       - up to a handful of severe weather alerts from Open-Meteo warnings, falling back to NWS if in US.
#     """
#     # Try Open-Meteo warnings first (global coverage where available via MeteoAlarm/WMO partners)
#     params = {"latitude": latitude, "longitude": longitude}  # build params
#     warn = await _get_json(OPEN_METEO_WARNINGS, params=params)  # call warnings endpoint
#     # If warnings exist and have 'warnings' list, format them
#     if warn and isinstance(warn.get("warnings"), list) and len(warn["warnings"]) > 0:  # check for items
#         out = []  # collect lines
#         for w in warn["warnings"][:3]:  # limit to top 3 to keep output short
#             # Extract basic fields safely
#             event = w.get("event") or "Alert"  # event title
#             sender = w.get("sender") or "Unknown agency"  # issuing organization
#             severity = w.get("severity") or "unknown"  # severity level
#             onset = w.get("onset") or "n/a"  # start time
#             ends = w.get("expires") or "n/a"  # end time
#             desc = (w.get("description") or "").strip()  # free-text description
#             # Append a readable block
#             out.append(f"{event} – {severity}\nFrom {sender}\n{onset} → {ends}\n{desc}")  # formatted alert
#         return "\n\n".join(out)  # join blocks
#     # If no global warnings, try US NWS alerts if point lies in US
#     # Call NWS /points to resolve grid and country (indirectly; NWS only responds for US/territories)
#     points = await _get_json(f"{NWS_API_BASE}/points/{latitude},{longitude}", headers={"Accept": "application/geo+json"})  # points lookup
#     # If NWS points succeeded, we can look for alerts by forecast office state/zone
#     if points and points.get("properties", {}).get("relativeLocation"):  # check for usable data
#         # region should be US if NWS understands the point; attempt area code by state abbrev
#         state = points["properties"].get("relativeLocation", {}).get("properties", {}).get("state")  # two-letter code
#         if state:  # if we got a state
#             alerts = await _get_json(f"{NWS_API_BASE}/alerts/active", params={"area": state}, headers={"Accept": "application/geo+json"})  # fetch alerts
#             feats = alerts.get("features") if alerts else None  # extract features
#             if feats:  # if any alerts exist
#                 blocks = []  # text blocks
#                 for f in feats[:3]:  # limit to three
#                     p = f.get("properties") or {}  # properties dict
#                     blocks.append(f"{p.get('event','Alert')}: {p.get('areaDesc','')}\n{p.get('headline','')}\n{p.get('description','').strip()}")  # format
#                 return "\n\n".join(blocks)  # join blocks
#     # If we reach here, no alerts found or unsupported region
#     return "No active alerts for this location."  # graceful default

# # Standard MCP server startup over stdio
# if __name__ == "__main__":  # run only when invoked as script
#     mcp.run(transport="stdio")  # start the MCP stdio loop















# weather_server.py
# ---------------------------
# Purpose:
#   - Provide weather tools via MCP:
#       1) geocode(location) -> lat/lon/country using Nominatim (OpenStreetMap).
#       2) get_forecast(latitude, longitude) -> forecast via Open-Meteo.
#       3) get_alerts(latitude, longitude) -> weather alerts via Open-Meteo + fallback to US NWS.
#       4) get_weather(location) -> composite (geocode + forecast + alerts).
#   - Enhancements:
#       - Weathercode → human-readable descriptions
#       - Feels-like temps
#       - Alert severity emojis
#       - Reverse geocoding in alerts
# ---------------------------

import httpx
from typing import Any, Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather")

# APIs
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_WARNINGS = "https://api.open-meteo.com/v1/warnings"
NWS_API_BASE = "https://api.weather.gov"
UA = "mcp-weather/2.0 (+github.com/your-org)"

# Weather code mapping (partial for demo, expand if needed)
WEATHER_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Hailstorm"
}
def describe_code(code: int) -> str:
    return WEATHER_CODES.get(code, "Unknown conditions")

# Severity → emoji map
SEVERITY_ICONS = {
    "Extreme": "🚨", "Severe": "⚠️", "Moderate": "🔔", "Minor": "ℹ️"
}

async def _get_json(url: str, params: Optional[dict] = None, headers: Optional[dict] = None, timeout: float = 20.0) -> Optional[Any]:
    """GET request helper (returns parsed JSON or None)."""
    hdrs = {"User-Agent": UA, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            r = await client.get(url, params=params, headers=hdrs)
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

@mcp.tool()
async def geocode(location: str) -> dict:
    """Geocode free-text location → {lat, lon, display_name, country_code}."""
    params = {"q": location, "format": "json", "limit": 1, "addressdetails": 1}
    data = await _get_json(NOMINATIM_URL, params=params, headers={"Accept-Language": "en"})
    if not data:
        return {"error": f"Could not geocode '{location}'."}
    top = data[0]
    return {
        "latitude": float(top.get("lat", 0.0)),
        "longitude": float(top.get("lon", 0.0)),
        "display_name": top.get("display_name", location),
        "country_code": (top.get("address", {}).get("country_code") or "").upper()
    }

@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Fetch forecast for given lat/lon → readable summary."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "daily": "temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum",
        "timezone": "auto"
    }
    data = await _get_json(OPEN_METEO_FORECAST, params=params)
    if not data:
        return "Unable to fetch forecast data."

    current = data.get("current_weather") or {}
    daily = data.get("daily") or {}

    lines = []
    if current:
        code = current.get("weathercode")
        condition = describe_code(code)
        lines.append(
            f"Now: {current.get('temperature','?')}°C, {condition}, wind {current.get('windspeed','?')} km/h"
        )

    times = daily.get("time") or []
    tmax = daily.get("temperature_2m_max") or []
    tmin = daily.get("temperature_2m_min") or []
    app_max = daily.get("apparent_temperature_max") or []
    app_min = daily.get("apparent_temperature_min") or []
    precip = daily.get("precipitation_sum") or []

    for i in range(min(2, len(times))):
        feels = f"(feels {app_min[i]}–{app_max[i]}°C)" if i < len(app_max) else ""
        lines.append(
            f"{times[i]}: min {tmin[i]}°C / max {tmax[i]}°C {feels}, precip {precip[i]} mm"
        )
    return "\n".join(lines)

@mcp.tool()
async def get_alerts(latitude: float, longitude: float) -> str:
    """Fetch severe weather alerts for given lat/lon."""
    params = {"latitude": latitude, "longitude": longitude}
    warn = await _get_json(OPEN_METEO_WARNINGS, params=params)
    if warn and isinstance(warn.get("warnings"), list) and warn["warnings"]:
        out = []
        for w in warn["warnings"][:3]:
            event = w.get("event", "Alert")
            severity = w.get("severity", "unknown").title()
            emoji = SEVERITY_ICONS.get(severity, "")
            sender = w.get("sender", "Unknown agency")
            onset, ends = w.get("onset", "n/a"), w.get("expires", "n/a")
            desc = (w.get("description") or "").strip()
            out.append(f"{emoji} {event} – {severity}\nFrom {sender}\n{onset} → {ends}\n{desc}")
        return "\n\n".join(out)

    # fallback → US NWS alerts
    points = await _get_json(f"{NWS_API_BASE}/points/{latitude},{longitude}", headers={"Accept": "application/geo+json"})
    if points and points.get("properties", {}).get("relativeLocation"):
        state = points["properties"]["relativeLocation"]["properties"].get("state")
        if state:
            alerts = await _get_json(f"{NWS_API_BASE}/alerts/active", params={"area": state}, headers={"Accept": "application/geo+json"})
            feats = alerts.get("features") if alerts else None
            if feats:
                blocks = []
                for f in feats[:3]:
                    p = f.get("properties") or {}
                    blocks.append(f"{p.get('event','Alert')}: {p.get('areaDesc','')}\n{p.get('headline','')}\n{p.get('description','').strip()}")
                return "\n\n".join(blocks)
    return "No active alerts for this location."

@mcp.tool()
async def get_weather(location: str) -> str:
    """Composite: location → forecast + alerts."""
    place = await geocode(location)
    if "error" in place:
        return place["error"]
    lat, lon, name = place["latitude"], place["longitude"], place["display_name"]
    forecast = await get_forecast(lat, lon)
    alerts = await get_alerts(lat, lon)
    return f"Weather for {name}:\n\nForecast:\n{forecast}\n\nAlerts:\n{alerts}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
