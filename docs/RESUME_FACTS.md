# Resume Facts — Proof & Verification Ledger

Every claim below is tied to a command you can re-run locally or in CI. Observed outputs are from branch `feat/engineering-hardening` (before PR merge).

## 1. Backend Test Count, Security Hardening & CI
- **Claim:** `52` automated pytest tests (`51` unit/API/security tests + `1` live PostgreSQL migration test when `DATABASE_URL` is set) and Ruff lint (`0` errors), verified in GitHub Actions across Python `3.11` and `3.14` with a real PostgreSQL 16 service container.
- **What is enforced and tested:**
  - Streaming byte-size cap (`MAX_UPLOAD_SIZE_MB=10`, aborts at `64 KiB` chunk boundary with `413`).
  - Magic-byte format verification (`PNG`, `JPEG`, `WEBP`) + OpenCV decode verification, ignoring filename extensions and `Content-Type` headers (`415`/`400`).
  - Pre-decode header dimension & pixel-bomb guard (`MAX_IMAGE_DIMENSION=4096`, `MAX_IMAGE_PIXELS=16,777,216` enforced from `IHDR`/`SOF`/`VP8*` headers before `cv2.imdecode`, returning `413`).
  - Off-event-loop worker execution (`anyio.to_thread.run_sync`) with read (`408`) and compute (`504`) timeouts.
  - Strict CORS (`ALLOWED_ORIGINS` limited to frontend origin + localhost, wildcard `*` rejected at config validation).
- **Proof commands (in `fractalvision-backend/`):**
  - `ruff check .`
  - `pytest tests/ -v` (with `DATABASE_URL` exported to run all 52 tests including Postgres migrations)

## 2. Docker & Version-Controlled Migrations
- **Claim:** Single-command local dev stack (`backend + Postgres 16 + transactional migrations`) matching Cloud Run startup (`uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`), with SHA-256 tracked migrations in `migrations/` (`0001_initial_schema.sql`, `0002_seed_reference_data.sql`).
- **Proof commands (in `fractalvision-backend/`):**
  - `docker compose up --build`
  - `python scripts/migrate.py` (twice -> idempotent)
  - `docker images fractalvision-backend:local` (measured size: `847 MB`)

## 3. Frontend Stack, Modules, Tests & WASM Benchmark
- **Frontend stack (actual):** Next.js `16.2.7` (App Router), React `19.2.4`, TypeScript `^5` (strict), Tailwind CSS v4, D3.js `7.9`, Zustand `5`, jsPDF `4.2`, Emscripten C++ WASM (`6.0.0`).
- **Frontend checks (`fractalvision-frontend/`):** `npm run lint`, `npm run typecheck`, `npm run test` (`9` Vitest tests across `3` files), `npm run build`.
- **Interactive modules:** `6` interactive modules (`/lab`, `/compare`, `/explorer`, `/benchmarks`, `/coastline-paradox`, `/gallery`) across `9` total routes.
- **WASM vs JS benchmark (`npm run benchmark` in `fractalvision-frontend/`):**
  - `1024×1024` fractal fixtures: WASM is `1.40×–1.51×` faster (`2.59–4.20 ms` vs `3.85–6.36 ms`).
  - Small/dense early-exit inputs (`128×128`, `256×256 dense`): JS is `1.42×–4.02×` faster because V8 TurboFan compiles tight `Uint8Array` loops efficiently while WASM pays `malloc` + `HEAPU8.set` + C++ JSON round-tripping + `JSON.parse`.

## 4. "$0/month" Hosting Reality Check
- **Fits free tiers on paper:** Vercel Hobby (non-commercial only), Cloud Run compute free tier (`180k vCPU-s`, `360k GiB-s`, `2M req/mo`), Supabase Free (`500 MB DB`, `1 GB storage`, `5 GB egress`, daily keep-alive avoids 7-day pause), cron-job.org Free.
- **Caveat:** Measured backend Docker image is **847 MB**, exceeding Google Artifact Registry's **0.5 GB (512 MB)** billing-account free tier (`$0.10/GB-month` overage if old/large revisions remain stored). Actual live cloud billing dashboards were not accessed per task ground rules.
