# ── Build stage ────────────────────────────────────────────────────────────
FROM python:3.11-slim AS base

WORKDIR /app

# Install Python dependencies first (layer-cache friendly)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app ./app

# Copy SQL init scripts (available inside the container for reference / manual use)
COPY schema.sql demo_data.sql create_user_and_grants.sql ./

# Ensure the log directory exists
RUN mkdir -p /var/log

# Expose the Flask port
EXPOSE 5000

ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app/web.py \
    FLASK_ENV=production

# Auto-start the web application
CMD ["python", "app/web.py"]
