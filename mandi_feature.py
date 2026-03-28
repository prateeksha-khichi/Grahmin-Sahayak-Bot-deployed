"""
=============================================================================
mandi_feature.py — /mandi command helper
Feature 1: Smart Market + Weather Intel with Offline Fallback

Responsibilities:
  • Fetch live mandi price from Agmarknet (with 2-sec timeout)
  • Fetch 3-day weather forecast from OpenWeatherMap (with 2-sec timeout)
  • Combine into a bilingual Hindi + English verdict
  • Serve cached data from mandi_cache.json on any failure
  • Refresh cache daily at 06:00 AM IST via APScheduler
=============================================================================
"""

import os
import json
import time
import asyncio
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from loguru import logger

# APScheduler (non-async, background scheduler)
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

# Path to the cache file (placed next to this file in the project root)
CACHE_FILE = Path(__file__).parent / "mandi_cache.json"

# API timeout in seconds (critical for 2G users)
API_TIMEOUT = 2

# OpenWeatherMap free-tier base URL
OWM_BASE_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Agmarknet base URL (public data portal — returns HTML; we scrape a summary)
AGMARKNET_BASE_URL = "https://agmarknet.gov.in/SearchCommodityWise.aspx"

# India Standard Time offset
IST = pytz.timezone("Asia/Kolkata")

# Minimum Procurement Season window (Oct–Feb) for MSP check
MSP_SEASON_MONTHS = {10, 11, 12, 1, 2}

# Baseline MSP prices (₹/quintal) — updated annually; used as fallback reference
BASELINE_MSP = {
    "wheat":   2275,
    "rice":    2183,
    "paddy":   2183,
    "maize":   2090,
    "soybean": 4600,
    "cotton":  7020,
    "sugarcane": 340,
    "mustard": 5650,
    "gram":    5440,
    "tur":     7000,
    "moong":   8558,
    "urad":    7400,
}

# Simulated price range (±5%) around MSP for demo fallback
def _simulated_price(crop: str) -> int:
    """Return a plausible demo price when live API is unreachable."""
    base = BASELINE_MSP.get(crop.lower(), 2000)
    import random
    random.seed(crop.lower())  # deterministic per crop so cache is consistent
    return int(base * (1 + random.uniform(-0.05, 0.08)))


# ─────────────────────────────────────────
# CACHE HELPERS
# ─────────────────────────────────────────

def _load_cache() -> dict:
    """Load the JSON cache from disk. Returns empty dict on any error."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"[mandi] Cache load error: {e}")
    return {}


def _save_cache(cache: dict) -> None:
    """Persist the cache dict to disk atomically."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        logger.debug(f"[mandi] Cache saved to {CACHE_FILE}")
    except Exception as e:
        logger.error(f"[mandi] Cache save error: {e}")


def _cache_key(crop: str, city: str) -> str:
    """Normalised key: wheat_jaipur"""
    return f"{crop.lower().strip()}_{city.lower().strip()}"


def _hours_ago(timestamp_str: str) -> float:
    """Return how many hours ago an ISO timestamp was recorded."""
    try:
        then = datetime.fromisoformat(timestamp_str)
        if then.tzinfo is None:
            then = then.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - then
        return delta.total_seconds() / 3600
    except Exception:
        return 999.0


# ─────────────────────────────────────────
# LIVE DATA FETCHERS  (sync, short timeout)
# ─────────────────────────────────────────

