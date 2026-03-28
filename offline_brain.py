"""
offline_brain.py — Smart Local Fallback Brain
===============================================
Part 1: Cache system  — get_with_fallback()
Part 2: Scheduled prefetch — prefetch_daily_data() via APScheduler
Part 3: Intelligent offline responses — build_offline_reply()
Part 4: Static knowledge lookup — search_static_knowledge()
"""

import os
import asyncio
import requests
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional
from loguru import logger

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from database.db import SessionLocal
from database.offline_models import (
    OfflineCache, MandiPriceHistory, StaticKnowledge, PrefetchLog
)

IST = pytz.timezone("Asia/Kolkata")

# ── Cache TTLs (hours) ────────────────────────────────────────────────────────
TTL = {
    "mandi":     12,
    "weather":    6,
    "scheme":   720,   # 30 days
    "loan_rule": 720,
}

# ── Top crops / cities for morning prefetch ───────────────────────────────────
PREFETCH_CROPS  = ["wheat", "rice", "mustard", "gram", "soybean", "cotton",
                   "maize", "tur", "moong", "urad"]
PREFETCH_CITIES = ["jaipur", "delhi", "lucknow", "bhopal", "mumbai",
                   "ahmedabad", "chandigarh", "patna", "hyderabad", "pune"]

# MSP baseline (₹/quintal) — fallback when API fails
BASELINE_MSP = {
    "wheat": 2275, "rice": 2183, "paddy": 2183, "maize": 2090,
    "soybean": 4600, "cotton": 7020, "sugarcane": 340, "mustard": 5650,
    "gram": 5440, "tur": 7000, "moong": 8558, "urad": 7400,
}

API_TIMEOUT = 3


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — Cache System
# ══════════════════════════════════════════════════════════════════════════════

def _upsert_cache(db, cache_type: str, cache_key: str,
                  payload: dict, ttl_hours: int) -> None:
    """Insert or update a cache row."""
    now     = datetime.utcnow()
    expires = now + timedelta(hours=ttl_hours)

    row = (db.query(OfflineCache)
             .filter_by(cache_type=cache_type, cache_key=cache_key)
             .first())
    if row:
        row.payload    = payload
        row.fetched_at = now
        row.expires_at = expires
    else:
        db.add(OfflineCache(
            cache_type=cache_type,
            cache_key=cache_key,
            payload=payload,
            fetched_at=now,
            expires_at=expires,
        ))
    db.commit()


def _get_cache(db, cache_type: str, cache_key: str) -> Optional[dict]:
    """Return cached payload if it exists and has NOT expired."""
    row = (db.query(OfflineCache)
             .filter_by(cache_type=cache_type, cache_key=cache_key)
             .first())
    if row and row.expires_at > datetime.utcnow():
        return row.payload
    return None


def _get_stale_cache(db, cache_type: str, cache_key: str) -> tuple[Optional[dict], float]:
    """Return stale cached payload + how many hours ago it was fetched."""
    row = (db.query(OfflineCache)
             .filter_by(cache_type=cache_type, cache_key=cache_key)
             .first())
    if row:
        age_hrs = (datetime.utcnow() - row.fetched_at).total_seconds() / 3600
        return row.payload, age_hrs
    return None, 0.0


async def get_with_fallback(
    api_call: Callable[[], dict],
    cache_type: str,
    cache_key: str,
    max_age_hours: Optional[int] = None,
) -> tuple[dict, bool, float]:
    """
    Generic async cache-or-fetch wrapper.

    Returns:
        (payload, from_cache, age_hours)
        from_cache=False means live data was fetched and stored.
    """
    ttl_hours = max_age_hours or TTL.get(cache_type, 12)
    db = SessionLocal()
    try:
        # 1. Try valid cache
        cached = _get_cache(db, cache_type, cache_key)
        if cached:
            _, age = _get_stale_cache(db, cache_type, cache_key)
            return cached, True, age

        # 2. Try live API (run sync call in thread pool)
        try:
            loop = asyncio.get_event_loop()
            payload = await loop.run_in_executor(None, api_call)
            if payload:
                _upsert_cache(db, cache_type, cache_key, payload, ttl_hours)
                return payload, False, 0.0
        except Exception as e:
            logger.warning(f"[Brain] API call failed ({cache_type}/{cache_key}): {e}")

        # 3. Stale fallback
        stale, age = _get_stale_cache(db, cache_type, cache_key)
        if stale:
            return stale, True, age

        return {}, True, 999.0
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — Scheduled Daily Prefetch
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_mandi_price_sync(crop: str, city: str) -> Optional[dict]:
    try:
        url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        params = {
            "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aab825ef7e6bd8c900",
            "format": "json",
            "filters[commodity]": crop.capitalize(),
            "filters[district]":  city.capitalize(),
            "limit": 1,
        }
        r = requests.get(url, params=params, timeout=API_TIMEOUT)
        r.raise_for_status()
        records = r.json().get("records", [])
        if records:
            rec = records[0]
            price = int(float(rec.get("modal_price", rec.get("Modal_x0020_Price", 0))))
            return {"price": price, "unit": "quintal", "market": rec.get("market", city)}
    except Exception:
        pass
    return None


