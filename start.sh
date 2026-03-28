#!/bin/bash
# Ensures script errors cause crash to prevent half-deployments
set -e

echo "======================================"
echo "    STARTING GRAHMIN SAHAYAK BOT      "
echo "======================================"

# 1. Download the large machine learning model
# We do this here instead of Dockerfile so Railway Env Vars are available!
echo "📝 [1/3] Securing Large ML Model from Google Drive..."
python download_model.py

# 2. Build the FAISS Document Index for Retrieval/RAG
echo "📚 [2/3] Building RAG Local Index..."
python build_index.py

# 3. Set the required Port
# Railway assigns random ports. Using $PORT is MANDATORY. 8000 is our fallback.
PORT="${PORT:-8000}"

# 4. Run the API and the Telegram Bot concurrently
echo "🌐 [3/3] Igniting FastAPI Server on Port $PORT..."
# Start FastAPI backend in the background Using '&'
uvicorn api.main:app --host 0.0.0.0 --port $PORT &

echo "🤖 Igniting Telegram Bot listener..."
# Run the long-polling Telegram bot in the foreground (blocks script exit)
python bots/telegram_bot.py
