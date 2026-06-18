# FractalVision Lab Backend — Deployment Dockerfile
# Used for Railway/Render deployment only. Not used for local development.

FROM python:3.11-slim

WORKDIR /app

# opencv-python-headless has minimal system deps, but ensure basics are present
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
