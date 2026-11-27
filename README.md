# FractalVision Lab — Backend API

[![Live API](https://img.shields.io/badge/API-Live-brightgreen?logo=googlecloud&logoColor=white)](https://fractalvision-backend-43382945646.us-central1.run.app/api/v1/health)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-3776AB?logo=python&logoColor=ffdd54)](https://www.python.org/)

FastAPI + OpenCV scientific compute API for box-counting fractal dimension analysis, statistical reliability diagnostics, and mathematical fractal generation.

- **Live API:** [https://fractalvision-backend-43382945646.us-central1.run.app](https://fractalvision-backend-43382945646.us-central1.run.app)
- **OpenAPI Docs:** [https://fractalvision-backend-43382945646.us-central1.run.app/docs](https://fractalvision-backend-43382945646.us-central1.run.app/docs)
- **Frontend:** [M3hul-raj/fractalvision-frontend](https://github.com/M3hul-raj/fractalvision-frontend) ([Live Demo](https://fractalvision-frontend.vercel.app))

---

## Architecture

```mermaid
flowchart LR
    FE["Next.js Frontend\n(Vercel)"] -->|"HTTPS + Strict CORS\nMultipart / JSON"| API["FastAPI App (Cloud Run)\napp/main.py"]
    API -->|"Streamed read + Magic bytes\n+ Pre-decode header bounds"| VAL["app/utils/image_validation.py"]
    VAL -->|"anyio.to_thread + wait_for timeout"| CORE["OpenCV + NumPy + SciPy\nbox_counting · regression · sensitivity"]
    MIG["scripts/migrate.py\n(migrations/*.sql)"] -->|"Local Dev / CI"| PG["PostgreSQL 16\n(Docker Compose / CI)"]
    FE -.->|"Direct read-only queries"| SUP["Supabase Postgres + Storage\n(Production Gallery)"]
```

---

## API Endpoints & Upload Hardening

All endpoints are served under `/api/v1`:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check with uptime |
| `POST` | `/analyze` | Analyze an uploaded JPEG/PNG/WEBP image and return $D$, $R^2$, CI, quality score, and sensitivity diagnostics |
| `GET` | `/fractals` | List the 5 standard mathematical fractals |
| `POST` | `/fractals/{id}/generate` | Generate a mathematical fractal at $N$ iterations and compute its empirical $D$ |
| `POST` | `/analyze/batch` | Unimplemented stub (returns HTTP `501`) |

### Untrusted Upload & Security Controls

- **Streaming byte-size limit (`413`):** `read_upload_limited()` reads uploads in 64 KiB chunks and aborts immediately past `MAX_UPLOAD_SIZE_MB` (default `10 MB`) without buffering oversized payloads.
- **Format verified by bytes, not extension/MIME (`415` / `400`):** Magic bytes (`PNG`, `JPEG`, `WEBP`) are verified and decoded via `cv2.imdecode`; disguised SVG/HTML/BMP/text payloads or corrupt images fail with clean 4xx responses (`415`/`400`), never `500`.
- **Decompression bomb protection (`413`):** PNG (`IHDR`), JPEG (`SOF`), and WEBP (`VP8`/`VP8L`/`VP8X`) headers are parsed *before* `cv2.imdecode()` to enforce `MAX_IMAGE_DIMENSION` (default `4096 px`) and `MAX_IMAGE_PIXELS` (default `16,777,216 px`).
- **Non-blocking execution & timeouts (`408` / `504`):** CPU-bound OpenCV/SciPy work runs in a worker thread via `anyio.to_thread.run_sync` wrapped in `asyncio.wait_for` (`UPLOAD_READ_TIMEOUT_SECONDS=10s`, `ANALYSIS_TIMEOUT_SECONDS=15s`).
- **Strict CORS:** Restricted to `ALLOWED_ORIGINS` (production Vercel frontend + localhost dev), `allow_credentials=False`, `GET`/`POST`/`OPTIONS` only, and wildcard `*` rejected at config validation.

---

## How to Run Locally

### Option 1: Docker Compose (Recommended — Backend + Postgres + Migrations)

```bash
git clone https://github.com/M3hul-raj/fractalvision-backend.git
cd fractalvision-backend
docker compose up --build
# API:      http://localhost:8000/api/v1/health
# Postgres: postgresql://fractalvision:fractalvision@localhost:5432/fractalvision
```

`docker compose up --build` starts PostgreSQL 16, waits for `pg_isready`, runs transactional SQL migrations (`scripts/migrate.py`), and boots Uvicorn with the same startup command used on Cloud Run.

### Option 2: Local Python Virtual Environment

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Database Migrations (Local / CI PostgreSQL)

Ordered SQL migrations live in `migrations/` (`0001_initial_schema.sql`, `0002_seed_reference_data.sql`) and are tracked with SHA-256 checksums in `schema_migrations`:

```bash
DATABASE_URL=postgresql://fractalvision:fractalvision@localhost:5432/fractalvision python scripts/migrate.py
```

---

## Test & Lint Commands

```bash
ruff check .       # Lint check (0 errors)
pytest tests/ -v   # 51 unit/API tests (+ 1 live Postgres migration test when DATABASE_URL is set = 52 total)
```

---

## Client-Side WASM Benchmark Summary

The companion frontend includes a reproducible JS-vs-WASM box-counting benchmark (`npm run benchmark` in `fractalvision-frontend`). On `1024×1024` fractal fixtures (10 warm-up, median of 30 runs), C++/Emscripten WASM is `1.40×–1.51×` faster than V8 JS (`2.59–4.20 ms` vs `3.85–6.36 ms`), while JS is `1.42×–4.02×` faster on small/early-exit images (`128×128`, `256×256 dense`) due to V8 TurboFan speed and JS–WASM buffer/JSON marshaling overhead.

---

## Limitations

- **Per-container in-memory rate limiting:** `slowapi` tracks request quotas in process memory, so limits are per Cloud Run instance rather than globally shared across scaled instances.
- **Finite-resolution raster analysis:** Uploaded images are downscaled to max `1024 px` before box-counting; regression rejects degenerate masks with $D \notin [0.5, 2.1]$ or fewer than 2 valid scales (`422`).
- **Batch endpoint unimplemented:** `POST /api/v1/analyze/batch` is intentionally disabled and returns HTTP `501`.
- **Container image size vs Cloud Run / Artifact Registry free tier:** The local `python:3.11-slim` + `opencv-python-headless` + `scipy` Docker image measures `847 MB`, which exceeds Google Artifact Registry's `0.5 GB` billing-account free storage tier unless older revisions are pruned or a paid tier covers storage (~`$0.10/GB-month`).
