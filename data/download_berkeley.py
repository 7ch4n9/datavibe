#!/usr/bin/env python3
"""
download_berkeley.py  –  Download Berkeley Earth temperature datasets.

Datasets downloaded
-------------------
1. Global land+ocean temperature anomaly (annual means, text)
2. Gridded land+ocean monthly anomaly (NetCDF, 1°×1°)  [~4 GB compressed]

Run from the project root:
    python data/download_berkeley.py [--full]

Pass --full to also download the large gridded NetCDF (needed for the
global heatmap animation). For city line charts, only the small file is
needed.
"""

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm

# ─── URLs ─────────────────────────────────────────────────────────────────────
URLS = {
    # Small files (< 5 MB each) — always downloaded
    "global_land_ocean_annual": (
        "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com"
        "/Global/Land_and_Ocean_summary.txt"
    ),
    "global_land_annual": (
        "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com"
        "/Global/Land_summary.txt"
    ),
    # Medium file — monthly global (needed for anomaly line chart)
    "global_land_ocean_monthly": (
        "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com"
        "/Global/Land_and_Ocean_complete.txt"
    ),
    # Large gridded NetCDF — only downloaded with --full flag (~4 GB)
    "gridded_land_ocean_monthly_nc": (
        "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com"
        "/Global/Gridded/Land_and_Ocean_LatLong1.nc"
    ),
}

# Alternative: use the smaller 1° gridded data from Berkeley Earth public S3
# This is faster to download (~200 MB) and good enough for city extraction
URLS_SMALL_GRID = {
    "gridded_land_monthly_nc": (
        "https://berkeley-earth-temperature.s3.us-west-1.amazonaws.com"
        "/Regional/TAVG/Complete_TAVG_LatLong1.nc"
    ),
}

DATA_DIR = Path(__file__).parent  # saves next to this script


def download_file(url: str, dest: Path, chunk_size: int = 1 << 20) -> None:
    """Stream-download a file with a tqdm progress bar."""
    if dest.exists():
        print(f"  ✓ Already downloaded: {dest.name}")
        return

    print(f"  ↓ {dest.name} ← {url}")
    r = requests.get(url, stream=True, timeout=60)
    r.raise_for_status()

    total = int(r.headers.get("content-length", 0))
    with open(dest, "wb") as f, tqdm(
        total=total, unit="B", unit_scale=True, unit_divisor=1024,
        desc=dest.name, ncols=80
    ) as bar:
        for chunk in r.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            bar.update(len(chunk))


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Berkeley Earth datasets")
    parser.add_argument("--full", action="store_true",
                        help="Also download large gridded NetCDF (~4 GB)")
    parser.add_argument("--grid-only", action="store_true",
                        help="Download only the small gridded NC (~200 MB)")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("\n═══ Berkeley Earth Temperature Data Downloader ═══\n")

    # Always get the summary / monthly files
    core_keys = ["global_land_ocean_annual", "global_land_annual",
                 "global_land_ocean_monthly"]
    for key in core_keys:
        url  = URLS[key]
        dest = DATA_DIR / Path(url).name
        download_file(url, dest)

    # Gridded data
    if args.full:
        url  = URLS["gridded_land_ocean_monthly_nc"]
        dest = DATA_DIR / Path(url).name
        print(f"\n  ⚠ Large file (~4 GB). This may take a while …")
        download_file(url, dest)
    elif args.grid_only:
        url  = URLS_SMALL_GRID["gridded_land_monthly_nc"]
        dest = DATA_DIR / Path(url).name
        download_file(url, dest)
    else:
        print("\n  ℹ  Skipping gridded NetCDF. Use --grid-only (~200 MB) or "
              "--full (~4 GB) to download.")

    print("\n  ✅ Done! Files saved to:", DATA_DIR.resolve())


if __name__ == "__main__":
    main()
