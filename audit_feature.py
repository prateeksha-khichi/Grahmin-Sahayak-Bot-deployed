"""
=============================================================================
audit_feature.py — /audit command helper
Feature 2: Decision Logger + Compliance Guardrail

Responsibilities:
  • log_decision()      — silently write a structured audit record to audit_log.json
  • get_audit_summary() — return the last 5 audit records as a formatted message
  • check_compliance()  — run every outgoing bot response through 3 compliance rules:
        1. Pesticide dosage must not exceed PM guidelines
        2. Loan interest rate must not be below RBI minimum (7%)
        3. During govt procurement window, MSP must be mentioned for crop selling advice
=============================================================================
"""

import json
import re
import os
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger
import pytz

# ─────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────

# Path to audit log (project root, next to this file)
AUDIT_LOG_FILE = Path(__file__).parent / "audit_log.json"

# India Standard Time
IST = pytz.timezone("Asia/Kolkata")

# RBI minimum lending rate (%) — below this is non-compliant
RBI_MIN_RATE = 7.0

# Government procurement season months (Rabi: Oct–Feb)
MSP_SEASON_MONTHS = {10, 11, 12, 1, 2}

# Keywords that indicate crop-selling advice was given
SELLING_KEYWORDS = [
    "बेचें", "बेचना", "sell", "selling", "मंडी", "mandi",
    "rate", "भाव", "price", "quintal", "क्विंटल",
]

# Keywords that indicate MSP was mentioned (compliance pass)
MSP_KEYWORDS = ["msp", "minimum support price", "न्यूनतम समर्थन मूल्य", "सरकारी खरीद"]

# ─────────────────────────────────────────────────────────────────────────────
# Pesticide dosage limits (ml or g per litre) as per PM Pesticide Guidelines
# Source: ICAR / Central Insecticides Board guidelines (2024)
# ─────────────────────────────────────────────────────────────────────────────
PESTICIDE_LIMITS = {
    # generic compound → max ml or g per litre of water
    "chlorpyrifos":  2.5,
    "imidacloprid":  0.5,
    "glyphosate":    5.0,
    "malathion":     2.0,
    "endosulfan":    0.0,   # Banned — any mention is non-compliant
    "monocrotophos": 0.0,   # Banned
    "cypermethrin":  1.0,
    "lambda-cyhalothrin": 0.5,
    "carbendazim":   1.0,
    "mancozeb":      2.5,
}

# ─────────────────────────────────────────
# AUDIT LOG HELPERS
# ─────────────────────────────────────────

def _load_audit_log() -> list:
    """Load audit records list from disk. Returns empty list on error."""
    if AUDIT_LOG_FILE.exists():
        try:
            with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            logger.warning(f"[audit] Log load error: {e}")
    return []


def _save_audit_log(records: list) -> None:
    """Persist the list of audit records to disk."""
    try:
        with open(AUDIT_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"[audit] Log save error: {e}")


# ─────────────────────────────────────────
# PUBLIC: LOG A DECISION
# ─────────────────────────────────────────

def log_decision(
    user_id: str,
    question_asked: str,
    data_source_used: str,
    rule_triggered: str,
    confidence_level: str,
    response_summary: str,
    compliance_flags: list | None = None,
) -> None:
    """
    Silently append a structured audit record to audit_log.json.

    Parameters
    ----------
    user_id          : Telegram user ID (string)
    question_asked   : The command or question the user sent
    data_source_used : e.g. "Agmarknet+OWM", "RAG", "LoanModel", "FraudModel"
    rule_triggered   : Which business rule produced this response
    confidence_level : "high" | "medium" | "low"
    response_summary : First 200 chars of the response sent
    compliance_flags : List of compliance violations found (empty = clean)
    """
    record = {
        "user_id":          user_id,
        "timestamp":        datetime.now(IST).isoformat(),
        "question_asked":   question_asked[:300],
        "data_source_used": data_source_used,
        "rule_triggered":   rule_triggered,
        "confidence_level": confidence_level,
        "response_summary": response_summary[:200],
        "compliance_flags": compliance_flags or [],
    }

    records = _load_audit_log()
    records.append(record)

    # Keep only the last 1000 records to prevent unbounded growth
    if len(records) > 1000:
        records = records[-1000:]

    _save_audit_log(records)
    logger.debug(f"[audit] Logged decision for user {user_id}: {rule_triggered}")


