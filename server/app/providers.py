import asyncio, random, re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse, urlunparse
import httpx
from .config import settings

@dataclass
class ProductSnapshot:
    marketplace: str; product_id: str; title: str; image_url: str|None; prices: dict[str,int|None]; available: dict[str,bool]; provider: str

class PriceProvider:
    name="base"
    def parse_url(self, url): raise NotImplementedError
    async def fetch_product(self, product_id): raise NotImplementedError

class MockProvider(PriceProvider):
    def __init__(self, marketplace): self.marketplace=marketplace; self.name=f"mock_{marketplace}"
    def parse_url(self, url): return self.marketplace, parse_product_url(url)[1]
    async def fetch_product(self, product_id):
        return ProductSnapshot(self.marketplace, product_id, f"Mock {self.marketplace.title()} product {product_id}", None, {"listed_price": 269900}, {"listed_price": True}, self.name)

class AmazonKeepaProvider(PriceProvider):
    name="keepa"
    def parse_url(self, url): return parse_product_url(url)
    async def fetch_product(self, product_id):
        if not settings.keepa_api_key: raise RuntimeError("Keepa API key is not configured")
        endpoint="https://api.keepa.com/product"
        params={"key":settings.keepa_api_key,"domain":"10","asin":product_id,"stats":"1"}
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.get(endpoint, params=params); r.raise_for_status(); data=r.json()
        p=(data.get("products") or [None])[0]
        if not p: raise LookupError("product not found")
        stats=p.get("stats") or {}; prices={k:v for k,v in {"buy_box":stats.get("buyBoxPrice"),"amazon":stats.get("current",[None])[0],"marketplace_new":stats.get("newPrice",[None])[0]}.items() if v is not None}
        prices={k:int(v) for k,v in prices.items()}; return ProductSnapshot("amazon_in",product_id,p.get("title") or product_id,p.get("imagesCSV","").split(",")[0] or None,prices,{k:v is not None for k,v in prices.items()},self.name)

class FlipkartProvider(PriceProvider):
    name="flipkart_api"
    def parse_url(self, url): return parse_product_url(url)
    async def fetch_product(self, product_id):
        if not settings.flipkart_api_url: raise RuntimeError("Flipkart provider endpoint is not configured")
        headers={"Authorization":f"Bearer {settings.flipkart_api_key}"} if settings.flipkart_api_key else {}
        async with httpx.AsyncClient(timeout=20) as client:
            r=await client.get(settings.flipkart_api_url, params={"pid":product_id}, headers=headers); r.raise_for_status(); d=r.json()
        price=d.get("price"); return ProductSnapshot("flipkart",product_id,d.get("title",product_id),d.get("image_url"),{"listed_price":int(price) if price is not None else None},{"listed_price":price is not None},self.name)

def parse_product_url(raw: str):
    u=urlparse(raw.strip()); host=u.netloc.lower().split(":")[0]; path=u.path
    if host in {"amzn.in","www.amzn.in"}:
        # Short links require resolving before a provider fetch.
        raise ValueError("short Amazon links must be expanded by the client or API gateway")
    if host.endswith("amazon.in"):
        m=re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", path, re.I)
        if m:return "amazon_in",m.group(1).upper()
    if host.endswith("flipkart.com") or host=="dl.flipkart.com":
        q=parse_qs(u.query); pid=(q.get("pid") or [None])[0] or (re.search(r"/p/(?:itm)?([A-Za-z0-9]+)",path) or [None,None])[1]
        if pid:return "flipkart",pid
    raise ValueError("unsupported or invalid product URL")

def provider_for(marketplace):
    if marketplace=="amazon_in": return AmazonKeepaProvider()
    if settings.app_env=="dev" and settings.flipkart_provider=="mock": return MockProvider("flipkart")
    return FlipkartProvider()

