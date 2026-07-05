# FractalVision Lab — API

[![Live API](https://img.shields.io/badge/API-Live-brightgreen?logo=googlecloud&logoColor=white)](https://fractalvision-backend-43382945646.us-central1.run.app/api/v1/health)
[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=ffdd54)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-16%20passing-success?logo=pytest&logoColor=white)](#test-coverage)

FastAPI backend for scientific fractal dimension analysis using the box-counting method. Powers the [FractalVision Lab](https://fractalvision-frontend.vercel.app) web application.

> Receives an uploaded image, preprocesses it with OpenCV, applies the box-counting algorithm across multiple scales, and performs linear regression on the log-log data to estimate the fractal dimension D. Returns D along with R², confidence intervals, quality scores, sensitivity analysis, and complexity classification.

---

## Live

| Service | URL |
|---------|-----|
| **Backend API** | https://fractalvision-backend-43382945646.us-central1.run.app |
| **API Docs** | https://fractalvision-backend-43382945646.us-central1.run.app/docs |
| **Frontend** | https://fractalvision-frontend.vercel.app |

---

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check with uptime |
| `POST` | `/analyze` | Single image → fractal dimension analysis |
| `GET` | `/fractals` | List 5 standard fractal types |
| `POST` | `/fractals/{id}/generate` | Generate fractal at N iterations + compute D |

### `POST /analyze` — Full Parameters

**Request:** `multipart/form-data`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | binary | required | Image file (PNG, JPG, WEBP). Max 10 MB |
| `analysis_mode` | string | `full_mask` | `full_mask`, `boundary`, `texture` |
| `threshold_method` | string | `otsu` | `otsu`, `manual`, `adaptive` |
| `threshold_value` | integer | `128` | 0–255 (used when method = `manual`) |
| `invert` | boolean | `false` | Invert foreground/background |
| `denoise` | boolean | `false` | Apply non-local means denoising |
| `blur_level` | integer | `0` | Gaussian blur kernel (1→3×3, 2→5×5, 3→7×7) |
| `grid_offsets` | string | `"0,0.25,0.5,0.75"` | Comma-separated offset fractions |
| `run_sensitivity` | boolean | `false` | Run threshold sensitivity test |
| `run_rotation_sensitivity` | boolean | `false` | Run rotation sensitivity test |
| `adaptive_block_size` | integer | `11` | Block size for adaptive thresholding |
| `adaptive_c` | integer | `2` | Constant C for adaptive thresholding |

**Response:** `AnalyzeResponse` includes:
- `result` — D, R², intercept, standard error, confidence interval, box sizes/counts, log arrays, fitted values, residuals, foreground ratio, quality score, reliability, interpretation, complexity class, warnings
- `binary_image_b64` — base64-encoded PNG of the binary image
- `sensitivity` — threshold ±15 test results (or null)
- `rotation_sensitivity` — 5-angle rotation test results (or null)
- `processing_time_ms`

### `POST /fractals/{id}/generate`

**Request:** JSON body

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `iterations` | integer | required | Recursion depth (clamped per fractal) |
| `image_size` | integer | `1024` | Output image dimensions (square) |
| `box_sizes` | list[int] | `[]` | Custom box sizes (empty = auto) |

**Response:** `GenerateFractalResponse` — fractal_id, computed_dimension, theoretical_dimension, error_percentage, R², image_base64, box data, processing_time_ms

### Upload Validation

- **File size:** max 10 MB
- **Accepted types:** `image/jpeg`, `image/jpg`, `image/png`, `image/webp`
- Images resized to max 1024px on the longest side before processing

---

## Core Algorithms

- **Box-counting** — Covers the binarized image with a grid of square boxes at each scale ε. Counts N(ε): boxes containing ≥1 foreground pixel. Scales are powers of 2 from 4 to `min(w, h) / 4`. Supports multiple grid-origin offsets (default: 0, 0.25, 0.5, 0.75); minimum count across offsets is used at each scale to reduce grid-alignment bias.

- **Log-log regression** — Computes log(1/ε) vs log(N(ε)) and fits via `scipy.stats.linregress`. Slope = fractal dimension D. Returns R², standard error, 95% confidence interval (z = 1.96), fitted values, and residuals. Rejects degenerate results where D ∉ [0.5, 2.1].

- **Image preprocessing** — Three modes: `full_mask` (binary thresholding), `boundary` (Otsu → Canny edge, σ = 50–150), `texture` (morphological gradient → Otsu). Three threshold methods: Otsu, adaptive (Gaussian, configurable block size and C), manual. Optional Gaussian blur (3 levels) and non-local means denoising. Optional inversion.

- **Quality scoring** — 0–100 score from R², scale count, foreground ratio, sensitivity σ, and rotation σ. Reliability: High (≥85), Medium (≥70), Low (<70). Bonuses for R² ≥ 0.999; penalties for low R², few scales, extreme foreground ratios, high sensitivity.

- **Threshold sensitivity** — Re-runs analysis at threshold ±15. σ < 0.05 = Stable. Only available in `full_mask` mode with Otsu or manual thresholding.

- **Rotation sensitivity** — Re-runs at 0°, 15°, 30°, 45°, 90° using `cv2.warpAffine` with `INTER_NEAREST`. σ < 0.05 = Stable. Available in any mode.

- **Fractal interpretation** — Maps D into 5 complexity bands (Simple/Linear → Very High) with human-readable descriptions. Appends low-R² warning when R² < 0.95.

- **Fractal generators** — 5 standard fractals for algorithm validation: Cantor Set (D ≈ 0.6309), Koch Curve (D ≈ 1.2619), Koch Snowflake (D ≈ 1.2619), Sierpiński Triangle (D ≈ 1.5850), Sierpiński Carpet (D ≈ 1.8928). Each rendered as a binary image using OpenCV and analyzed with the same pipeline.

---

## Project Structure

```
fractalvision-backend/
├── app/
│   ├── api/
│   │   ├── deps.py                 # Rate limiter (slowapi, IP-based)
│   │   └── v1/
│   │       ├── router.py           # Aggregates all v1 route modules
│   │       ├── analyze.py          # POST /analyze (+ /analyze/batch stub)
│   │       ├── fractals.py         # GET /fractals, POST /fractals/{id}/generate
│   │       ├── health.py           # GET /health
│   │       └── meta.py             # GET /meta/interpretation-bands (stub)
│   ├── core/
│   │   ├── box_counting.py         # Box-counting algorithm with grid offsets
│   │   ├── image_processing.py     # OpenCV preprocessing, thresholding, encoding
│   │   ├── regression.py           # OLS linear regression via scipy
│   │   ├── quality_score.py        # Quality scoring (0-100) and reliability
│   │   ├── sensitivity.py          # Threshold + rotation sensitivity analysis
│   │   ├── interpretation.py       # D-value bands and complexity classification
│   │   └── fractal_generators.py   # Standard fractal image generators
│   ├── models/
│   │   ├── enums.py                # AnalysisMode, ThresholdMethod, Reliability
│   │   ├── requests.py             # Pydantic request models
│   │   └── responses.py            # Pydantic response models
│   ├── utils/
│   │   ├── id_generator.py         # UUID-based short ID generator
│   │   ├── image_validation.py     # Upload validation helpers
│   │   └── rate_limiter.py         # Rate limiter setup
│   ├── config.py                   # pydantic-settings configuration
│   └── main.py                     # FastAPI app entry point
├── tests/                          # pytest test suite (16 tests)
├── Dockerfile                      # Google Cloud Run deployment container
├── docker-compose.yml              # Docker Compose for local testing
├── .python-version                 # Python 3.14
└── requirements.txt                # 12 dependencies
```

---

## Tech Stack

| Package | Purpose |
|---------|---------|
| `fastapi` | ASGI web framework, auto-generated OpenAPI docs |
| `uvicorn[standard]` | ASGI server with uvloop and httptools |
| `python-multipart` | Multipart form data parsing for file uploads |
| `opencv-python-headless` | Image decoding, thresholding, edge detection, morphology |
| `numpy` | Array operations for box-counting and image manipulation |
| `scipy` | `scipy.stats.linregress` for OLS regression |
| `httpx` | Async HTTP client |
| `slowapi` | IP-based rate limiting (built on limits) |
| `python-dotenv` | `.env` file loading |
| `pydantic-settings` | Typed configuration from environment variables |
| `supabase` | Supabase client (used by data migration scripts) |
| `requests` | HTTP client (used by data migration scripts) |

**Python version:** 3.14 (pinned in `.python-version`)

---

## Test Coverage

**16 pytest tests** covering:

| Module | Tests | What's tested |
|--------|:-----:|---------------|
| Box counting | 3 | `box_count` at multiple scales, `auto_select_box_sizes` for 1024×1024, `run_box_counting` pipeline |
| Image processing | 7 | Grayscale, Otsu, manual, adaptive, boundary (Canny), texture (morph gradient), resize |
| Quality scoring | 2 | High reliability (R²=0.9995, 7 scales), Low reliability (R²=0.88, 4 scales) |
| Regression | 2 | Perfect linear dataset (slope=2, R²=1.0), log transform correctness |
| Sensitivity | 2 | Checkerboard stability, `None` return for adaptive mode |

```bash
pytest tests/
```

---

## Getting Started

### Prerequisites

- Python 3.14+
- pip

### Installation

```bash
# 1. Clone
git clone https://github.com/M3hul-raj/fractalvision-backend.git
cd fractalvision-backend

# 2. Create .env
cat > .env << 'EOF'
SUPABASE_URL=<your-supabase-url>
SUPABASE_SERVICE_KEY=<your-supabase-service-key>
ALLOWED_ORIGINS=http://localhost:3000
EOF

# 3. Create virtual environment
python -m venv .venv

# 4. Activate
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Run dev server
uvicorn app.main:app --reload --port 8000

# 7. Health check
curl http://localhost:8000/api/v1/health
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `SUPABASE_URL` | Yes | — | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | — | Supabase service role key |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | Comma-separated CORS origins |
| `RATE_LIMIT_PER_MINUTE` | No | `60` | General rate limit |
| `ANALYSIS_RATE_LIMIT_PER_MINUTE` | No | `10` | Analysis endpoint rate limit |
| `MAX_UPLOAD_SIZE_MB` | No | `10` | Max upload size in MB |
| `MAX_IMAGE_DIMENSION` | No | `2048` | Max image dimension in px |

---

## Deployment

Deployed on **Google Cloud Run** (us-central1, free tier) via Dockerfile.

| Setting | Value |
|---------|-------|
| Container | Python 3.11-slim with OpenCV system deps |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Resources | 1 GiB RAM, 1 vCPU |
| Scaling | 0–2 instances (scales to zero when idle) |
| Cost | $0/month (within free tier limits) |
| CORS | Configured via `ALLOWED_ORIGINS` env var |
| Keep-alive | cron-job.org pings `/api/v1/health` every 5 minutes |

> **Note:** The Docker image uses Python 3.11-slim because `opencv-python-headless` wheels are most reliable on that base image. Local development uses Python 3.14 (pinned in `.python-version`) — this has no impact on functionality.

---

## Related

- **Frontend:** [fractalvision-frontend](https://github.com/M3hul-raj/fractalvision-frontend) — Next.js 16 + TypeScript + D3.js + Emscripten WASM
