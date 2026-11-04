FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=production \
    STORAGE_DIR=/data/storage

WORKDIR /srv

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

RUN useradd --create-home --uid 10001 folio \
    && mkdir -p /data/storage /srv/.cache \
    && chown -R folio:folio /data /srv/.cache
USER folio

# Uploads, per-user Chroma indexes, and the embedding model cache must survive restarts.
VOLUME ["/data/storage", "/srv/.cache"]

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
