"""
One-time script to upload dissertation specimen images to Supabase Storage
and update the specimens table with their public URLs.

Usage:
    cd fractalvision-backend
    .venv\Scripts\activate
    python upload_images.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

# Load env vars from .env
load_dotenv(Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
# Strip /rest/v1/ if present (the Python client needs the base URL)
if SUPABASE_URL.endswith("/rest/v1"):
    SUPABASE_URL = SUPABASE_URL.replace("/rest/v1", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

BUCKET = "specimens"

# Dynamically find the dissertation folder (has a non-breaking space in the name)
import glob
diss_dirs = glob.glob(r"D:\Dissertation*")
if not diss_dirs:
    print("ERROR: Dissertation folder not found on D: drive")
    exit(1)
DISS_DIR = diss_dirs[0]
LEAVES = os.path.join(DISS_DIR, "Samples", "Leaves")
COASTLINES = os.path.join(DISS_DIR, "Samples", "Coastlines")

IMAGES = [
    (os.path.join(LEAVES, "Akondo_S.jpg"),             "leaves/akondo.jpg",             "spc_akondo"),
    (os.path.join(LEAVES, "Guava_S.jpg"),              "leaves/guava.jpg",              "spc_guava"),
    (os.path.join(LEAVES, "Lamiaceae.jpg"),             "leaves/lamiaceae.jpg",          "spc_lamiaceae"),
    (os.path.join(LEAVES, "MAngo_S.jpg"),              "leaves/mango.jpg",              "spc_mango"),
    (os.path.join(LEAVES, "Maple.jpg"),                "leaves/maple.jpg",              "spc_maple"),
    (os.path.join(LEAVES, "Monoon Longifolium_S.jpg"), "leaves/monoon-longifolium.jpg", "spc_monoon"),
    (os.path.join(LEAVES, "Peepal_S.jpg"),             "leaves/peepal.jpg",             "spc_peepal"),
    (os.path.join(COASTLINES, "coastline1.png"),       "coastlines/coastline-1.png",    "spc_coast1"),
    (os.path.join(COASTLINES, "coastline3.png"),       "coastlines/coastline-3.png",    "spc_coast3"),
    (os.path.join(COASTLINES, "coastline4.png"),       "coastlines/coastline-4.png",    "spc_coast4"),
    (os.path.join(COASTLINES, "coastline5.png"),       "coastlines/coastline-5.png",    "spc_coast5"),
]


def main():
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Service key:  ...{SUPABASE_SERVICE_KEY[-12:]}")
    print(f"Bucket:       {BUCKET}")
    print(f"Images:       {len(IMAGES)}")
    print("-" * 60)

    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    for local_path, storage_path, specimen_id in IMAGES:
        try:
            # Check local file exists
            if not os.path.isfile(local_path):
                print(f"[FAIL] {specimen_id} -> ERROR: File not found: {local_path}")
                continue

            # Read file bytes
            with open(local_path, "rb") as f:
                file_bytes = f.read()

            # Determine content type
            ext = os.path.splitext(local_path)[1].lower()
            content_type = "image/jpeg" if ext in (".jpg", ".jpeg") else "image/png"

            # Upload to Supabase Storage (upsert to overwrite if exists)
            supabase.storage.from_(BUCKET).upload(
                path=storage_path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )

            # Construct public URL
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"

            # Update database
            supabase.table("specimens").update({"image_url": public_url}).eq("id", specimen_id).execute()

            print(f"[OK] {specimen_id} -> {public_url}")

        except Exception as e:
            print(f"[FAIL] {specimen_id} -> ERROR: {e}")

    print("-" * 60)
    print("Done.")


if __name__ == "__main__":
    main()