def _fetch_weather_sync(city: str) -> Optional[dict]:
    owm_key = os.getenv("OPENWEATHER_API_KEY", "")
    if not owm_key:
        return None
    try:
        r = requests.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={"q": city, "appid": owm_key, "units": "metric", "cnt": 24},
            timeout=API_TIMEOUT,
        )
        r.raise_for_status()
        forecasts = r.json().get("list", [])
        rain_count = sum(
            1 for f in forecasts[:24]
            if "rain" in f.get("weather", [{}])[0].get("main", "").lower()
        )
        rain_days = min(3, round(rain_count / 2))
        return {
            "rain_days": rain_days,
            "desc_hi": f"अगले {rain_days} दिन बारिश" if rain_days else "मौसम साफ़",
            "desc_en": f"Rain {rain_days} days" if rain_days else "Clear weather",
        }
    except Exception:
        return None


def _record_price_history(db, crop: str, city: str, price: float):
    db.add(MandiPriceHistory(crop=crop.lower(), city=city.lower(), price=price))
    db.commit()
    # Keep only last 30 days of history per crop+city
    cutoff = datetime.utcnow() - timedelta(days=30)
    (db.query(MandiPriceHistory)
       .filter(
           MandiPriceHistory.crop == crop.lower(),
           MandiPriceHistory.city == city.lower(),
           MandiPriceHistory.recorded_at < cutoff,
       )
       .delete())
    db.commit()


def prefetch_daily_data() -> None:
    """
    Runs every morning at 06:00 IST.
    Fetches top 10 crop × stored locations, weather, and logs results.
    """
    db  = SessionLocal()
    log = PrefetchLog(started_at=datetime.utcnow())
    db.add(log)
    db.commit()

    fetched = failed = 0

    # ── Mandi prices ──────────────────────────────────────────────────────────
    from database.models import UserPreference
    locations = [
        r.location for r in db.query(UserPreference).all()
        if r.location
    ]
    # Merge with default list, dedupe
    all_cities = list({c.lower() for c in (locations + PREFETCH_CITIES)})

    for city in all_cities[:15]:          # cap at 15 cities
        for crop in PREFETCH_CROPS:
            try:
                data = _fetch_mandi_price_sync(crop, city)
                if data:
                    key = f"{crop}_{city}"
                    _upsert_cache(db, "mandi", key,
                                  {"price": data["price"], "market": data["market"]},
                                  TTL["mandi"])
                    _record_price_history(db, crop, city, data["price"])
                    fetched += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"[Prefetch] mandi {crop}/{city}: {e}")
                failed += 1

    # ── Weather ───────────────────────────────────────────────────────────────
    for city in all_cities[:15]:
        try:
            w = _fetch_weather_sync(city)
            if w:
                _upsert_cache(db, "weather", city, w, TTL["weather"])
                fetched += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"[Prefetch] weather {city}: {e}")
            failed += 1

    # ── Finalise log ──────────────────────────────────────────────────────────
    log.finished_at   = datetime.utcnow()
    log.items_fetched = fetched
    log.items_failed  = failed
    log.notes = f"{len(all_cities)} cities × {len(PREFETCH_CROPS)} crops"
    db.commit()
    db.close()
    logger.success(f"[Prefetch] Done — {fetched} ok, {failed} failed")


def start_offline_scheduler() -> BackgroundScheduler:
    """Start APScheduler for 06:00 IST daily prefetch. Returns scheduler."""
    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(
        prefetch_daily_data,
        trigger=CronTrigger(hour=6, minute=0, timezone=IST),
        id="offline_brain_daily_prefetch",
        name="Offline Brain Daily Prefetch",
        replace_existing=True,
    )
    scheduler.start()
    logger.success("[Brain] Prefetch scheduler started — runs daily at 06:00 IST")
    return scheduler


# ══════════════════════════════════════════════════════════════════════════════
# PART 3 — Intelligent Offline Response Builder
# ══════════════════════════════════════════════════════════════════════════════

def _price_trend(db, crop: str, city: str) -> str:
    """Calculate 7-day trend from MandiPriceHistory. Returns trend string."""
    cutoff = datetime.utcnow() - timedelta(days=7)
    rows = (
        db.query(MandiPriceHistory)
          .filter(
              MandiPriceHistory.crop == crop.lower(),
              MandiPriceHistory.city == city.lower(),
              MandiPriceHistory.recorded_at >= cutoff,
          )
          .order_by(MandiPriceHistory.recorded_at)
          .all()
    )
    if len(rows) < 2:
        return "📊 ट्रेंड: पर्याप्त डेटा नहीं / Insufficient data"

    first, last = rows[0].price, rows[-1].price
    change_pct  = ((last - first) / first) * 100

    if change_pct > 2:
        return f"📈 ट्रेंड: ऊपर +{change_pct:.1f}% (7 दिन) / Rising +{change_pct:.1f}%"
    elif change_pct < -2:
        return f"📉 ट्रेंड: नीचे {change_pct:.1f}% (7 दिन) / Falling {change_pct:.1f}%"
    else:
        return f"➡️ ट्रेंड: स्थिर {change_pct:+.1f}% (7 दिन) / Stable {change_pct:+.1f}%"