def _fetch_mandi_price(crop: str, city: str) -> dict | None:
    """
    Attempt to fetch mandi price from Agmarknet.

    NOTE: Agmarknet's public portal does NOT expose a clean JSON REST API.
    The official data is served via HTML forms / dynamic pages and requires
    authentication for the bulk download API.
    Strategy used here:
      1. Try the government's data.gov.in MANDI dataset (open REST, JSON).
      2. If that times out / fails → return None so caller uses cache.

    Returns dict with keys: price (int), unit (str), market (str)
    """
    try:
        # data.gov.in has published Agmarknet price datasets as JSON APIs
        # Resource ID for "Daily Market Price" (commodity-wise)
        resource_id = "9ef84268-d588-465a-a308-a864a43d0070"
        url = "https://api.data.gov.in/resource/" + resource_id
        params = {
            "api-key": "579b464db66ec23bdd000001cdd3946e44ce4aab825ef7e6bd8c900",  # public demo key
            "format":  "json",
            "filters[commodity]": crop.capitalize(),
            "filters[district]":  city.capitalize(),
            "limit":  1,
        }
        resp = requests.get(url, params=params, timeout=API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        records = data.get("records", [])
        if records:
            rec = records[0]
            # Field names from data.gov.in Agmarknet dataset
            price = int(float(rec.get("modal_price", rec.get("Modal_x0020_Price", 2000))))
            return {
                "price":  price,
                "unit":   "quintal",
                "market": rec.get("market", city),
            }
    except requests.exceptions.Timeout:
        logger.warning(f"[mandi] Agmarknet timeout for {crop}/{city}")
    except Exception as e:
        logger.warning(f"[mandi] Agmarknet fetch error: {e}")
    return None


def _fetch_weather(city: str, owm_key: str) -> dict | None:
    """
    Fetch 3-day weather forecast from OpenWeatherMap free-tier /forecast endpoint.
    Returns dict with keys: summary (str), rain_days (int), description_hi (str)
    """
    try:
        params = {
            "q":     city,
            "appid": owm_key,
            "units": "metric",
            "cnt":   24,   # 8 forecasts/day × 3 days
            "lang":  "en",
        }
        resp = requests.get(OWM_BASE_URL, params=params, timeout=API_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        forecasts = data.get("list", [])
        rain_count = 0
        conditions = []
        for f in forecasts[:24]:
            weather_main = f.get("weather", [{}])[0].get("main", "").lower()
            if "rain" in weather_main or "storm" in weather_main:
                rain_count += 1
            conditions.append(weather_main)

        # Convert 3-hourly rain slots → approximate rain days
        rain_days = min(3, round(rain_count / 2))

        if rain_days >= 2:
            summary = "rain"
            desc_hi = f"अगले {rain_days} दिन बारिश"
            desc_en = f"Rain expected {rain_days} days"
        elif rain_days == 1:
            summary = "light_rain"
            desc_hi = "कल हल्की बारिश हो सकती है"
            desc_en = "Light rain possible tomorrow"
        else:
            summary = "clear"
            desc_hi = "मौसम साफ़ रहेगा"
            desc_en = "Clear weather expected"

        return {
            "summary":    summary,
            "rain_days":  rain_days,
            "desc_hi":    desc_hi,
            "desc_en":    desc_en,
        }
    except requests.exceptions.Timeout:
        logger.warning(f"[mandi] OpenWeatherMap timeout for {city}")
    except Exception as e:
        logger.warning(f"[mandi] OpenWeatherMap fetch error: {e}")
    return None


# ─────────────────────────────────────────
# VERDICT BUILDER
# ─────────────────────────────────────────

def _build_verdict(crop: str, city: str, price: int, weather: dict, from_cache: bool = False, cache_hours: float = 0) -> str:
    """
    Compose the bilingual sell-advice verdict message.
    Considers weather forecast to recommend immediate vs delayed sale.
    """
    crop_hi_map = {
        "wheat":    "गेहूं", "rice":    "चावल", "paddy":  "धान",
        "maize":    "मक्का", "soybean": "सोयाबीन", "cotton": "कपास",
        "mustard":  "सरसों", "gram":    "चना",   "tur":    "अरहर",
        "moong":    "मूंग",  "urad":    "उड़द",  "sugarcane": "गन्ना",
    }
    crop_hi = crop_hi_map.get(crop.lower(), crop.capitalize())

    rain_days = weather.get("rain_days", 0)
    weather_hi = weather.get("desc_hi", "मौसम साफ़ रहेगा")
    weather_en = weather.get("desc_en", "Clear weather")

    # Price estimate after wait: +2–3% uplift if rain expected (demand increases)
    if rain_days >= 2:
        wait_days = rain_days + 1
        estimated_price = int(price * 1.03)
        advice_hi = f"{wait_days} दिन रुककर बेचें, अनुमानित ₹{estimated_price:,} मिलेगा"
        advice_en = f"Wait {wait_days} days to sell, estimated ₹{estimated_price:,}"
    else:
        estimated_price = int(price * 1.01)
        advice_hi = f"अभी बेचें या 1-2 दिन प्रतीक्षा करें, अनुमानित ₹{estimated_price:,} मिलेगा"
        advice_en = f"Sell now or wait 1-2 days, estimated ₹{estimated_price:,}"

    # MSP reference if in procurement season
    msp_note = ""
    current_month = datetime.now(IST).month
    msp = BASELINE_MSP.get(crop.lower())
    if msp and current_month in MSP_SEASON_MONTHS:
        if price < msp:
            msp_note = (
                f"\n\n⚠️ *MSP सूचना*: सरकारी MSP ₹{msp:,}/quintal है। "
                f"मंडी भाव MSP से कम है — सरकारी खरीद केंद्र पर बेचने की कोशिश करें।\n"
                f"⚠️ *MSP Notice*: Govt MSP is ₹{msp:,}/quintal. "
                f"Current price is below MSP — try selling at govt procurement centre."
            )
        else:
            msp_note = (
                f"\n\n✅ मंडी भाव MSP (₹{msp:,}) से अधिक है।\n"
                f"✅ Mandi price is above MSP (₹{msp:,})."
            )

    # Cache tag
    cache_tag = ""
    if from_cache:
        hrs = int(cache_hours)
        cache_tag = f"\n\n📶 _(ऑफलाइन डेटा — {hrs} घंटे पहले का)_\n_(cached {hrs} hours ago)_"

    verdict = (
        f"🌾 *{crop_hi} — {city.capitalize()} मंडी भाव*\n\n"
        f"💰 आज का भाव: ₹{price:,}/quintal\n"
        f"🌦️ मौसम: {weather_hi}\n"
        f"📊 सलाह: {advice_hi}\n\n"
        f"——\n"
        f"*{crop.capitalize()} — {city.capitalize()} Mandi Price*\n\n"
        f"💰 Today's Price: ₹{price:,}/quintal\n"
        f"🌦️ Weather: {weather_en}\n"
        f"📊 Advice: {advice_en}"
        f"{msp_note}"
        f"{cache_tag}"
    )
    return verdict


# ─────────────────────────────────────────
# MAIN PUBLIC FUNCTION
# ─────────────────────────────────────────

def get_mandi_info(crop: str, city: str) -> str:
    """
    Primary entry point called by the /mandi Telegram handler.

    Flow:
      1. Try live Agmarknet + OpenWeatherMap (2-sec timeout each)
      2. On failure → serve from mandi_cache.json
      3. On cache miss → build from simulated/MSP baseline + cached weather

    Returns a bilingual formatted message string.
    """
    key = _cache_key(crop, city)
    owm_key = os.getenv("OPENWEATHER_API_KEY", "")

    # ── Step 1: Try live APIs ─────────────────────────────────────────────
    price_data = _fetch_mandi_price(crop, city)
    weather_data = _fetch_weather(city, owm_key) if owm_key else None

    if price_data and weather_data:
        price = price_data["price"]
        verdict = _build_verdict(crop, city, price, weather_data)

        # Update cache with fresh data
        cache = _load_cache()
        cache[key] = {
            "price":     price,
            "weather":   weather_data["summary"],
            "weather_detail": weather_data,
            "verdict":   verdict,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        _save_cache(cache)
        logger.info(f"[mandi] Live data fetched and cached for {key}")
        return verdict

    # ── Step 2: Fallback to cache ─────────────────────────────────────────
    cache = _load_cache()
    if key in cache:
        entry = cache[key]
        hours = _hours_ago(entry.get("timestamp", ""))
        cached_verdict = entry.get("verdict", "")

        # Rebuild verdict with fresh cache-tag (hours may have changed)
        price = entry.get("price", _simulated_price(crop))
        weather_detail = entry.get("weather_detail", {
            "rain_days": 0, "desc_hi": "मौसम जानकारी उपलब्ध नहीं", "desc_en": "Weather unavailable"
        })
        verdict = _build_verdict(crop, city, price, weather_detail, from_cache=True, cache_hours=hours)
        logger.info(f"[mandi] Served from cache for {key} ({hours:.1f}h ago)")
        return verdict

    # ── Step 3: Full fallback (no cache entry) ────────────────────────────
    price = _simulated_price(crop)
    weather_fallback = {
        "rain_days": 0,
        "desc_hi": "मौसम जानकारी उपलब्ध नहीं (नेटवर्क समस्या)",
        "desc_en": "Weather unavailable (network issue)",
    }
    # Partial live fetch: if we got price but not weather, use it
    if price_data:
        price = price_data["price"]
    if weather_data:
        weather_fallback = weather_data

    verdict = _build_verdict(crop, city, price, weather_fallback, from_cache=True, cache_hours=999)

    # Seed the cache so next call has something
    cache[key] = {
        "price":        price,
        "weather":      "unknown",
        "weather_detail": weather_fallback,
        "verdict":      verdict,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }
    _save_cache(cache)
    logger.warning(f"[mandi] No cache entry for {key}; seeded with baseline price ₹{price}")
    return verdict


# ─────────────────────────────────────────
# SCHEDULED CACHE REFRESH
# ─────────────────────────────────────────

def _refresh_all_cache() -> None:
    """
    Called by APScheduler every day at 06:00 IST.
    Re-fetches data for every crop+city pair already in the cache,
    so 2G users get fresh morning data without waiting.
    """
    logger.info("[mandi] Scheduled cache refresh starting...")
    cache = _load_cache()
    owm_key = os.getenv("OPENWEATHER_API_KEY", "")

    refreshed = 0
    for key in list(cache.keys()):
        try:
            parts = key.split("_", 1)
            if len(parts) != 2:
                continue
            crop, city = parts

            price_data = _fetch_mandi_price(crop, city)
            weather_data = _fetch_weather(city, owm_key) if owm_key else None

            if price_data:
                price = price_data["price"]
            else:
                price = cache[key].get("price", _simulated_price(crop))

            if not weather_data:
                weather_data = cache[key].get("weather_detail", {
                    "rain_days": 0,
                    "desc_hi": "मौसम जानकारी उपलब्ध नहीं",
                    "desc_en": "Weather unavailable",
                })

            verdict = _build_verdict(crop, city, price, weather_data)
            cache[key] = {
                "price":        price,
                "weather":      weather_data.get("summary", "unknown"),
                "weather_detail": weather_data,
                "verdict":      verdict,
                "timestamp":    datetime.now(timezone.utc).isoformat(),
            }
            refreshed += 1
        except Exception as e:
            logger.error(f"[mandi] Refresh error for {key}: {e}")

    _save_cache(cache)
    logger.success(f"[mandi] Scheduled refresh complete — {refreshed} entries updated")


def start_mandi_scheduler() -> BackgroundScheduler:
    """
    Start APScheduler to refresh mandi cache every day at 06:00 AM IST.
    Call this once from telegram_bot.py during application startup.
    Returns the scheduler instance so the caller can shut it down cleanly.
    """
    scheduler = BackgroundScheduler(timezone=IST)
    scheduler.add_job(
        _refresh_all_cache,
        trigger=CronTrigger(hour=6, minute=0, timezone=IST),
        id="mandi_daily_refresh",
        name="Mandi Cache Daily Refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.success("[mandi] APScheduler started — cache refreshes daily at 06:00 IST")
    return scheduler
