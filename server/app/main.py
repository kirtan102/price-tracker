import logging
from datetime import timedelta
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .alerts import evaluate
from .auth import decode_access, hash_password, make_access, make_refresh, verify_password
from .config import settings
from .db import Base, SessionLocal, engine, get_db, now
from .models import *
from .providers import parse_product_url, provider_for
from .schemas import *

logging.basicConfig(level=settings.log_level, format='{"level":"%(levelname)s","message":"%(message)s"}')
app=FastAPI(title="Personal Price Tracker", version="1.0", docs_url="/docs" if settings.app_env=="dev" else None)
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in settings.cors_origins.split(",")], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
bearer=HTTPBearer()

@app.on_event("startup")
async def startup():
    async with engine.begin() as c: await c.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        if not await db.scalar(select(User).where(User.username==settings.admin_username)):
            db.add(User(username=settings.admin_username,password_hash=hash_password(settings.admin_password),created_at=now())); await db.commit()

async def user(creds: HTTPAuthorizationCredentials=Depends(bearer),db: AsyncSession=Depends(get_db)):
    try: uid=int(decode_access(creds.credentials)["sub"])
    except Exception: raise HTTPException(401,"invalid access token")
    u=await db.get(User,uid)
    if not u: raise HTTPException(401,"user not found")
    return u

@app.get("/health")
async def health(): return {"status":"ok","environment":settings.app_env}

@app.post("/api/v1/auth/login",response_model=TokenOut)
async def login(body: LoginIn,db:AsyncSession=Depends(get_db)):
    u=await db.scalar(select(User).where(User.username==body.username))
    if not u or not verify_password(body.password,u.password_hash): raise HTTPException(401,"invalid credentials")
    raw,h=make_refresh(); db.add(RefreshToken(user_id=u.id,token_hash=h,expires_at=now()+timedelta(days=settings.refresh_days))); await db.commit(); return TokenOut(access_token=make_access(u.id),refresh_token=raw)

@app.post("/api/v1/auth/refresh",response_model=TokenOut)
async def refresh(body:RefreshIn,db:AsyncSession=Depends(get_db)):
    import hashlib
    row=await db.scalar(select(RefreshToken).where(RefreshToken.token_hash==hashlib.sha256(body.refresh_token.encode()).hexdigest(),RefreshToken.revoked==False))
    if not row or row.expires_at<now(): raise HTTPException(401,"invalid refresh token")
    row.revoked=True; raw,h=make_refresh(); db.add(RefreshToken(user_id=row.user_id,token_hash=h,expires_at=now()+timedelta(days=settings.refresh_days))); await db.commit(); return TokenOut(access_token=make_access(row.user_id),refresh_token=raw)

@app.post("/api/v1/products/preview")
async def preview(body:PreviewIn, _:User=Depends(user)):
    try: marketplace,pid=parse_product_url(body.url)
    except ValueError as e: raise HTTPException(422,detail={"code":"invalid_url","message":str(e)})
    try: snap=await provider_for(marketplace).fetch_product(pid)
    except LookupError as e: raise HTTPException(404,detail={"code":"product_not_found","message":str(e)})
    except Exception as e: raise HTTPException(503,detail={"code":"provider_unavailable","message":str(e)})
    return {"marketplace":marketplace,"product_id":pid,"title":snap.title,"image_url":snap.image_url,"prices":snap.prices,"available_price_types":list(snap.prices)}

@app.post("/api/v1/products",response_model=ProductOut)
async def add(body:TrackIn,u:User=Depends(user),db:AsyncSession=Depends(get_db)):
    p=await db.scalar(select(TrackedProduct).where(TrackedProduct.user_id==u.id,TrackedProduct.canonical_url==body.url))
    if p: raise HTTPException(409,detail={"code":"duplicate_product"})
    marketplace,pid=parse_product_url(body.url); snap=await provider_for(marketplace).fetch_product(pid); price=snap.prices.get(body.selected_price_type)
    p=TrackedProduct(user_id=u.id,marketplace=marketplace,product_id=pid,canonical_url=body.url,title=snap.title,image_url=snap.image_url,selected_price_type=body.selected_price_type,current_price=price,target_price=body.target_price,status="active",last_checked_at=now(),last_success_at=now(),created_at=now())
    db.add(p); await db.flush(); a=AlertSettings(product_id=p.id,**body.alerts.model_dump()); db.add(a); db.add(PriceObservation(product_id=p.id,price=price,observed_at=now(),price_type=body.selected_price_type,available=snap.available.get(body.selected_price_type,False),provider=snap.provider)); await db.commit(); await db.refresh(p); return p

@app.get("/api/v1/products",response_model=list[ProductOut])
async def products(u:User=Depends(user),db:AsyncSession=Depends(get_db)): return (await db.scalars(select(TrackedProduct).where(TrackedProduct.user_id==u.id).order_by(TrackedProduct.created_at if hasattr(TrackedProduct,'created_at') else TrackedProduct.id))).all()

@app.get("/api/v1/products/{product_id}/history")
async def history(product_id:int,u:User=Depends(user),db:AsyncSession=Depends(get_db)):
    p=await db.scalar(select(TrackedProduct).where(TrackedProduct.id==product_id,TrackedProduct.user_id==u.id));
    if not p: raise HTTPException(404,"not found")
    return (await db.scalars(select(PriceObservation).where(PriceObservation.product_id==p.id).order_by(PriceObservation.observed_at))).all()

@app.post("/api/v1/dev/simulate/{product_id}")
async def simulate(product_id:int,price:int|None=None,u:User=Depends(user),db:AsyncSession=Depends(get_db)):
    if settings.app_env!="dev": raise HTTPException(404)
    p=await db.scalar(select(TrackedProduct).where(TrackedProduct.id==product_id,TrackedProduct.user_id==u.id));
    if not p: raise HTTPException(404,"not found")
    previous=p.current_price; current=price if price is not None else max(1,(previous or 100000)-10000); p.previous_price=previous; p.current_price=current
    a=await db.scalar(select(AlertSettings).where(AlertSettings.product_id=p.id)); types=await evaluate(db,p,previous,current,True,a)
    db.add(PriceObservation(product_id=p.id,price=current,observed_at=now(),price_type=p.selected_price_type,available=True,provider="simulator",changed=current!=previous)); await db.commit(); return {"price":current,"alerts":types}

