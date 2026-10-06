from datetime import timedelta
from sqlalchemy import select
from .db import now
from .models import PriceObservation, AlertSettings

async def evaluate(db, product, previous, current, available, settings_row):
    events=[]
    if current is None: return events
    if previous is not None:
        delta=current-previous; pct=abs(delta)*100/previous if previous else 0
        if delta<0 and settings_row.notify_on_drop and (settings_row.min_drop_amount is None or abs(delta)>=settings_row.min_drop_amount) and (settings_row.min_drop_percent is None or pct>=settings_row.min_drop_percent): events.append("drop")
        if delta>0 and settings_row.notify_on_increase and (settings_row.min_increase_amount is None or delta>=settings_row.min_increase_amount) and (settings_row.min_increase_percent is None or pct>=settings_row.min_increase_percent): events.append("increase")
    if settings_row.notify_on_target and product.target_price is not None and current<=product.target_price and (previous is None or previous>product.target_price): events.append("target")
    if settings_row.notify_on_back_in_stock and available and previous is None: events.append("back_in_stock")
    since=now()-timedelta(days=settings_row.new_low_window)
    lows=(await db.scalars(select(PriceObservation.price).where(PriceObservation.product_id==product.id,PriceObservation.observed_at>=since,PriceObservation.price.is_not(None)).order_by(PriceObservation.observed_at))).all()
    if settings_row.notify_on_new_low and len(lows)>1 and current<min(lows[:-1]): events.append("new_low")
    return list(dict.fromkeys(events))

