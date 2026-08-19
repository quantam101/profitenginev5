FROM python:3.12-slim

LABEL maintainer="dispatch@alreadyherellc.com"
LABEL description="Taylor — Already Here LLC AI Voice Secretary"

WORKDIR /app

# System dependencies
RUN apt-get update -qq && apt-get install -y -qq --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn[standard] aiohttp stripe twilio

# Copy project
COPY . /app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${TAYLOR_PORT:-8001}/health || exit 1

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "agents.taylor.server:app", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "2", \
     "--log-level", "info"]
