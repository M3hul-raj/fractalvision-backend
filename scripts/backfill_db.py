# NOTE: This is a local one-off maintenance script, not part of the deployed app.
"""
One-time script to backfill empty array columns in the Supabase 'specimens' table
and update fractal_dimension/r_squared/intercept with freshly computed values
if the delta is within an acceptable range (<= 0.05).

Usage:
    cd fractalvision-backend
    .venv\Scripts\activate
    python scripts/backfill_db.py
"""

import os
import glob
import requests
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env vars from .env (parent directory)
load_dotenv(Path(__file__).parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL.replace("/rest/v1", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

API_URL = "http://127.0.0.1:8000/api/v1/analyze"

# Dynamically find the dissertation folder (has a non-breaking space in the name)
diss_dirs = glob.glob(r"D:\Dissertation*")
if not diss_dirs:
    print("ERROR: Dissertation folder not found on D: drive")
    exit(1)
DISS_DIR = diss_dirs[0]
LEAVES = os.path.join(DISS_DIR, "Samples", "Leaves")
COASTLINES = os.path.join(DISS_DIR, "Samples", "Coastlines")

IMAGES = [
    (os.path.join(LEAVES, "Akondo_S.jpg"), "spc_akondo"),
    (os.path.join(LEAVES, "Guava_S.jpg"), "spc_guava"),
    (os.path.join(LEAVES, "Lamiaceae.jpg"), "spc_lamiaceae"),
    (os.path.join(LEAVES, "MAngo_S.jpg"), "spc_mango"),
    (os.path.join(LEAVES, "Maple.jpg"), "spc_maple"),
    (os.path.join(LEAVES, "Monoon Longifolium_S.jpg"), "spc_monoon"),
    (os.path.join(LEAVES, "Peepal_S.jpg"), "spc_peepal"),
    (os.path.join(COASTLINES, "coastline1.png"), "spc_coast1"),
    (os.path.join(COASTLINES, "coastline3.png"), "spc_coast3"),
    (os.path.join(COASTLINES, "coastline4.png"), "spc_coast4"),
    (os.path.join(COASTLINES, "coastline5.png"), "spc_coast5"),
]

def main():
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"API URL:      {API_URL}")
    print("-" * 60)

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    updated_count = 0
    skipped_missing = 0

    for local_path, specimen_id in IMAGES:
        # a. Check if file exists
        if not os.path.isfile(local_path):
            print(f"[WARN] {specimen_id}: File not found, skipping. ({local_path})")
            skipped_missing += 1
            continue
        
        try:
            # b. Fetch currently stored 'fractal_dimension'
            res = supabase.table("specimens").select("fractal_dimension").eq("id", specimen_id).execute()
            if not res.data:
                print(f"[WARN] {specimen_id}: Not found in database, skipping.")
                skipped_missing += 1
                continue
            
            stored_d = res.data[0]["fractal_dimension"]

            # c. POST the image to local backend
            with open(local_path, "rb") as f:
                response = requests.post(
                    API_URL,
                    data={"analysis_mode": "full_mask", "threshold_method": "otsu"},
                    files={"file": (os.path.basename(local_path), f, "image/jpeg")}
                )

            if response.status_code != 200:
                print(f"[FAIL] {specimen_id}: API request failed with status {response.status_code}. {response.text}")
                continue

            data = response.json()["result"]

            # d. Parse JSON response
            computed_d = data["fractal_dimension"]
            box_sizes = data["box_sizes"]
            box_counts = data["box_counts"]
            log_inverse_sizes = data["log_inverse_sizes"]
            log_counts = data["log_counts"]
            r_squared = data["r_squared"]
            intercept = data["intercept"]

            # e. Compute delta
            delta = abs(computed_d - stored_d)

            # f. Print comparison line
            print(f"{specimen_id}: stored D={stored_d:.4f}, computed D={computed_d:.4f}, delta={delta:.4f}")

            # h. Run Supabase update
            update_data = {
                "box_sizes": box_sizes,
                "box_counts": box_counts,
                "log_inverse_sizes": log_inverse_sizes,
                "log_counts": log_counts,
                "fractal_dimension": computed_d,
                "r_squared": r_squared,
                "intercept": intercept
            }
            supabase.table("specimens").update(update_data).eq("id", specimen_id).execute()
            print(f"  \033[92m[OK] Updated DB for {specimen_id}\033[0m")
            updated_count += 1

        except Exception as e:
            print(f"[ERROR] {specimen_id}: {e}")

    print("-" * 60)
    print(f"Summary: {updated_count} updated, {skipped_missing} skipped (missing)")

if __name__ == "__main__":
    main()
