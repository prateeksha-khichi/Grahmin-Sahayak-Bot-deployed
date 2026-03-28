"""
offline_migrate.py — Create offline_brain tables + seed static knowledge base
Run once:  python offline_migrate.py
"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))

from database.db import engine, SessionLocal
from database.models import Base
from database.offline_models import OfflineCache, MandiPriceHistory, StaticKnowledge, PrefetchLog
from sqlalchemy import inspect, text

# ── Create tables ────────────────────────────────────────────────────────────

def create_tables():
    print("📦 Creating offline brain tables...")
    Base.metadata.create_all(bind=engine, tables=[
        OfflineCache.__table__,
        MandiPriceHistory.__table__,
        StaticKnowledge.__table__,
        PrefetchLog.__table__,
    ])
    print("✅ Tables created")


# ── Static Knowledge Seed Data ────────────────────────────────────────────────

SEED_DATA = [

    # ── GOVERNMENT SCHEMES ────────────────────────────────────────────────────
    {
        "category": "scheme",
        "title": "PM-KISAN Yojana",
        "content_hi": (
            "🌾 *PM-KISAN योजना*\n\n"
            "• सरकार किसानों को ₹6,000/वर्ष देती है (3 किस्तों में ₹2,000-₹2,000)\n"
            "• पात्रता: भारतीय नागरिक किसान जिनके पास खेती योग्य जमीन हो\n"
            "• अपात्र: सरकारी कर्मचारी, आयकर दाता, संवैधानिक पदधारक\n"
            "• आवेदन: pmkisan.gov.in पर या नजदीकी CSC केंद्र पर\n"
            "• जरूरी दस्तावेज: आधार, बैंक खाता, जमीन के कागज"
        ),
        "content_en": (
            "🌾 *PM-KISAN Scheme*\n\n"
            "• Govt gives ₹6,000/year to farmers (3 installments of ₹2,000)\n"
            "• Eligible: Indian citizen farmers with cultivable land\n"
            "• Ineligible: Govt employees, income tax payers, constitutional post holders\n"
            "• Apply: pmkisan.gov.in or nearest CSC centre\n"
            "• Documents: Aadhaar, bank account, land records"
        ),
        "keywords": ["pm kisan", "pmkisan", "किसान सम्मान", "6000", "किस्त", "kisan samman"],
    },
    {
        "category": "scheme",
        "title": "Mudra Yojana",
        "content_hi": (
            "💼 *प्रधानमंत्री मुद्रा योजना*\n\n"
            "• Shishu: ₹50,000 तक — छोटे व्यवसाय के लिए\n"
            "• Kishore: ₹50,001 – ₹5 लाख — व्यवसाय विस्तार\n"
            "• Tarun: ₹5 लाख – ₹10 लाख — बड़े व्यवसाय\n"
            "• ब्याज: बैंक के अनुसार (8–12% वार्षिक)\n"
            "• कोई collateral नहीं चाहिए Shishu/Kishore में\n"
            "• आवेदन: किसी भी राष्ट्रीयकृत बैंक या NBFC में"
        ),
        "content_en": (
            "💼 *PM Mudra Yojana*\n\n"
            "• Shishu: Up to ₹50,000 — small startups\n"
            "• Kishore: ₹50,001 – ₹5 lakh — business expansion\n"
            "• Tarun: ₹5 lakh – ₹10 lakh — larger businesses\n"
            "• Interest: 8–12% p.a. (bank-dependent)\n"
            "• No collateral needed for Shishu/Kishore\n"
            "• Apply: Any nationalised bank or NBFC"
        ),
        "keywords": ["mudra", "मुद्रा", "shishu", "kishore", "tarun", "business loan", "व्यवसाय लोन"],
    },
    {
        "category": "scheme",
        "title": "Kisan Credit Card (KCC)",
        "content_hi": (
            "💳 *किसान क्रेडिट कार्ड (KCC)*\n\n"
            "• खेती के लिए क्रेडिट लाइन ₹3 लाख तक 7% ब्याज पर\n"
            "• 3% सब्सिडी — समय पर चुकाने पर प्रभावी ब्याज 4%\n"
            "• बीमा भी मिलता है: फसल + आकस्मिक \n"
            "• पात्रता: खेती करने वाले किसान, बटाईदार, खुद काश्तकार\n"
            "• बैंक: SBI, PNB, NABARD संबद्ध बैंक\n"
            "• दस्तावेज: खसरा-खतौनी, आधार, फोटो"
        ),
        "content_en": (
            "💳 *Kisan Credit Card (KCC)*\n\n"
            "• Credit line up to ₹3 lakh at 7% interest for farming\n"
            "• 3% subsidy — effective rate 4% on timely repayment\n"
            "• Includes insurance: crop + accidental\n"
            "• Eligible: Farmers, tenant farmers, sharecroppers\n"
            "• Banks: SBI, PNB, NABARD-affiliated banks\n"
            "• Documents: Land records, Aadhaar, photo"
        ),
        "keywords": ["kcc", "kisan credit", "किसान क्रेडिट", "credit card", "4%", "7%", "फसल ऋण"],
    },
    {
        "category": "scheme",
        "title": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "content_hi": (
            "🌧️ *प्रधानमंत्री फसल बीमा योजना (PMFBY)*\n\n"
            "• प्राकृतिक आपदा से फसल नुकसान पर मुआवजा\n"
            "• किसान प्रीमियम: खरीफ 2%, रबी 1.5%, बागवानी 5%\n"
            "• बाकी प्रीमियम केंद्र + राज्य सरकार भरती है\n"
            "• पात्रता: ऋणी और गैर-ऋणी दोनों किसान\n"
            "• आवेदन: बैंक, CSC, या pmfby.gov.in\n"
            "• समय सीमा: खरीफ के लिए जुलाई, रबी के लिए दिसंबर"
        ),
        "content_en": (
            "🌧️ *PM Fasal Bima Yojana (PMFBY)*\n\n"
            "• Compensation for crop loss due to natural calamities\n"
            "• Farmer premium: Kharif 2%, Rabi 1.5%, Horticulture 5%\n"
            "• Rest paid by central + state government\n"
            "• Eligible: Both loanee and non-loanee farmers\n"
            "• Apply: Bank, CSC, or pmfby.gov.in\n"
            "• Deadline: July for Kharif, December for Rabi"
        ),
        "keywords": ["pmfby", "fasal bima", "फसल बीमा", "crop insurance", "बाढ़", "सूखा", "flood"],
    },
    {
        "category": "scheme",
        "title": "Pradhan Mantri Awas Yojana (PMAY)",
        "content_hi": (
            "🏠 *प्रधानमंत्री आवास योजना (PMAY)*\n\n"
            "• ग्रामीण: कच्चे मकान वालों को ₹1.2-1.3 लाख सहायता\n"
            "• शहरी: EWS/LIG परिवारों को होम लोन पर 6.5% तक ब्याज सब्सिडी\n"
            "• पात्रता: जिनके पास पक्का मकान नहीं है\n"
            "• आय सीमा: शहरी EWS — ₹3 लाख/वर्ष तक\n"
            "• आवेदन: pmaymis.gov.in या ग्राम पंचायत"
        ),
        "content_en": (
            "🏠 *PM Awas Yojana (PMAY)*\n\n"
            "• Rural: ₹1.2–1.3 lakh assistance for kutcha house owners\n"
            "• Urban: 6.5% interest subsidy on home loan for EWS/LIG\n"
            "• Eligible: Those without pucca house\n"
            "• Income limit: Urban EWS — up to ₹3 lakh/year\n"
            "• Apply: pmaymis.gov.in or gram panchayat"
        ),
        "keywords": ["pmay", "awas", "आवास", "home", "मकान", "house", "gramin awas"],
    },

    # ── RBI / LOAN RULES ──────────────────────────────────────────────────────
    {
        "category": "loan_rule",
        "title": "RBI Loan Interest Rate Rules",
        "content_hi": (
            "🏦 *RBI ब्याज दर नियम 2024*\n\n"
            "• Repo Rate (Oct 2024): 6.50%\n"
            "• होम लोन: 8.5%–9.5% वार्षिक (बैंक अनुसार)\n"
            "• कृषि लोन: 7% (KCC), 4% (ब्याज सब्सिडी के साथ)\n"
            "• पर्सनल लोन: 10%–18%\n"
            "• माइक्रोफाइनेंस: अधिकतम 26% (RBI नियम)\n"
            "• अगर कोई बैंक 36% से ज्यादा ब्याज मांगे — शिकायत करें!\n"
            "• RBI हेल्पलाइन: 14440"
        ),
        "content_en": (
            "🏦 *RBI Interest Rate Rules 2024*\n\n"
            "• Repo Rate (Oct 2024): 6.50%\n"
            "• Home Loan: 8.5%–9.5% p.a.\n"
            "• Agri Loan: 7% (KCC), 4% (with interest subvention)\n"
            "• Personal Loan: 10%–18%\n"
            "• Microfinance: Max 26% (RBI mandate)\n"
            "• If any lender charges >36% — file complaint!\n"
            "• RBI Helpline: 14440"
        ),
        "keywords": ["rbi", "interest rate", "ब्याज दर", "repo", "loan rate", "लोन ब्याज", "14440"],
    },
    {
        "category": "loan_rule",
        "title": "Loan Repayment Rights",
        "content_hi": (
            "⚖️ *लोन चुकाने के आपके अधिकार*\n\n"
            "• बैंक बिना नोटिस के लोन वापस नहीं मांग सकता\n"
            "• EMI न चुकाने पर: 3 बार डिफ़ॉल्ट के बाद NPA\n"
            "• NPA से पहले बैंक Settlement offer कर सकता है\n"
            "• SARFAESI Act: बैंक संपत्ति लेने से पहले 60-दिन नोटिस देगा\n"
            "• Loan Ombudsman: bankingombudsman.rbi.org.in\n"
            "• किसान लोन माफ़ी: राज्य सरकार घोषणा पर निर्भर"
        ),
        "content_en": (
            "⚖️ *Your Loan Repayment Rights*\n\n"
            "• Bank cannot recall loan without notice\n"
            "• 3 missed EMIs → account becomes NPA\n"
            "• Bank must offer settlement before NPA\n"
            "• SARFAESI: 60-day notice before property seizure\n"
            "• Loan Ombudsman: bankingombudsman.rbi.org.in\n"
            "• Farmer loan waiver: depends on state govt announcement"
        ),
        "keywords": ["emi", "npa", "default", "sarfaesi", "repayment", "ombudsman", "माफ़ी", "waiver"],
    },

    # ── FRAUD PATTERNS ────────────────────────────────────────────────────────
    {
        "category": "fraud_pattern",
        "title": "WhatsApp Loan Fraud",
        "content_hi": (
            "🚨 *WhatsApp लोन धोखाधड़ी*\n\n"
            "❌ ये संकेत देखें — यह धोखाधड़ी है:\n"
            "• 'तुरंत लोन मिलेगा, कोई document नहीं चाहिए'\n"
            "• 'Processing fee / Registration fee पहले दो'\n"
            "• अनजान WhatsApp नंबर से offer\n"
            "• बहुत कम ब्याज का वादा (1–2%)\n\n"
            "✅ असली बैंक:\n"
            "• कभी पहले पैसे नहीं मांगता\n"
            "• Official website/branch से ही apply होता है\n"
            "• RBI registered होता है\n\n"
            "📞 शिकायत: cybercrime.gov.in | 1930"
        ),
        "content_en": (
            "🚨 *WhatsApp Loan Fraud*\n\n"
            "❌ Warning signs — this is fraud:\n"
            "• 'Instant loan, no documents needed'\n"
            "• 'Pay processing/registration fee first'\n"
            "• Offer from unknown WhatsApp number\n"
            "• Promise of very low interest (1–2%)\n\n"
            "✅ Real banks:\n"
            "• Never ask for money upfront\n"
            "• Apply only via official website/branch\n"
            "• Always RBI registered\n\n"
            "📞 Complaint: cybercrime.gov.in | 1930"
        ),
        "keywords": ["whatsapp loan", "instant loan", "processing fee", "धोखाधड़ी", "fraud", "fake loan", "1930"],
    },
    {
        "category": "fraud_pattern",
        "title": "Fake Government Scheme Fraud",
        "content_hi": (
            "🚨 *नकली सरकारी योजना धोखाधड़ी*\n\n"
            "❌ इनसे सावधान रहें:\n"
            "• 'PM KISAN में ₹10,000 बोनस मिलेगा — link पर click करें'\n"
            "• 'आधार अपडेट करो नहीं तो subsidy बंद'\n"
            "• OTP माँगना किसी भी scheme के लिए\n"
            "• Unknown app download करवाना\n\n"
            "✅ सरकारी जानकारी केवल:\n"
            "• pmkisan.gov.in, india.gov.in\n"
            "• नजदीकी CSC/ग्राम पंचायत\n"
            "• PM हेल्पलाइन: 1800-115-526"
        ),
        "content_en": (
            "🚨 *Fake Government Scheme Fraud*\n\n"
            "❌ Watch out for:\n"
            "• 'PM KISAN ₹10,000 bonus — click this link'\n"
            "• 'Update Aadhaar or subsidy stops'\n"
            "• Asking for OTP for any scheme\n"
            "• Making you download unknown apps\n\n"
            "✅ Official info only at:\n"
            "• pmkisan.gov.in, india.gov.in\n"
            "• Nearest CSC / Gram Panchayat\n"
            "• PM Helpline: 1800-115-526"
        ),
        "keywords": ["fake scheme", "नकली योजना", "otp", "link", "click", "bonus", "aadhaar update fraud"],
    },

    # ── CROP ADVISORY BY SEASON ───────────────────────────────────────────────
    {
        "category": "crop_advisory",
        "title": "Kharif Season Advisory (June–October)",
        "content_hi": (
            "🌱 *खरीफ फसल सलाह (जून–अक्टूबर)*\n\n"
            "• *धान/चावल*: जून 15 – जुलाई 15 में रोपाई करें\n"
            "  बीमारी से बचाव: Kresoxim-methyl spray करें\n"
            "• *सोयाबीन*: जुलाई 1-15 बोएं, Ridge & Furrow method\n"
            "• *कपास*: अप्रैल-मई रोपाई, Bt कपास अनुशंसित\n"
            "• *अरहर/tur*: जून-जुलाई, Rhizobium inoculation जरूर\n"
            "• *मक्का*: जून में बोएं, 60:40:20 kg NPK/हेक्टेयर\n\n"
            "⚠️ मानसून अनुमान: IMD — imd.gov.in/monsoon"
        ),
        "content_en": (
            "🌱 *Kharif Season Advisory (June–Oct)*\n\n"
            "• *Paddy/Rice*: Transplant June 15 – July 15\n"
            "  Disease control: Kresoxim-methyl spray\n"
            "• *Soybean*: Sow July 1–15, Ridge & Furrow method\n"
            "• *Cotton*: Plant April–May, Bt cotton recommended\n"
            "• *Tur/Arhar*: June–July, Rhizobium inoculation\n"
            "• *Maize*: Sow June, 60:40:20 kg NPK/hectare\n\n"
            "⚠️ Monsoon forecast: IMD — imd.gov.in/monsoon"
        ),
        "keywords": ["kharif", "खरीफ", "paddy", "rice", "soybean", "cotton", "maize", "tur", "monsoon", "june", "july"],
    },
    {
        "category": "crop_advisory",
        "title": "Rabi Season Advisory (November–March)",
        "content_hi": (
            "🌾 *रबी फसल सलाह (नवंबर–मार्च)*\n\n"
            "• *गेहूं*: नवंबर 1-20 बोएं, 120:60:40 NPK\n"
            "  पानी: बुवाई के 21, 42, 63, 84, 105 दिन बाद\n"
            "• *सरसों*: अक्टूबर 15 – नवंबर 15\n"
            "  Aphid control: Imidacloprid 17.8 SL\n"
            "• *चना*: अक्टूबर-नवंबर, खुश्क खेत में बोएं\n"
            "• *आलू*: अक्टूबर, Blight से बचाव जरूरी\n\n"
            "💡 गेहूं MSP 2024: ₹2,275/quintal"
        ),
        "content_en": (
            "🌾 *Rabi Season Advisory (Nov–March)*\n\n"
            "• *Wheat*: Sow Nov 1–20, 120:60:40 NPK\n"
            "  Irrigation at: 21, 42, 63, 84, 105 days after sowing\n"
            "• *Mustard*: Oct 15 – Nov 15\n"
            "  Aphid control: Imidacloprid 17.8 SL\n"
            "• *Gram*: Oct–Nov, sow in dry field\n"
            "• *Potato*: October, Blight prevention essential\n\n"
            "💡 Wheat MSP 2024: ₹2,275/quintal"
        ),
        "keywords": ["rabi", "रबी", "wheat", "गेहूं", "mustard", "सरसों", "gram", "चना", "potato", "november", "november"],
    },
]


def seed_knowledge(db):
    existing = db.query(StaticKnowledge).count()
    if existing > 0:
        print(f"⚠️  Static knowledge already has {existing} rows — skipping seed")
        return

    print(f"🌱 Seeding {len(SEED_DATA)} knowledge entries...")
    for row in SEED_DATA:
        db.add(StaticKnowledge(**row, updated_at=datetime.utcnow()))
    db.commit()
    print("✅ Knowledge base seeded")


def run_migration():
    print("\n" + "="*60)
    print("🧠 Offline Brain — Database Migration")
    print("="*60)
    create_tables()
    db = SessionLocal()
    try:
        seed_knowledge(db)
    finally:
        db.close()
    print("\n✅ Migration complete! Run the bot normally.\n")


if __name__ == "__main__":
    run_migration()
