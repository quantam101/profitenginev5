FROM python:3.12-slim AS backend-base

WORKDIR /srv

# System deps for any native wheels + healthcheck curl
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt /srv/backend/requirements.txt
COPY code_merger /srv/code_merger
RUN pip install --no-cache-dir -r /srv/backend/requirements.txt \
 && pip install --no-cache-dir anthropic google-genai stripe

# Copy app
COPY backend /srv/backend
COPY pytest.ini /srv/pytest.ini
COPY pyproject.toml /srv/pyproject.toml

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fs http://localhost:8001/api/health || exit 1

CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8001"]
