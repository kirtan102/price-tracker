import enum
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .db import Base

class Marketplace(str, enum.Enum): amazon_in="amazon_in"; flipkart="flipkart"
class ProductStatus(str, enum.Enum): active="active"; paused="paused"; error="error"

class User(Base):
    __tablename__="users"; id: Mapped[int]=mapped_column(primary_key=True); username: Mapped[str]=mapped_column(String(100), unique=True); password_hash: Mapped[str]=mapped_column(String(255)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
class RefreshToken(Base):
    __tablename__="refresh_tokens"; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey("users.id")); token_hash: Mapped[str]=mapped_column(String(255), unique=True); expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); revoked: Mapped[bool]=mapped_column(Boolean, default=False)
class Device(Base):
    __tablename__="devices"; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey("users.id")); fcm_token: Mapped[str]=mapped_column(String(512), unique=True); name: Mapped[str|None]=mapped_column(String(100)); last_seen: Mapped[datetime]=mapped_column(DateTime(timezone=True)); active: Mapped[bool]=mapped_column(Boolean, default=True)
class TrackedProduct(Base):
    __tablename__="tracked_products"; __table_args__=(UniqueConstraint("user_id","marketplace","product_id"),)
    id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey("users.id")); marketplace: Mapped[Marketplace]=mapped_column(Enum(Marketplace)); product_id: Mapped[str]=mapped_column(String(200)); canonical_url: Mapped[str]=mapped_column(Text); title: Mapped[str]=mapped_column(String(500)); image_url: Mapped[str|None]=mapped_column(Text); selected_price_type: Mapped[str]=mapped_column(String(100)); current_price: Mapped[int|None]=mapped_column(Integer); previous_price: Mapped[int|None]=mapped_column(Integer); target_price: Mapped[int|None]=mapped_column(Integer); status: Mapped[ProductStatus]=mapped_column(Enum(ProductStatus), default=ProductStatus.active); last_checked_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); last_success_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True)); consecutive_failures: Mapped[int]=mapped_column(Integer, default=0); last_error: Mapped[str|None]=mapped_column(Text); check_interval_minutes: Mapped[int]=mapped_column(Integer, default=60); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
class AlertSettings(Base):
    __tablename__="alert_settings"; id: Mapped[int]=mapped_column(primary_key=True); product_id: Mapped[int]=mapped_column(ForeignKey("tracked_products.id"), unique=True); notify_on_drop: Mapped[bool]=mapped_column(Boolean, default=True); notify_on_increase: Mapped[bool]=mapped_column(Boolean, default=False); notify_on_target: Mapped[bool]=mapped_column(Boolean, default=True); notify_on_new_low: Mapped[bool]=mapped_column(Boolean, default=True); new_low_window: Mapped[int]=mapped_column(Integer, default=30); notify_on_back_in_stock: Mapped[bool]=mapped_column(Boolean, default=True); min_drop_amount: Mapped[int|None]=mapped_column(Integer); min_drop_percent: Mapped[int|None]=mapped_column(Integer); min_increase_amount: Mapped[int|None]=mapped_column(Integer); min_increase_percent: Mapped[int|None]=mapped_column(Integer)
class PriceObservation(Base):
    __tablename__="price_observations"; id: Mapped[int]=mapped_column(primary_key=True); product_id: Mapped[int]=mapped_column(ForeignKey("tracked_products.id")); price: Mapped[int|None]=mapped_column(Integer); currency: Mapped[str]=mapped_column(String(3), default="INR"); observed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); price_type: Mapped[str]=mapped_column(String(100)); available: Mapped[bool]=mapped_column(Boolean); provider: Mapped[str]=mapped_column(String(100)); changed: Mapped[bool]=mapped_column(Boolean, default=False)
class AlertEvent(Base):
    __tablename__="alert_events"; id: Mapped[int]=mapped_column(primary_key=True); product_id: Mapped[int]=mapped_column(ForeignKey("tracked_products.id")); type: Mapped[str]=mapped_column(String(50)); old_price: Mapped[int|None]=mapped_column(Integer); new_price: Mapped[int|None]=mapped_column(Integer); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); dedupe_key: Mapped[str]=mapped_column(String(255), unique=True); read: Mapped[bool]=mapped_column(Boolean, default=False); notification_sent: Mapped[bool]=mapped_column(Boolean, default=False)
class Notification(Base):
    __tablename__="notifications"; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int]=mapped_column(ForeignKey("users.id")); product_id: Mapped[int|None]=mapped_column(ForeignKey("tracked_products.id")); title: Mapped[str]=mapped_column(String(200)); body: Mapped[str]=mapped_column(Text); data: Mapped[dict]=mapped_column(JSON, default=dict); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True)); read: Mapped[bool]=mapped_column(Boolean, default=False)
class TrackingEvent(Base):
    __tablename__="tracking_events"; id: Mapped[int]=mapped_column(primary_key=True); product_id: Mapped[int]=mapped_column(ForeignKey("tracked_products.id")); kind: Mapped[str]=mapped_column(String(50)); detail: Mapped[str|None]=mapped_column(Text); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))

