#!/usr/bin/env python3
"""
process_data.py  –  Parse Berkeley Earth files → clean pandas DataFrames.

Outputs (saved to data/processed/)
-----------------------------------
global_annual.csv        – year, anomaly, uncertainty (global mean)
global_monthly.csv       – year, month, anomaly, uncertainty
city_annual.csv          – year, city, anomaly   (extracted from NetCDF)
city_monthly.csv         – year, month, city, anomaly

Run:
    python data/process_data.py
    python data/process_data.py --city-source netcdf  # requires gridded NC
"""

from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).parent
OUT_DIR  = DATA_DIR / "processed"
OUT_DIR.mkdir(exist_ok=True)


# ─── Parser for Berkeley Earth text files ────────────────────────────────────

def parse_berkeley_text(filepath: Path) -> pd.DataFrame:
    """
    Parse a Berkeley Earth summary .txt file into a DataFrame.

    The format has a header of comment lines starting with '%', then
    whitespace-delimited columns:
        Year  Month  Anomaly  Unc(95%)
    or for annual summaries:
        Year  Anomaly  Unc(95%)
    """
    rows = []
    with open(filepath, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("%"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                nums = [float(p) for p in parts]
                rows.append(nums)
            except ValueError:
                continue

    if not rows:
        raise ValueError(f"No data rows found in {filepath}")

    n_cols = len(rows[0])
    if n_cols == 3:      # Year  Anomaly  Uncertainty
        df = pd.DataFrame(rows, columns=["year", "anomaly", "uncertainty"])
        df["year"] = df["year"].astype(int)
    elif n_cols == 4:    # Year  Month  Anomaly  Uncertainty
        df = pd.DataFrame(rows, columns=["year", "month", "anomaly", "uncertainty"])
        df["year"]  = df["year"].astype(int)
        df["month"] = df["month"].astype(int)
    else:
        # Fallback — store raw
        cols = [f"col{i}" for i in range(n_cols)]
        df = pd.DataFrame(rows, columns=cols)

    # Remove obviously invalid rows (NaN anomalies, year < 1700)
    if "anomaly" in df.columns:
        df = df[df["anomaly"].notna() & (df["anomaly"].abs() < 50)]
    if "year" in df.columns:
        df = df[df["year"] >= 1750]

    return df.reset_index(drop=True)


def build_global_annual(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Compute annual means from a monthly DataFrame."""
    agg = monthly_df.groupby("year").agg(
        anomaly     = ("anomaly",     "mean"),
        uncertainty = ("uncertainty", "mean"),
    ).reset_index()
    return agg.sort_values("year")


# ─── Extract city data from NetCDF grid ──────────────────────────────────────

def extract_city_from_netcdf(nc_path: Path, cities: list[dict]) -> pd.DataFrame:
    """
    Extract monthly temperature anomalies for each city from a Berkeley Earth
    gridded NetCDF file.

    The NetCDF has dimensions: (time, latitude, longitude)
    We find the nearest grid cell to each city's lat/lon.
    """
    try:
        import xarray as xr
    except ImportError:
        raise ImportError("Install xarray:  pip install xarray")

    print(f"  Opening {nc_path.name} …")
    ds = xr.open_dataset(nc_path, engine="netcdf4")

    # Berkeley Earth uses 'temperature' or 'land_mask' variable names
    # The anomaly variable is typically 'temperature'
    temp_var = None
    for candidate in ["temperature", "land_mask", "TAVG", "tas", "temp"]:
        if candidate in ds.data_vars:
            temp_var = candidate
            break
    if temp_var is None:
        temp_var = list(ds.data_vars)[0]
        print(f"  ⚠ Guessing temperature variable: '{temp_var}'")

    print(f"  Temperature variable: '{temp_var}'")
    print(f"  Time range: {str(ds.time.values[0])[:10]} → {str(ds.time.values[-1])[:10]}")

    # Decode time to year/month
    times = pd.DatetimeIndex(ds.time.values)
    years  = times.year
    months = times.month

    records = []
    for city in cities:
        name = city["name"]
        lat  = city["lat"]
        lon  = city["lon"]

        # Nearest grid point
        lat_idx = int(np.abs(ds.latitude.values  - lat).argmin())
        lon_idx = int(np.abs(ds.longitude.values - lon).argmin())

        vals = ds[temp_var].values[:, lat_idx, lon_idx]  # shape: (time,)

        for i, (yr, mo, val) in enumerate(zip(years, months, vals)):
            if not np.isnan(val):
                records.append({
                    "year":    int(yr),
                    "month":   int(mo),
                    "city":    name,
                    "country": city["country"],
                    "lat":     lat,
                    "lon":     lon,
                    "anomaly": float(val),
                    "color":   city.get("color", "#FFFFFF"),
                    "flag":    city.get("flag", ""),
                })

        print(f"    ✓ {name}: {len([r for r in records if r['city']==name])} months")

    ds.close()
    return pd.DataFrame(records)


# ─── Fallback: synthetic city data from global signal ────────────────────────

def synthesize_city_data(
    global_monthly: pd.DataFrame,
    cities: list[dict],
    seed: int = 42,
) -> pd.DataFrame:
    """
    When NetCDF is not available, synthesise plausible city data by adding
    realistic noise and local biases to the global signal.

    This is ONLY for development / testing.  Real NetCDF data should be used
    for publication.
    """
    rng = np.random.default_rng(seed)
    records = []

    # Latitude-based bias: higher latitudes warm faster (Arctic amplification)
    def lat_bias_scale(lat: float) -> float:
        return 1.0 + 1.5 * (abs(lat) / 90) ** 1.5

    for city in cities:
        scale = lat_bias_scale(city["lat"])
        # Persistent local offset (urban heat island, elevation, etc.)
        local_offset = rng.normal(0, 0.3)

        for _, row in global_monthly.iterrows():
            noise = rng.normal(0, 0.6)
            anom  = row["anomaly"] * scale + local_offset + noise
            records.append({
                "year":    row["year"],
                "month":   row["month"],
                "city":    city["name"],
                "country": city["country"],
                "lat":     city["lat"],
                "lon":     city["lon"],
                "anomaly": anom,
                "color":   city.get("color", "#FFFFFF"),
                "flag":    city.get("flag", ""),
            })

    return pd.DataFrame(records)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--city-source", choices=["netcdf", "synth"],
                        default="synth",
                        help="'netcdf' requires the gridded NC; 'synth' uses global signal")
    args = parser.parse_args()

    # Load city list
    cities_path = DATA_DIR / "cities.json"
    with open(cities_path) as f:
        cities_meta = json.load(f)["cities"]

    # ── Global monthly ──────────────────────────────────────────────────────
    monthly_txt = DATA_DIR / "Land_and_Ocean_complete.txt"
    if not monthly_txt.exists():
        print(f"  ⚠ Monthly text file not found at {monthly_txt}")
        print("     Run:  python data/download_berkeley.py")
        sys.exit(1)

    print("\n[1/4] Parsing global monthly anomalies …")
    global_monthly = parse_berkeley_text(monthly_txt)
    # Ensure month column exists (monthly file has 4 columns)
    if "month" not in global_monthly.columns:
        raise ValueError("Expected monthly file; got annual?  Check the URL.")

    global_monthly.to_csv(OUT_DIR / "global_monthly.csv", index=False)
    print(f"  → Saved global_monthly.csv  ({len(global_monthly)} rows)")

    # ── Global annual ───────────────────────────────────────────────────────
    print("\n[2/4] Computing global annual means …")
    global_annual = build_global_annual(global_monthly)
    global_annual.to_csv(OUT_DIR / "global_annual.csv", index=False)
    print(f"  → Saved global_annual.csv  ({len(global_annual)} rows, "
          f"{global_annual['year'].min()}–{global_annual['year'].max()})")

    # ── City data ───────────────────────────────────────────────────────────
    if args.city_source == "netcdf":
        nc_candidates = [
            DATA_DIR / "Land_and_Ocean_LatLong1.nc",
            DATA_DIR / "Complete_TAVG_LatLong1.nc",
        ]
        nc_path = next((p for p in nc_candidates if p.exists()), None)
        if nc_path is None:
            print("  ⚠ No gridded NetCDF found. Run with --grid-only flag first.")
            print("     Falling back to synthetic city data.")
            args.city_source = "synth"
        else:
            print(f"\n[3/4] Extracting city data from NetCDF: {nc_path.name} …")
            city_monthly = extract_city_from_netcdf(nc_path, cities_meta)

    if args.city_source == "synth":
        print("\n[3/4] Synthesising city data from global signal (dev mode) …")
        city_monthly = synthesize_city_data(global_monthly, cities_meta)

    city_monthly.to_csv(OUT_DIR / "city_monthly.csv", index=False)
    print(f"  → Saved city_monthly.csv  ({len(city_monthly)} rows)")

    # ── City annual ─────────────────────────────────────────────────────────
    print("\n[4/4] Computing city annual means …")
    city_annual = (
        city_monthly
        .groupby(["year", "city", "country", "lat", "lon", "color", "flag"])
        .agg(anomaly=("anomaly", "mean"))
        .reset_index()
        .sort_values(["city", "year"])
    )
    city_annual.to_csv(OUT_DIR / "city_annual.csv", index=False)
    print(f"  → Saved city_annual.csv  ({len(city_annual)} rows)")

    print("\n  ✅ All data processed.  Files in:", OUT_DIR.resolve())


import sys
if __name__ == "__main__":
    main()
