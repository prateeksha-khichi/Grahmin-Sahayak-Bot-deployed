<p align="center">
  <h1 align="center">🌾 Grahmin Sahayak</h1>
  <p align="center"><strong>Multi-Agent AI Orchestration System for Rural Financial Intelligence</strong></p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" />
    <img src="https://img.shields.io/badge/FastAPI-0.110+-green?logo=fastapi" />
    <img src="https://img.shields.io/badge/LLM-Groq%20Llama%203%2070B-purple" />
    <img src="https://img.shields.io/badge/VectorDB-FAISS-orange" />
    <img src="https://img.shields.io/badge/Platform-Telegram-blue?logo=telegram" />
    <img src="https://img.shields.io/badge/Deploy-HuggingFace%20Spaces-yellow?logo=huggingface" />
    <img src="https://img.shields.io/badge/License-MIT-lightgrey" />
  </p>
</p>

---

> **Grahmin Sahayak** (meaning *Rural Helper*) is an AI-powered Telegram bot that delivers financial guidance, scheme intelligence, fraud protection, and crop market advisory to rural farmers in India — in Hindi, via voice or text, even on a 2G connection.

---

## 📋 Table of Contents

- [The Problem](#-the-problem)
- [Solution Overview](#-solution-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Impact Model](#-impact-model)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚜 The Problem

India has 140 million small and marginal farmers. The majority:

- Are **eligible for government schemes** they have never received — only 42% of eligible farmers receive PM-KISAN due to information gaps
- **Cannot read formal bank notices** sent in English or complex legal language
- **Lose money to agricultural scams** — average rural fraud loss is ₹12,000 per incident
- **Sell crops below market price** due to information asymmetry with traders and middlemen
- **Miss loan deadlines** due to lack of guidance — 24% of eligible farmers miss KCC applications

Grahmin Sahayak solves all of this — through a single Telegram conversation.

---

## 💡 Solution Overview

Grahmin Sahayak is architected as an **Orchestrator-Based Multi-Agent System**. A central FastAPI controller detects intent and routes each query to a specialised AI agent that owns its tools, context, and output format.

```
User (Telegram) → FastAPI Orchestrator → Intent Detection → Agent Router
                                                           ├── RAG Agent        (Schemes)
                                                           ├── Loan Agent       (Eligibility)
                                                           ├── OCR Agent        (Documents)
                                                           ├── Fraud Agent      (Protection)
                                                           ├── Advisory Agent   (Mandi + Weather)
                                                           ├── Language Agent   (Localisation)
                                                           └── Audit Agent      (Compliance)
                                                                   ↕
                                              Groq LLM + FAISS + PostgreSQL + Redis
```

---

## ✨ Features

### 1. 📋 Scheme Intelligence — RAG Agent
Answers any question about government agricultural schemes, eligibility, and application steps.

- **How it works:** Embeds the user's query → retrieves top-k relevant chunks from FAISS vector index (built on 10+ official govt PDFs) → feeds context to Groq LLM
- **Guarantee:** Zero hallucination — every fact is sourced from official government documents
- **Example:** *"PM-Kisan ke liye kaun eligible hai?"* → Returns verified eligibility criteria with source reference

### 2. 🏦 Loan Eligibility Prediction — Loan Agent
Predicts KCC / agricultural loan eligibility using a trained ML model, with plain-language explanation.

- **How it works:** Collects 11 structured inputs → XGBoost inference → LLM wraps the prediction in Hindi with rationale and next steps
- **Guarantee:** Explainable prediction — not just yes/no, but *why* and *what to do next*
- **Inputs:** Income, land size, crop type, credit history, existing loans, repayment record, and 5 more

### 3. 📄 Document OCR Explainer — OCR Agent
Converts photos of bank notices, loan letters, and government documents into simple Hindi action items.

- **How it works:** EasyOCR extracts text from image → LLM simplifies into plain language → key deadlines, amounts, and contacts highlighted
- **Guarantee:** Converts formal English/legal language into simple actionable Hindi
- **Supported inputs:** JPEG/PNG photos of physical documents via Telegram

### 4. 🚨 Fraud Detection — Fraud Agent
Classifies suspicious messages, URLs, and scheme descriptions as SAFE / SUSPICIOUS / SCAM.

- **How it works:** Rule-based pattern matching → LLM semantic analysis → risk score computation → Hindi explanation
- **Guarantee:** Hybrid approach catches both known fraud templates and novel scam patterns
- **Categories detected:** Fake schemes, phishing links, impersonation scams, unauthorised loan agents

### 5. 📊 Mandi Advisory — Advisory Agent
Provides SELL / HOLD / WAIT recommendations based on live mandi prices and weather forecasts.

- **How it works:** Fetches Agmarknet mandi prices + OpenWeatherMap 5-day forecast → LLM synthesises with user's crop and quantity → recommendation with rationale
- **Offline-safe:** Redis cache (6hr TTL) serves data when APIs are unavailable
- **Example:** *"Mujhe aaj gehu bechna chahiye?"* → *"HOLD — rain expected will raise prices ₹40/quintal in 4 days"*

### 6. 🗣️ Language Agent — Localisation
Ensures every interaction is in the user's preferred Indian language, with voice input and output support.

- **Voice input:** Whisper ASR transcribes audio messages
- **Language detection:** langdetect identifies the language and adds a routing tag
- **Output:** Localised response with optional Hindi voice output via gTTS
- **Coverage:** First-class Hindi; extensible to all 22 scheduled Indian languages

### 7. 📋 Audit Agent — Compliance & Logging
Passively logs every interaction, agent decision, and confidence score for full compliance traceability.

- **How it works:** Async event subscriber — receives all agent outputs without slowing down response delivery
- **Stores:** session_id, user_id, agent_used, query, response, confidence, timestamp
- **Zero performance impact** — fully asynchronous, out-of-band

---

## 🏗️ Architecture

### Core Principles

| Principle | Implementation |
|---|---|
| **Agent Isolation** | Each agent is independently scoped — failures do not cascade |
| **Single Orchestrator** | One FastAPI controller; no direct agent-to-agent calls |
| **Offline-First** | FAISS runs locally; mandi/weather is Redis-cached |
| **Verified Outputs** | RAG answers grounded in official PDFs — no hallucination |
| **Full Auditability** | Every decision logged asynchronously to PostgreSQL |
| **Multilingual by Default** | Language detection happens before any agent is invoked |

### Request Lifecycle

```
1. User sends voice/text via Telegram
2. Whisper ASR (if voice) + Language Agent → language tag
3. NLP Intent Classifier → intent category
4. Orchestrator dispatches to correct agent
5. Agent fetches data (FAISS / ML / API / DB)
6. Groq LLM generates localised natural language response
7. Response delivered via Telegram + Audit Agent logs asynchronously
```

### Error Handling

| Scenario | Detection | Strategy |
|---|---|---|
| Incomplete input | Input validator | Fallback prompt with example |
| Low model confidence (<0.6) | Threshold check | Escalation to clarification |
| API timeout (>5s) | Async timeout | Serve from Redis cache |
| Unknown language | langdetect score <0.7 | Default to Hindi |
| Prompt injection attempt | Content safety classifier | Refuse + log, no response |
| DB write failure | Exception handler | Retry ×3 with backoff |

---

## 🛠️ Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **Interface** | Telegram Bot API + python-telegram-bot | 20.x |
| **TTS** | gTTS | 2.x |
| **Backend** | FastAPI + Uvicorn | 0.110+ / 0.29+ |
| **Runtime** | Python | 3.11 |
| **LLM** | Groq API (Llama 3 70B) | cloud |
| **ASR** | OpenAI Whisper v3 | local |
| **Embeddings** | Sentence Transformers MPNet-base-v2 | — |
| **Vector DB** | FAISS | 1.7.x |
| **Database** | Neon PostgreSQL | serverless |
| **Cache** | Redis | 7.x |
| **ML Model** | XGBoost / scikit-learn | 2.x / 1.4 |
| **OCR** | EasyOCR | 1.7+ |
| **Language ID** | langdetect | 1.0.9 |
| **Containers** | Docker | 24+ |
| **CI/CD** | GitHub Actions | — |
| **Deployment** | HuggingFace Spaces | free tier |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Docker 24+ (recommended)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Groq API Key (from [console.groq.com](https://console.groq.com))
- Neon PostgreSQL connection string
- Redis instance (local or cloud)

### Clone the Repository

```bash
git clone https://github.com/yourusername/grahmin-sahayak.git
cd grahmin-sahayak
```

### Using Docker (Recommended)

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Build and run all services
docker-compose up --build
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Build FAISS index from government PDFs
python scripts/build_faiss_index.py --pdf-dir ./data/govt_pdfs/

# Train / load loan ML model
python scripts/train_loan_model.py

# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Start the Telegram bot (separate terminal)
python bot/telegram_handler.py
```

---

## 🔐 Environment Variables

Create a `.env` file in the project root:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Groq LLM
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama3-70b-8192

# Database
DATABASE_URL=postgresql://user:pass@host/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# External APIs
AGMARKNET_API_KEY=your_agmarknet_key
OPENWEATHER_API_KEY=your_openweather_key

# App Config
LOG_LEVEL=INFO
CONFIDENCE_THRESHOLD=0.6
REDIS_TTL_HOURS=6
```

---

## 📁 Project Structure

```
grahmin-sahayak/
│
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── orchestrator.py          # Central agent router
│   ├── intent_classifier.py     # NLP intent detection
│   │
│   └── agents/
│       ├── rag_agent.py         # Scheme intelligence (FAISS + LLM)
│       ├── loan_agent.py        # Loan eligibility (XGBoost + LLM)
│       ├── ocr_agent.py         # Document OCR explainer
│       ├── fraud_agent.py       # Fraud detection (rules + LLM)
│       ├── advisory_agent.py    # Mandi + weather advisory
│       ├── language_agent.py    # ASR + language detection + TTS
│       └── audit_agent.py       # Async compliance logger
│
├── bot/
│   └── telegram_handler.py      # Telegram webhook handler
│
├── data/
│   ├── govt_pdfs/               # Official scheme PDFs (source of truth)
│   ├── faiss_index/             # Prebuilt FAISS index
│   └── models/                  # Trained XGBoost model
│
├── scripts/
│   ├── build_faiss_index.py     # Index builder from PDFs
│   └── train_loan_model.py      # ML model trainer
│
├── tests/
│   ├── test_agents/
│   └── test_orchestrator.py
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📡 API Reference

### POST `/webhook`
Telegram webhook endpoint. Receives all bot updates.

### POST `/query`
Direct API query (for testing without Telegram).

```json
{
  "user_id": "12345",
  "message": "PM-Kisan ke liye apply kaise karein?",
  "language": "hi",
  "session_id": "abc-123"
}
```

**Response:**
```json
{
  "agent_used": "rag_agent",
  "response": "PM-Kisan योजना के लिए आवेदन करने के लिए...",
  "confidence": 0.91,
  "sources": ["pm_kisan_guidelines_2023.pdf"],
  "session_id": "abc-123"
}
```

### POST `/ocr`
Submit a document image for OCR explanation.

```
Content-Type: multipart/form-data
Fields: file (image), user_id, language
```

---

## 📊 Impact Model

| Metric | Annual Estimate (100K Users) |
|---|---|
| Scheme benefits unlocked | ₹220 Crore |
| Fraud losses prevented | ₹62 Crore |
| Better crop pricing | ₹80 Crore |
| Loan defaults averted | ₹24 Crore |
| **Total estimated value** | **₹486 Crore** |
| Farmer time saved | 2.1 Crore hours |
| Infrastructure cost | ~₹12 Lakh/year |
| ROI ratio | **405x** |

Full methodology and assumptions → see [`docs/ImpactModel.pdf`](docs/ImpactModel.pdf)

---

## 🗺️ Roadmap

- [x] 7-agent orchestrator architecture
- [x] FAISS RAG over government PDFs
- [x] XGBoost loan eligibility model
- [x] EasyOCR document explainer
- [x] Hybrid fraud detection (rules + LLM)
- [x] Live mandi + weather advisory
- [x] Hindi voice input (Whisper) + output (gTTS)
- [x] Async audit logging (Neon PostgreSQL)
- [ ] DigiLocker integration for document verification
- [ ] 22-language support (Bhashini API integration)
- [ ] FPO (Farmer Producer Organisation) dashboard
- [ ] Bank BC (Business Correspondent) white-label mode
- [ ] Crop disease detection via image (vision model)
- [ ] Soil health card integration

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

```bash
# Fork and clone
git clone https://github.com/yourusername/grahmin-sahayak.git

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, add tests
pytest tests/

# Submit a pull request
```

---

## 📜 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [NABARD](https://www.nabard.org) for rural finance data
- [Agmarknet](https://agmarknet.gov.in) for mandi price API
- [Groq](https://groq.com) for ultra-fast LLM inference
- [HuggingFace](https://huggingface.co) for hosting

---

<p align="center">
  Built with ❤️ for India's farmers 
</p>
