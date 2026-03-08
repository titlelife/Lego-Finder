"""
FastAPI backend server for LEGO Minifigure Price Finder Mini App
Handles price search from BrickLink API and Avito scraping
"""

import os
import re
import json
import logging
import asyncio
import base64
from typing import Optional
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LEGO Price Finder API")

# CORS for Telegram WebApp
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
BRICKLINK_CONSUMER_KEY = os.getenv("BRICKLINK_CONSUMER_KEY", "")
BRICKLINK_CONSUMER_SECRET = os.getenv("BRICKLINK_CONSUMER_SECRET", "")
BRICKLINK_TOKEN = os.getenv("BRICKLINK_TOKEN", "")
BRICKLINK_TOKEN_SECRET = os.getenv("BRICKLINK_TOKEN_SECRET", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    language: str = "en"


class PriceResult(BaseModel):
    name: str
    item_id: Optional[str] = None
    bricklink_avg: Optional[float] = None
    bricklink_min: Optional[float] = None
    bricklink_max: Optional[float] = None
    bricklink_qty: Optional[int] = None
    avito_avg: Optional[float] = None
    avito_min: Optional[float] = None
    avito_max: Optional[float] = None
    avito_listings: Optional[int] = None
    image_url: Optional[str] = None
    currency: str = "USD"
    source_urls: dict = {}


# ─────────────────────────────────────────────
# BrickLink API integration
# ─────────────────────────────────────────────
async def search_bricklink(query: str) -> Optional[dict]:
    """
    Search BrickLink for minifigure prices using their OAuth1 API.
    Docs: https://www.bricklink.com/v3/api.page
    """
    try:
        # First search for items matching the query
        search_url = f"https://api.bricklink.com/api/store/v1/items/MINIFIG/{query.upper()}"
        
        # For demo: using BrickLink's public catalog search
        # In production, implement OAuth1 signing
        catalog_url = f"https://api.bricklink.com/api/store/v1/items/MINIFIG/{query}"
        
        headers = {
            "User-Agent": "LEGO-Price-Finder/1.0"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Search catalog
            resp = await client.get(
                f"https://www.bricklink.com/catalogSearchResult.asp",
                params={
                    "q": query,
                    "itemType": "M",  # M = Minifig
                    "sz": "10",
                },
                headers=headers
            )
            
            if resp.status_code == 200:
                # Parse basic results from HTML (simplified)
                # In production, use BrickLink OAuth API
                return await get_bricklink_price_guide(query)
    except Exception as e:
        logger.error(f"BrickLink search error: {e}")
    
    return None


async def get_bricklink_price_guide(item_no: str) -> Optional[dict]:
    """
    Get price guide for a specific minifigure from BrickLink.
    Uses BrickLink API v3 with OAuth1.
    
    In production, implement proper OAuth1 HMAC-SHA1 signing:
    https://www.bricklink.com/v3/api.page#/authentication
    """
    try:
        # Simulated response structure (replace with real OAuth API call)
        # Real endpoint: GET /api/store/v1/items/MINIFIG/{no}/price
        
        # For demo purposes, we'll use BrickLink's public price page
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(
                f"https://www.bricklink.com/v2/catalog/catalogitem.page",
                params={"M": item_no.upper()},
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if resp.status_code == 200:
                html = resp.text
                # Extract price data from HTML
                return parse_bricklink_html(html, item_no)
    except Exception as e:
        logger.error(f"BrickLink price guide error: {e}")
    
    return None


def parse_bricklink_html(html: str, item_no: str) -> dict:
    """Parse price data from BrickLink HTML page"""
    result = {
        "item_id": item_no.upper(),
        "name": item_no,
        "avg_price": None,
        "min_price": None,
        "max_price": None,
        "qty_sold": None,
        "image_url": f"https://img.bricklink.com/ItemImage/MN/0/{item_no.upper()}.png"
    }
    
    # Extract name
    name_match = re.search(r'<h1[^>]*class="[^"]*catalog-item-name[^"]*"[^>]*>([^<]+)</h1>', html)
    if name_match:
        result["name"] = name_match.group(1).strip()
    
    # Extract prices (simplified - real implementation would be more robust)
    price_match = re.search(r'Avg Price.*?\$(\d+\.?\d*)', html, re.DOTALL)
    if price_match:
        result["avg_price"] = float(price_match.group(1))
    
    return result


# ─────────────────────────────────────────────
# Avito search
# ─────────────────────────────────────────────
async def search_avito(query: str) -> Optional[dict]:
    """
    Search Avito for LEGO minifigure listings.
    Note: Avito requires proper API access for production use.
    Avito API: https://developers.avito.ru/
    """
    try:
        avito_api_token = os.getenv("AVITO_API_TOKEN", "")
        
        if avito_api_token:
            # Use official Avito API
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://api.avito.ru/core/v1/items",
                    params={
                        "query": f"LEGO минифигурка {query}",
                        "category_id": "43",  # Toys
                        "limit": 20
                    },
                    headers={
                        "Authorization": f"Bearer {avito_api_token}",
                        "User-Agent": "LEGO-Price-Finder/1.0"
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    return parse_avito_response(data)
        else:
            # Fallback: scrape public Avito search
            return await scrape_avito_prices(query)
            
    except Exception as e:
        logger.error(f"Avito search error: {e}")
    
    return None


async def scrape_avito_prices(query: str) -> Optional[dict]:
    """Scrape Avito public search results"""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(
                "https://www.avito.ru/rossiya",
                params={
                    "q": f"лего минифигурка {query}",
                    "cat": "43"
                },
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "ru-RU,ru;q=0.9",
                    "Accept": "text/html"
                }
            )
            
            if resp.status_code == 200:
                return parse_avito_html(resp.text)
    except Exception as e:
        logger.error(f"Avito scraping error: {e}")
    
    return None


def parse_avito_response(data: dict) -> dict:
    """Parse Avito API response"""
    items = data.get("items", [])
    if not items:
        return None
    
    prices = [item.get("price", 0) for item in items if item.get("price")]
    
    if not prices:
        return None
    
    return {
        "avg_price": sum(prices) / len(prices),
        "min_price": min(prices),
        "max_price": max(prices),
        "listings_count": len(items),
        "currency": "RUB"
    }


def parse_avito_html(html: str) -> Optional[dict]:
    """Parse prices from Avito HTML"""
    # Extract prices from JSON-LD or structured data
    prices = []
    
    price_pattern = re.findall(r'"price":\s*(\d+)', html)
    for p in price_pattern[:20]:
        try:
            prices.append(float(p))
        except:
            pass
    
    if not prices:
        return None
    
    # Filter reasonable LEGO prices (10 - 50000 RUB)
    prices = [p for p in prices if 10 <= p <= 50000]
    
    if not prices:
        return None
    
    return {
        "avg_price": round(sum(prices) / len(prices), 2),
        "min_price": min(prices),
        "max_price": max(prices),
        "listings_count": len(prices),
        "currency": "RUB"
    }


# ─────────────────────────────────────────────
# AI Photo Recognition via Claude API
# ─────────────────────────────────────────────
async def identify_minifigure(image_data: bytes, media_type: str = "image/jpeg") -> dict:
    """Use Claude API to identify LEGO minifigure from photo"""
    try:
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-opus-4-5",
                    "max_tokens": 1024,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_b64
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": """You are a LEGO minifigure expert. Analyze this image and identify the LEGO minifigure(s) shown.

Please provide a JSON response with:
{
  "identified": true/false,
  "name": "Full name of the minifigure",
  "set_number": "LEGO set number if known (e.g. sw0001 for BrickLink ID)",
  "theme": "LEGO theme (e.g. Star Wars, City, Harry Potter)",
  "year": "Year released if known",
  "description": "Brief description of the figure",
  "search_query": "Best search query to use on BrickLink",
  "confidence": "high/medium/low",
  "notes": "Any additional relevant information for collectors"
}

If multiple figures are shown, identify the most prominent one.
If no LEGO minifigure is visible, set identified to false."""
                                }
                            ]
                        }
                    ]
                }
            )
            
            if resp.status_code == 200:
                data = resp.json()
                text = data["content"][0]["text"]
                
                # Parse JSON from response
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                    
    except Exception as e:
        logger.error(f"AI identification error: {e}")
    
    return {
        "identified": False,
        "name": "Unknown",
        "description": "Could not identify the minifigure",
        "confidence": "low"
    }


# ─────────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────────
@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/search")
async def search_prices(request: SearchRequest):
    """Search prices for a LEGO minifigure"""
    query = request.query.strip()
    
    if not query or len(query) < 2:
        raise HTTPException(status_code=400, detail="Query too short")
    
    logger.info(f"Searching prices for: {query}")
    
    # Run both searches in parallel
    bricklink_task = search_bricklink(query)
    avito_task = search_avito(query)
    
    bricklink_data, avito_data = await asyncio.gather(
        bricklink_task, avito_task, return_exceptions=True
    )
    
    # Handle exceptions
    if isinstance(bricklink_data, Exception):
        logger.error(f"BrickLink error: {bricklink_data}")
        bricklink_data = None
    if isinstance(avito_data, Exception):
        logger.error(f"Avito error: {avito_data}")
        avito_data = None
    
    result = {
        "query": query,
        "name": query,
        "bricklink": None,
        "avito": None,
        "image_url": None,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if bricklink_data:
        result["name"] = bricklink_data.get("name", query)
        result["image_url"] = bricklink_data.get("image_url")
        result["bricklink"] = {
            "avg_price": bricklink_data.get("avg_price"),
            "min_price": bricklink_data.get("min_price"),
            "max_price": bricklink_data.get("max_price"),
            "qty_sold": bricklink_data.get("qty_sold"),
            "currency": "USD",
            "url": f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={query.upper()}"
        }
    
    if avito_data:
        result["avito"] = {
            "avg_price": avito_data.get("avg_price"),
            "min_price": avito_data.get("min_price"),
            "max_price": avito_data.get("max_price"),
            "listings_count": avito_data.get("listings_count"),
            "currency": "RUB",
            "url": f"https://www.avito.ru/rossiya?q=lego+{query}"
        }
    
    # If no real data, return demo data for testing
    if not bricklink_data and not avito_data:
        result = get_demo_data(query)
    
    return result


@app.post("/api/identify")
async def identify_from_photo(file: UploadFile = File(...)):
    """Identify minifigure from uploaded photo using AI"""
    
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    image_data = await file.read()
    
    if len(image_data) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="Image too large (max 10MB)")
    
    logger.info(f"Identifying minifigure from photo: {file.filename}")
    
    # Identify with AI
    identification = await identify_minifigure(image_data, file.content_type)
    
    result = {
        "identification": identification,
        "search_query": identification.get("search_query", identification.get("name", "")),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # If identified with confidence, also search prices
    if identification.get("identified") and identification.get("confidence") in ["high", "medium"]:
        search_query = identification.get("search_query", identification.get("name", ""))
        if search_query:
            prices = await search_prices(SearchRequest(query=search_query))
            result["prices"] = prices
    
    return result


def get_demo_data(query: str) -> dict:
    """Return demo data when APIs are not configured"""
    import random
    
    demo_figures = {
        "sw0001": {"name": "Luke Skywalker (Tatooine)", "theme": "Star Wars"},
        "hp001": {"name": "Harry Potter (Gryffindor)", "theme": "Harry Potter"},
        "col001": {"name": "Collectible Minifigure Series 1", "theme": "Collectible"},
    }
    
    figure = demo_figures.get(query.lower(), {"name": f"LEGO Minifigure: {query}", "theme": "Unknown"})
    
    base_usd = random.uniform(5, 45)
    base_rub = base_usd * 90 * random.uniform(0.8, 1.2)
    
    return {
        "query": query,
        "name": figure["name"],
        "theme": figure.get("theme"),
        "bricklink": {
            "avg_price": round(base_usd, 2),
            "min_price": round(base_usd * 0.7, 2),
            "max_price": round(base_usd * 1.5, 2),
            "qty_sold": random.randint(5, 150),
            "currency": "USD",
            "url": f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={query.upper()}",
            "demo": True
        },
        "avito": {
            "avg_price": round(base_rub, 0),
            "min_price": round(base_rub * 0.6, 0),
            "max_price": round(base_rub * 1.8, 0),
            "listings_count": random.randint(3, 45),
            "currency": "RUB",
            "url": f"https://www.avito.ru/rossiya?q=lego+{query}",
            "demo": True
        },
        "image_url": f"https://img.bricklink.com/ItemImage/MN/0/{query.upper()}.png",
        "timestamp": datetime.utcnow().isoformat(),
        "is_demo": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
