# FractalVision Lab — API

FastAPI backend for scientific fractal dimension analysis using the box-counting method.

## Live API

**Backend:** https://fractalvision-backend-jt6d2.ondigitalocean.app  
**Frontend:** https://fractalvision-frontend.vercel.app

## What This Does

FractalVision Lab receives an uploaded image, preprocesses it with OpenCV (grayscale conversion, thresholding, optional edge/texture extraction), and applies the box-counting algorithm across multiple scales (powers of 2). It then performs ordinary least-squares linear regression on the resulting log-log data to estimate the fractal dimension D, where D is the slope of log(N) vs log(1/ε). The API returns D along with R², confidence intervals, residuals, a quality score, a complexity classification, and an optional threshold sensitivity report. This backend powers a Mathematics dissertation project on fractal dimensions of natural patterns (leaves, coastlines).

## API Endpoints

All endpoints are prefixed with `/api/v1`.

| Method | Endpoint | Description | Key Parameters | Response |
|--------|----------|-------------|----------------|----------|
| `GET` | `/health` | Health check with uptime | — | `{ status, version, uptime_seconds }` |
| `POST` | `/analyze` | Single image fractal analysis | `file` (image), `analysis_mode`, `threshold_method`, `threshold_value`, `invert`, `denoise`, `grid_offsets`, `run_sensitivity` | `AnalyzeResponse` — fractal dimension, R², intercept, standard error, 95% CI, box sizes/counts, log-log arrays, fitted values, residuals, foreground ratio, quality score, reliability, interpretation, complexity class, binary image (base64), optional sensitivity result |
| `GET` | `/fractals` | List available standard fractals | — | Array of `{ fractal_id, name, theoretical_dimension, max_iterations, description }` |
| `POST` | `/fractals/{fractal_id}/generate` | Generate a standard fractal and compute its box-counting dimension | `iterations`, `image_size`, `box_sizes` (optional) | `GenerateFractalResponse` — computed vs theoretical dimension, error %, R², image (base64), box sizes/counts, log-log arrays |

### Upload Validation

- **File size:** max 10 MB
- **Accepted types:** `image/jpeg`, `image/jpg`, `image/png`, `image/webp`
- Images are resized to max 1024px on the longest side before processing

## Core Algorithms

- **Box-counting algorithm** — Covers the binarized image with a grid of square boxes at each scale ε. Counts N(ε): the number of boxes containing at least one foreground pixel. Scales are auto-selected as powers of 2 from 4 up to `min(width, height) / 4`. Supports multiple grid-origin offsets (default: 0, 0.25, 0.5, 0.75) to reduce grid-alignment bias; the minimum count across offsets is used at each scale.

- **Log-log regression** — Computes log(1/ε) vs log(N(ε)) and fits via `scipy.stats.linregress`. The slope is the estimated fractal dimension D. Returns R² (goodness of fit), standard error of the slope, 95% confidence interval (z = 1.96), fitted values, and residuals. Rejects degenerate results where D falls outside [0.5, 2.1].

- **Image preprocessing** — Three analysis modes: `full_mask` (standard binary thresholding of the entire image), `boundary` (Otsu binarization followed by Canny edge detection, σ = 50–150), and `texture` (morphological gradient with a 3×3 kernel, then Otsu). Three threshold methods within `full_mask`: Otsu (automatic), adaptive (Gaussian, block size 11, C = 2), and manual (user-specified 0–255). Optional inversion of the binary image.

- **Quality scoring** — Computes a 0–100 quality score from R² and the number of box-counting scales. Scores ≥ 85 are classified as High reliability, ≥ 70 as Medium, below 70 as Low. Bonuses for R² ≥ 0.999; penalties for R² < 0.95, R² < 0.90, or fewer than 5 scales.

- **Threshold sensitivity analysis** — Tests how D changes when the threshold is varied by ±15 around the computed value. Computes standard deviation across the three test points; stable if σ < 0.05. Only available in `full_mask` mode with Otsu or manual thresholding.

- **Fractal interpretation engine** — Maps D into five complexity bands (Simple/Linear, Low, Moderate, High, Very High Complexity) with human-readable descriptions. Appends a low-R² warning when R² < 0.95.