# ─────────────────────────────────────────
# PUBLIC: GET AUDIT SUMMARY FOR /audit COMMAND
# ─────────────────────────────────────────

def get_audit_summary(user_id: str | None = None, last_n: int = 5) -> str:
    """
    Return the last `last_n` audit records as a clean formatted Telegram message.
    If user_id is provided, filter to that user's records only.
    """
    records = _load_audit_log()

    if user_id:
        records = [r for r in records if str(r.get("user_id")) == str(user_id)]

    if not records:
        return (
            "📋 *Audit Log — पिछले निर्णय*\n\n"
            "कोई रिकॉर्ड नहीं मिला।\n"
            "No audit records found yet."
        )

    # Most recent last_n
    recent = records[-last_n:][::-1]  # newest first

    lines = ["📋 *Audit Log — पिछले 5 निर्णय / Last 5 Decisions*\n"]
    for i, r in enumerate(recent, 1):
        ts_raw = r.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_raw).strftime("%d %b %Y, %I:%M %p")
        except Exception:
            ts = ts_raw

        flags = r.get("compliance_flags", [])
        flag_str = ""
        if flags:
            flag_str = "\n   ⚠️ Compliance: " + " | ".join(flags)

        lines.append(
            f"*{i}.* 🕐 {ts}\n"
            f"   👤 User: `{r.get('user_id', '?')}`\n"
            f"   ❓ Query: {r.get('question_asked', '?')[:80]}\n"
            f"   📂 Source: {r.get('data_source_used', '?')}\n"
            f"   📌 Rule: {r.get('rule_triggered', '?')}\n"
            f"   🎯 Confidence: {r.get('confidence_level', '?')}\n"
            f"   💬 Response: _{r.get('response_summary', '?')[:100]}..._"
            f"{flag_str}\n"
        )

    return "\n".join(lines)


# ─────────────────────────────────────────
# COMPLIANCE ENGINE
# ─────────────────────────────────────────

def _check_pesticide_compliance(text: str) -> list[str]:
    """
    Rule 1: Pesticide dosage must not exceed PM guidelines.
    Scans for compound names and nearby numeric values.
    Returns list of violation strings (empty = compliant).
    """
    violations = []
    text_lower = text.lower()

    for compound, max_dose in PESTICIDE_LIMITS.items():
        if compound not in text_lower:
            continue

        if max_dose == 0.0:
            violations.append(
                f"BANNED_PESTICIDE:{compound.upper()}"
            )
            continue

        # Find numbers near the compound name (within 60 chars)
        pattern = rf"{re.escape(compound)}.{{0,60}}?(\d+\.?\d*)\s*(?:ml|g|gram|litre|liter)"
        matches = re.findall(pattern, text_lower)
        for m in matches:
            try:
                dose = float(m)
                if dose > max_dose:
                    violations.append(
                        f"PESTICIDE_OVERDOSE:{compound}:{dose}ml>{max_dose}ml_limit"
                    )
            except ValueError:
                pass

    return violations


def _check_loan_rate_compliance(text: str) -> list[str]:
    """
    Rule 2: Loan interest rate must not be below RBI minimum (7%).
    Scans for percentage patterns adjacent to interest-rate keywords.
    Returns list of violation strings.
    """
    violations = []
    text_lower = text.lower()

    rate_keywords = ["interest", "byaj", "ब्याज", "rate", "दर", "%"]
    has_rate_context = any(kw in text_lower for kw in rate_keywords)

    if not has_rate_context:
        return violations

    # Find all percentage values in text
    percent_pattern = r"(\d+\.?\d*)\s*%"
    matches = re.findall(percent_pattern, text)
    for m in matches:
        try:
            rate = float(m)
            if 0 < rate < RBI_MIN_RATE:
                violations.append(
                    f"LOAN_RATE_BELOW_RBI:{rate}%<{RBI_MIN_RATE}%_minimum"
                )
        except ValueError:
            pass

    return violations


def _check_msp_compliance(text: str) -> list[str]:
    """
    Rule 3: During govt procurement window, MSP must be mentioned
    whenever crop selling advice is given.
    Returns list of violation strings.
    """
    violations = []
    current_month = datetime.now(IST).month

    if current_month not in MSP_SEASON_MONTHS:
        return violations  # Outside procurement season — rule doesn't apply

    text_lower = text.lower()

    # Check if selling advice was given
    is_selling_advice = any(kw in text_lower for kw in SELLING_KEYWORDS)
    if not is_selling_advice:
        return violations

    # Check if MSP was mentioned
    msp_mentioned = any(kw in text_lower for kw in MSP_KEYWORDS)
    if not msp_mentioned:
        violations.append("MSP_NOT_MENTIONED:crop_selling_advice_during_procurement_season")

    return violations


