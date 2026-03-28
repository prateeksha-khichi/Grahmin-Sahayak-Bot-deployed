# Use lightweight slim Python release for smaller image footprint
FROM python:3.11-slim

# Prevent python from producing pycache blocks (.pyc files)
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent python output buffering to safely monitor stdout logs in UI
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (ffmpeg is heavily required for audio processes)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    wget \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies first to cache this layer securely 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all the remaining project code directly into container
COPY . .

# IMPORTANT: Ensure the launch shell script has executable permissions
RUN chmod +x start.sh

EXPOSE 7860

# The script does model downloading, FAISS index builds, and boots Bot + backend
CMD ["bash", "start.sh"]