- **Fractal generators** — Generates five standard mathematical fractals for validation: Cantor Set (D ≈ 0.6309), Koch Curve (D ≈ 1.2619), Koch Snowflake (D ≈ 1.2619), Sierpiński Triangle (D ≈ 1.5850), and Sierpiński Carpet (D ≈ 1.8928). Each is rendered as a binary image using OpenCV drawing primitives and analyzed with the same box-counting pipeline.

## Project Structure

```
fractalvision-backend/
├── app/
│   ├── api/
│   │   ├── deps.py                 # Rate limiter (slowapi, IP-based)
│   │   └── v1/
│   │       ├── router.py           # Aggregates all v1 route modules
│   │       ├── analyze.py          # POST /analyze, POST /analyze/batch
│   │       ├── fractals.py         # GET /fractals, POST /fractals/{id}/generate
│   │       ├── health.py           # GET /health
│   │       └── meta.py             # GET /meta/interpretation-bands
│   ├── core/
│   │   ├── box_counting.py         # Box-counting algorithm with grid offsets
│   │   ├── image_processing.py     # OpenCV preprocessing, thresholding, encoding
│   │   ├── regression.py           # OLS linear regression via scipy
│   │   ├── quality_score.py        # Quality scoring (0-100) and reliability
│   │   ├── sensitivity.py          # Threshold sensitivity analysis
│   │   ├── interpretation.py       # D-value bands and complexity classification
│   │   └── fractal_generators.py   # Standard fractal image generators
│   ├── models/
│   │   ├── enums.py                # AnalysisMode, ThresholdMethod, Reliability
│   │   ├── requests.py             # Pydantic request models
│   │   └── responses.py            # Pydantic response models
│   ├── utils/
│   │   ├── id_generator.py         # UUID generation
│   │   ├── image_validation.py     # Upload validation helpers
│   │   └── rate_limiter.py         # Rate limiter setup
│   ├── config.py                   # pydantic-settings configuration
│   └── main.py                     # FastAPI app entry point
├── tests/                          # pytest test suite (16 tests)
├── Procfile                        # DigitalOcean start command
├── .python-version                 # Python 3.14
└── requirements.txt
```

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

## Test Coverage

**16 pytest tests** covering:

- **Box counting** (3 tests) — `box_count` at multiple scales, `auto_select_box_sizes` for a 1024×1024 image, `run_box_counting` pipeline returning correct sizes and counts
- **Image processing** (7 tests) — `to_grayscale` conversion, `otsu_threshold` correctness, `manual_threshold` with value verification, `adaptive_threshold` returning None threshold, `mode_boundary` edge detection output, `mode_texture` morphological gradient output, `resize_if_needed` scaling and passthrough
- **Quality scoring** (2 tests) — High reliability at R² = 0.9995 with 7 scales, Low reliability at R² = 0.88 with 4 scales
- **Regression** (2 tests) — `linear_regression` on a perfect linear dataset (slope = 2, R² = 1.0), `compute_log_values` verifying log transform correctness
- **Sensitivity** (2 tests) — Threshold sensitivity on a synthetic checkerboard pattern (verifies output structure and stability flag), returns `None` when `computed_threshold` is `None` (adaptive mode)

```bash
pytest tests/
```

## Local Development

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

**Environment variables:**

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | Supabase service role key |
| `ALLOWED_ORIGINS` | No | Comma-separated CORS origins (default: `http://localhost:3000`) |
| `RATE_LIMIT_PER_MINUTE` | No | General rate limit (default: 60) |
| `ANALYSIS_RATE_LIMIT_PER_MINUTE` | No | Analysis endpoint rate limit (default: 10) |
| `MAX_UPLOAD_SIZE_MB` | No | Max upload size in MB (default: 10) |
| `MAX_IMAGE_DIMENSION` | No | Max image dimension in px (default: 2048) |

## Deployment

Deployed on **DigitalOcean App Platform** via GitHub auto-deploy on push to `main`.

- **Buildpack:** Python (auto-detected from `requirements.txt` and `.python-version`)
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Instance:** Basic ($10/mo), 1 GB RAM, Bangalore region
- **CORS:** Configured via `ALLOWED_ORIGINS` env var

## Related

- **Frontend:** [fractalvision-frontend](https://github.com/M3hul-raj/fractalvision-frontend)
