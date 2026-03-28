"""
Offline Brain — ORM Models (4 new tables)
  offline_cache        — generic API response store with TTL
  mandi_price_history  — rolling price log for 7-day trend
  static_knowledge     — zero-API knowledge base (schemes, RBI rules, fraud)
  prefetch_log         — audit log for daily 6 AM prefetch runs
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, Index
from database.models import Base  # reuse existing declarative_base


class OfflineCache(Base):
    __tablename__ = "offline_cache"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    cache_type = Column(String(30),  nullable=False)   # mandi|weather|scheme|loan_rule
    cache_key  = Column(String(200), nullable=False)   # e.g. wheat_jaipur
    payload    = Column(JSON,        nullable=False)
    fetched_at = Column(DateTime,    default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime,    nullable=False)   # absolute UTC expiry

Index("ix_offline_cache_type_key", OfflineCache.cache_type, OfflineCache.cache_key, unique=True)


class MandiPriceHistory(Base):
    __tablename__ = "mandi_price_history"
    id          = Column(Integer, primary_key=True, autoincrement=True)
    crop        = Column(String(50),  nullable=False)
    city        = Column(String(100), nullable=False)
    price       = Column(Float,       nullable=False)   # ₹/quintal
    source      = Column(String(30),  default="agmarknet")
    recorded_at = Column(DateTime,    default=datetime.utcnow, nullable=False)

Index("ix_mandi_price_crop_city", MandiPriceHistory.crop, MandiPriceHistory.city)


class StaticKnowledge(Base):
    __tablename__ = "static_knowledge"
    id         = Column(Integer, primary_key=True, autoincrement=True)
    category   = Column(String(30),  nullable=False)  # scheme|loan_rule|fraud_pattern|crop_advisory
    title      = Column(String(200), nullable=False)
    content_hi = Column(Text,        nullable=False)
    content_en = Column(Text,        nullable=False)
    keywords   = Column(JSON,        default=list)
    is_active  = Column(Boolean,     default=True)
    updated_at = Column(DateTime,    default=datetime.utcnow)


class PrefetchLog(Base):
    __tablename__ = "prefetch_log"
    id            = Column(Integer, primary_key=True, autoincrement=True)
    started_at    = Column(DateTime, default=datetime.utcnow)
    finished_at   = Column(DateTime, nullable=True)
    items_fetched = Column(Integer,  default=0)
    items_failed  = Column(Integer,  default=0)
    notes         = Column(Text,     nullable=True)
