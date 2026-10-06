import asyncio, logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from .alerts import evaluate
from .config import settings
from .db import SessionLocal, now
from .models import AlertSettings, PriceObservation, ProductStatus, TrackedProduct
from .providers import provider_for

async def check_one(p):
    async with SessionLocal() as db:
        try:
            snap=await provider_for(p.marketplace.value).fetch_product(p.product_id); current=snap.prices.get(p.selected_price_type); previous=p.current_price
            p.previous_price=previous; p.current_price=current; p.last_checked_at=now(); p.last_success_at=now(); p.consecutive_failures=0; p.status=ProductStatus.active; p.last_error=None
            db.add(PriceObservation(product_id=p.id,price=current,observed_at=now(),price_type=p.selected_price_type,available=snap.available.get(p.selected_price_type,False),provider=snap.provider,changed=current!=previous))
            a=await db.scalar(select(AlertSettings).where(AlertSettings.product_id==p.id)); types=await evaluate(db,p,previous,current,snap.available.get(p.selected_price_type,False),a)
            await db.commit(); logging.info("checked product=%s alerts=%s",p.id,types)
        except Exception as e:
            p.consecutive_failures+=1; p.last_error=str(e); p.last_checked_at=now();
            if p.consecutive_failures>=settings.max_failures: p.status=ProductStatus.error
            await db.commit(); logging.exception("check failed product=%s",p.id)

async def run():
    scheduler=AsyncIOScheduler(); scheduler.add_job(tick,"interval",minutes=settings.check_interval_minutes); scheduler.start(); await tick();
    while True: await asyncio.sleep(3600)
async def tick():
    async with SessionLocal() as db: products=(await db.scalars(select(TrackedProduct).where(TrackedProduct.status==ProductStatus.active))).all()
    await asyncio.gather(*(check_one(p) for p in products))
if __name__=="__main__": asyncio.run(run())