def build_offline_mandi_reply(crop: str, city: str, lang: str = "hi") -> str:
    """
    Build the intelligent offline reply for /mandi when live API unreachable.
    Always returns something useful — never a bare error.
    """
    db = SessionLocal()
    try:
        key   = f"{crop.lower()}_{city.lower()}"
        stale, age_hrs = _get_stale_cache(db, "mandi", key)

        # Determine price
        if stale:
            price     = stale.get("price", BASELINE_MSP.get(crop.lower(), 2000))
            age_label = f"{int(age_hrs)} घंटे पहले / {int(age_hrs)} hours ago"
            data_note = f"📊 कैश्ड डेटा (अपडेट: {age_label})"
        else:
            price     = BASELINE_MSP.get(crop.lower(), 2000)
            age_label = "MSP बेसलाइन"
            data_note = "📊 MSP आधारित अनुमान (कोई कैश नहीं)"

        trend = _price_trend(db, crop, city)

        crop_hi_map = {
            "wheat": "गेहूं", "rice": "चावल", "paddy": "धान",
            "maize": "मक्का", "soybean": "सोयाबीन", "cotton": "कपास",
            "mustard": "सरसों", "gram": "चना", "tur": "अरहर",
            "moong": "मूंग", "urad": "उड़द", "sugarcane": "गन्ना",
        }
        crop_hi = crop_hi_map.get(crop.lower(), crop.capitalize())

        reply = (
            f"📶 *लाइव डेटा उपलब्ध नहीं* / Live data unavailable\n"
            f"{data_note}\n\n"
            f"🌾 *{crop_hi} — {city.capitalize()}*\n"
            f"💰 भाव: ₹{price:,}/quintal\n"
            f"{trend}\n\n"
            f"⚠️ लाइव भाव के लिए इंटरनेट चालू करें\n"
            f"⚠️ Connect to internet for live prices"
        )
        return reply
    finally:
        db.close()


# ══════════════════════════════════════════════════════════════════════════════
# PART 4 — Static Knowledge Base Lookup
# ══════════════════════════════════════════════════════════════════════════════

def search_static_knowledge(query: str, lang: str = "hi",
                            category: Optional[str] = None) -> Optional[str]:
    """
    Fuzzy keyword search over StaticKnowledge table.
    Returns formatted answer string, or None if no match.
    Never makes an API call — 100% offline.
    """
    db = SessionLocal()
    try:
        q = db.query(StaticKnowledge).filter(StaticKnowledge.is_active == True)
        if category:
            q = q.filter(StaticKnowledge.category == category)
        rows = q.all()

        query_lower = query.lower()
        best_row    = None
        best_score  = 0

        for row in rows:
            score = 0
            keywords = row.keywords or []
            for kw in keywords:
                if kw.lower() in query_lower:
                    score += 2
            # Title match is also valuable
            if any(w in query_lower for w in row.title.lower().split()):
                score += 1
            if score > best_score:
                best_score = score
                best_row   = row

        if best_row and best_score > 0:
            content = best_row.content_hi if lang == "hi" else best_row.content_en
            return f"📚 *{best_row.title}*\n\n{content}\n\n_(ऑफलाइन जानकारी / Offline data)_"
        return None
    finally:
        db.close()


def get_all_knowledge_titles(lang: str = "hi") -> str:
    """Return a formatted menu of all static knowledge topics."""
    db = SessionLocal()
    try:
        rows = db.query(StaticKnowledge).filter_by(is_active=True).all()
        categories: dict[str, list] = {}
        for row in rows:
            categories.setdefault(row.category, []).append(row.title)

        cat_labels_hi = {
            "scheme":        "🏛️ सरकारी योजनाएं",
            "loan_rule":     "🏦 लोन नियम",
            "fraud_pattern": "🚨 धोखाधड़ी पैटर्न",
            "crop_advisory": "🌱 फसल सलाह",
        }
        cat_labels_en = {
            "scheme":        "🏛️ Government Schemes",
            "loan_rule":     "🏦 Loan Rules",
            "fraud_pattern": "🚨 Fraud Patterns",
            "crop_advisory": "🌱 Crop Advisory",
        }
        labels = cat_labels_hi if lang == "hi" else cat_labels_en

        lines = ["📚 *ऑफलाइन ज्ञान आधार / Offline Knowledge Base*\n"]
        for cat, titles in categories.items():
            lines.append(f"\n{labels.get(cat, cat)}:")
            for t in titles:
                lines.append(f"  • {t}")
        lines.append("\nकीवर्ड लिखकर पूछें / Type keywords to ask")
        return "\n".join(lines)
    finally:
        db.close()
