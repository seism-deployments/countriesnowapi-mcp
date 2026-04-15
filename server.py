from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse
import uvicorn
from fastmcp import FastMCP
import httpx
import os
from typing import Optional

mcp = FastMCP("CountriesNow API")

BASE_URL = "https://countriesnow.space/api/v0.1/countries"


@mcp.tool()
async def get_countries() -> dict:
    """Retrieve a list of all countries with their cities. Use this as a starting point when the user needs a full list of countries or wants to explore available country data. Returns country names paired with their city lists."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_country_cities(country: str) -> dict:
    """Retrieve all cities for a specific country. Use this when the user wants to know what cities exist within a particular country. Accepts a country name and returns its cities.

    Args:
        country: The name of the country to retrieve cities for (e.g., 'Nigeria', 'Canada', 'Germany').
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/cities",
            json={"country": country}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_country_states(country: str) -> dict:
    """Retrieve all states or provinces for a specific country. Use this when the user needs administrative subdivisions (states, provinces, regions) of a country.

    Args:
        country: The name of the country to retrieve states for (e.g., 'United States', 'Brazil', 'India').
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/states",
            json={"country": country}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_state_cities(country: str, state: str) -> dict:
    """Retrieve all cities within a specific state of a given country. Use this when the user needs city-level data scoped to a particular state or province.

    Args:
        country: The name of the country the state belongs to (e.g., 'United States').
        state: The name of the state or province to retrieve cities for (e.g., 'California', 'Ontario').
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/state/cities",
            json={"country": country, "state": state}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_country_capital(country: str) -> dict:
    """Retrieve the capital city of a specific country. Use this when the user asks about the capital of a country or needs capital city information for geographic or educational purposes.

    Args:
        country: The name of the country whose capital is being requested (e.g., 'France', 'Japan', 'Brazil').
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/capital",
            json={"country": country}
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_country_dial_codes(country: Optional[str] = None) -> dict:
    """Retrieve international dialing codes (phone country codes) for countries. Use this when the user needs to know the dial code or phone prefix for one or more countries.

    Args:
        country: Optional country name to filter results to a specific country (e.g., 'Ghana'). If omitted, returns dial codes for all countries.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        if country:
            response = await client.post(
                f"{BASE_URL}/codes",
                json={"country": country}
            )
        else:
            response = await client.get(f"{BASE_URL}/codes")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_country_currency(country: Optional[str] = None) -> dict:
    """Retrieve currency information for a specific country or all countries. Use this when the user asks about what currency a country uses, currency codes, or currency symbols.

    Args:
        country: Optional country name to filter to a specific country's currency (e.g., 'Japan'). If omitted, returns currency data for all countries.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        if country:
            response = await client.post(
                f"{BASE_URL}/currency",
                json={"country": country}
            )
        else:
            response = await client.get(f"{BASE_URL}/currency")
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def get_country_flag(country: str) -> dict:
    """Retrieve the flag image URL or unicode for a specific country. Use this when the user wants to display or reference a country's flag in an application or for informational purposes.

    Args:
        country: The name of the country whose flag is being requested (e.g., 'Canada', 'Australia', 'Kenya').
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/flag/images",
            json={"country": country}
        )
        response.raise_for_status()
        return response.json()




async def health(request):
    return JSONResponse({"status": "ok", "server": mcp.name})

async def tools(request):
    registered = await mcp.list_tools()
    tool_list = [{"name": t.name, "description": t.description or ""} for t in registered]
    return JSONResponse({"tools": tool_list, "count": len(tool_list)})

mcp_app = mcp.http_app(transport="streamable-http")

class _FixAcceptHeader:
    """Ensure Accept header includes both types FastMCP requires."""
    def __init__(self, app):
        self.app = app
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            accept = headers.get(b"accept", b"").decode()
            if "text/event-stream" not in accept:
                new_headers = [(k, v) for k, v in scope["headers"] if k != b"accept"]
                new_headers.append((b"accept", b"application/json, text/event-stream"))
                scope = dict(scope, headers=new_headers)
        await self.app(scope, receive, send)

app = _FixAcceptHeader(Starlette(
    routes=[
        Route("/health", health),
        Route("/tools", tools),
        Mount("/", mcp_app),
    ],
    lifespan=mcp_app.lifespan,
))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