# ─────────────────────────────────────────
# PUBLIC: CHECK COMPLIANCE
# ─────────────────────────────────────────

def check_compliance(response_text: str) -> tuple[str, list[str]]:
    """
    Run response_text through all 3 compliance rules.

    Returns
    -------
    (final_text, violations)
      final_text  : The (possibly modified) text to send to the user
      violations  : List of rule violation codes (empty = compliant)

    Behaviour:
    • BANNED_PESTICIDE   → block + replace with Hindi warning
    • PESTICIDE_OVERDOSE → append ⚠️ warning
    • LOAN_RATE_BELOW_RBI → append ⚠️ warning
    • MSP_NOT_MENTIONED  → append MSP reminder
    """
    all_violations = []

    pest_violations   = _check_pesticide_compliance(response_text)
    rate_violations   = _check_loan_rate_compliance(response_text)
    msp_violations    = _check_msp_compliance(response_text)

    all_violations = pest_violations + rate_violations + msp_violations

    final_text = response_text

    # ── Banned pesticide → hard block ────────────────────────────────────
    for v in pest_violations:
        if v.startswith("BANNED_PESTICIDE:"):
            compound = v.split(":")[1]
            final_text = (
                f"🚫 *यह जानकारी प्रदर्शित नहीं की जा सकती।*\n\n"
                f"इस संदेश में **{compound}** का उल्लेख था, जो भारत में "
                f"प्रतिबंधित कीटनाशक है। PM कीटनाशक दिशा-निर्देशों के अनुसार "
                f"यह जानकारी साझा करना उचित नहीं है।\n\n"
                f"*This message has been blocked.* It referenced **{compound}**, "
                f"a banned pesticide in India per PM Pesticide Guidelines."
            )
            logger.warning(f"[compliance] BLOCKED response — banned pesticide: {compound}")
            return final_text, all_violations

    # ── Pesticide overdose warning ────────────────────────────────────────
    for v in pest_violations:
        if v.startswith("PESTICIDE_OVERDOSE:"):
            parts = v.split(":")
            compound = parts[1] if len(parts) > 1 else "कीटनाशक"
            final_text += (
                f"\n\n⚠️ *कीटनाशक सावधानी*: {compound} की मात्रा PM दिशा-निर्देश "
                f"से अधिक बताई गई हो सकती है। कृपया कृषि अधिकारी से पुष्टि करें।\n"
                f"⚠️ *Pesticide Caution*: Dosage mentioned may exceed PM Guidelines. "
                f"Please confirm with a local agriculture officer."
            )
            logger.warning(f"[compliance] Pesticide overdose flag: {v}")

    # ── Loan rate warning ─────────────────────────────────────────────────
    for v in rate_violations:
        final_text += (
            f"\n\n⚠️ *RBI सूचना*: इस संदेश में उल्लिखित ब्याज दर RBI न्यूनतम "
            f"दर ({RBI_MIN_RATE}%) से कम है। कोई भी वैध बैंक इससे कम ब्याज पर "
            f"लोन नहीं देता — यह धोखाधड़ी का संकेत हो सकता है।\n"
            f"⚠️ *RBI Alert*: Interest rate mentioned is below RBI minimum "
            f"({RBI_MIN_RATE}%). No legitimate bank offers rates this low — "
            f"this may indicate a fraudulent scheme."
        )
        logger.warning(f"[compliance] Loan rate flag: {v}")

    # ── MSP reminder ──────────────────────────────────────────────────────
    for v in msp_violations:
        current_month = datetime.now(IST).month
        final_text += (
            f"\n\n📢 *MSP सूचना (सरकारी खरीद सीजन)*: अभी सरकारी खरीद खिड़की चल रही है। "
            f"न्यूनतम समर्थन मूल्य (MSP) पर बिक्री के लिए अपने नज़दीकी सरकारी खरीद केंद्र "
            f"(APMC/FCI) पर जाएं।\n"
            f"📢 *MSP Notice (Procurement Season)*: Govt procurement window is open. "
            f"Visit your nearest APMC/FCI centre to sell at Minimum Support Price (MSP)."
        )
        logger.warning(f"[compliance] MSP flag: {v}")

    return final_text, all_violations
