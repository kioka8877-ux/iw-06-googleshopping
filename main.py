"""
IW-06 GoogleShopping — Google Shopping Results
Iron Warrior #6 — E-commerce, prix + produits.
Attaque : Advanced SERP ($39.99/10K)
"""
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import sys
sys.path.insert(0, '/home/user/iron_warriors/shared')
from base import create_app, fetch_html, clean_text, get_timestamp, measure_latency
import time

app = create_app("IW-06 GoogleShopping", "Google Shopping results — prix + produits e-commerce")

class ShoppingResult(BaseModel):
    title: str
    url: str
    price: Optional[str] = None
    merchant: Optional[str] = None
    rating: Optional[str] = None
    reviews: Optional[str] = None
    image_url: Optional[str] = None
    position: int

class ShoppingResponse(BaseModel):
    query: str
    engine: str
    results: List[ShoppingResult]
    timestamp: str
    latency_ms: int

@app.get("/search", response_model=ShoppingResponse)
async def google_shopping(
    q: str = Query(..., description="Product search query"),
    num: int = Query(20, ge=1, le=50),
    gl: str = Query("us"),
    hl: str = Query("en"),
):
    start = time.time()
    url = f"https://www.google.com/search?q={quote_plus(q)}&tbm=shop&num={num}&gl={gl}&hl={hl}"
    try:
        html = await fetch_html(url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Google Shopping fetch failed: {e}")

    soup = BeautifulSoup(html, 'html.parser')
    results = []
    seen = set()

    # Google Shopping results
    for div in soup.find_all('div', class_='sh-dgr__content') or soup.find_all('div', {'data-docid': True}):
        title_tag = div.find('h3') or div.find('a', class_='shntl')
        link = div.find('a', href=True)
        price_tag = div.find('span', class_='a8Pkg') or div.find('span', class_='OELB7d')
        merchant_tag = div.find('div', class_='sh-dgr__merchant')
        rating_tag = div.find('span', class_='Rsc7Yb')
        reviews_tag = div.find('span', class_='QIrs8')
        img_tag = div.find('img')

        if title_tag and link:
            href = link['href']
            if href.startswith('/url?q='):
                href = href.split('/url?q=')[1].split('&')[0]
            if href in seen or not href.startswith('http'):
                continue
            seen.add(href)
            results.append(ShoppingResult(
                title=clean_text(title_tag.get_text()),
                url=href,
                price=clean_text(price_tag.get_text()) if price_tag else None,
                merchant=clean_text(merchant_tag.get_text()) if merchant_tag else None,
                rating=clean_text(rating_tag.get_text()) if rating_tag else None,
                reviews=clean_text(reviews_tag.get_text()) if reviews_tag else None,
                image_url=img_tag.get('src') if img_tag else None,
                position=len(results) + 1,
            ))
            if len(results) >= num:
                break

    return ShoppingResponse(
        query=q, engine="google_shopping", results=results,
        timestamp=get_timestamp(), latency_ms=measure_latency(start),
    )
