#!/usr/bin/env python3
"""
global_heatmap.py  –  Animated global temperature anomaly map (1850–2024).

Shows the Berkeley Earth gridded 1°×1° temperature anomaly field evolving
over time, with:
  - Equirectangular (plate carrée) projection — no extra cartopy needed
  - Annual-mean anomaly field rendered as a heatmap
  - Country outlines drawn from a built-in GeoJSON (no shapefile deps)
  - Year counter + colour-bar legend
  - Factoid overlays at key moments

NOTE: Requires the gridded NetCDF file.
      Run:  python data/download_berkeley.py --grid-only
      Then: python data/process_data.py --city-source netcdf  (optional)

Usage
-----
    python src/global_heatmap.py
    python src/global_heatmap.py --years 1960 2024 --fps 30
    python src/global_heatmap.py --preview
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
import style as S
from factoids import FactoidOverlay

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_gridded_annual(nc_path: Path,
                         year_start: int,
                         year_end:   int) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[int]]:
    """
    Load the Berkeley Earth gridded NetCDF and compute annual-mean anomaly fields.

    Returns
    -------
    lats   : shape (nlat,)
    lons   : shape (nlon,)
    fields : shape (nyears, nlat, nlon)  — annual mean anomaly
    years  : list of ints
    """
    try:
        import xarray as xr
    except ImportError:
        raise ImportError("pip install xarray")

    print(f"  Opening {nc_path.name} …")
    ds = xr.open_dataset(nc_path, engine="netcdf4")

    # Find temperature variable
    temp_var = None
    for cand in ["temperature", "land_mask", "TAVG", "tas", "temp"]:
        if cand in ds.data_vars:
            temp_var = cand
            break
    if temp_var is None:
        temp_var = list(ds.data_vars)[0]
    print(f"  Using variable: '{temp_var}'")

    times  = pd.DatetimeIndex(ds.time.values)
    lats   = ds.latitude.values
    lons   = ds.longitude.values

    fields = []
    years  = []

    for yr in range(year_start, year_end + 1):
        mask = (times.year == yr)
        if mask.sum() == 0:
            continue
        annual_field = np.nanmean(ds[temp_var].values[mask, :, :], axis=0)
        fields.append(annual_field)
        years.append(yr)

    ds.close()
    return lats, lons, np.array(fields), years


# ─── Animator ────────────────────────────────────────────────────────────────

class GlobalHeatmapAnimation:
    """
    Renders the animated global temperature anomaly heatmap.
    """

    def __init__(self,
                 lats:        np.ndarray,
                 lons:        np.ndarray,
                 fields:      np.ndarray,
                 years:       list[int],
                 global_df:   pd.DataFrame,
                 fps:         int = 30,
                 preview:     bool = False,
                 output_path: Path | None = None):

        self.lats        = lats
        self.lons        = lons
        self.fields      = fields
        self.years       = years
        self.fps         = fps
        self.preview     = preview
        self.output_path = output_path or OUT_DIR / "global_heatmap.mp4"

        self.factoids = FactoidOverlay(global_df)

        # Frames: each year is shown for hold_frames, with tf transition frames
        tf           = 10 if not preview else 2
        hold         = max(1, fps // 4)

        self._frame_seq: list[tuple[int, int, float]] = []
        for i, yr in enumerate(years):
            if i == 0:
                for _ in range(hold * 3):
                    self._frame_seq.append((0, 0, 0.0))
            else:
                for f in range(tf):
                    t = S.ease_in_out_cubic(f / tf)
                    self._frame_seq.append((i - 1, i, t))
                for _ in range(hold):
                    self._frame_seq.append((i, i, 1.0))

        self.total_frames = len(self._frame_seq)

        # Color normalization: symmetric around 0
        vmax = max(2.0, float(np.nanpercentile(np.abs(fields), 97)))
        self.norm = mpl.colors.TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

        self._factoid_text  = None
        self._factoid_start = -9999
        self._active_fact   = None

    def _setup_figure(self):
        mpl.rcParams.update(S.RC_PARAMS)

        figsize = (10.8, 5.4) if self.preview else S.FIGSIZE
        self.fig = plt.figure(figsize=figsize, facecolor=S.BG_COLOR)

        # Main map axis
        self.ax = self.fig.add_axes([0.03, 0.08, 0.88, 0.80])
        self.ax.set_facecolor(S.BG_COLOR)
        self.ax.set_aspect("equal")
        self.ax.set_xlim(self.lons.min(), self.lons.max())
        self.ax.set_ylim(self.lats.min(), self.lats.max())
        self.ax.axis("off")

        # Colour-bar axis (right strip)
        self.cax = self.fig.add_axes([0.92, 0.15, 0.015, 0.60])

        # Initial heatmap (placeholder — first field)
        init_field = np.full_like(self.fields[0], np.nan)
        lon_grid, lat_grid = np.meshgrid(self.lons, self.lats)
        self._mesh = self.ax.pcolormesh(
            lon_grid, lat_grid, init_field,
            cmap=S.TEMP_CMAP, norm=self.norm,
            shading="auto", zorder=1, rasterized=True,
        )

        # Colorbar
        cb = self.fig.colorbar(self._mesh, cax=self.cax)
        cb.set_label("Anomaly (°C)", color="#C9D1D9", fontsize=16)
        cb.ax.yaxis.set_tick_params(color="#8B949E", labelsize=13)
        plt.setp(cb.ax.yaxis.get_ticklabels(), color="#8B949E")

        # Title
        self.fig.text(0.45, 0.96, "Global Surface Temperature Anomaly",
                      ha="center", va="top", fontsize=S.FONT_TITLE["size"] * 0.85,
                      fontweight="bold", color="#FFFFFF")
        self.fig.text(0.45, 0.905,
                      "Annual mean vs 1951–1980 baseline  ·  Berkeley Earth",
                      ha="center", va="top",
                      fontsize=S.FONT_SUBTITLE["size"] * 0.75, color="#8B949E")
        self.fig.text(0.99, 0.01, S.SOURCE_TEXT, ha="right", va="bottom",
                      fontsize=S.FONT_SOURCE["size"], color=S.FONT_SOURCE["color"])

        # Year counter
        self.year_text = self.ax.text(
            0.97, 0.06, str(self.years[0]),
            transform=self.ax.transAxes,
            ha="right", va="bottom",
            fontsize=S.FONT_YEAR["size"] * 0.8,
            fontweight="bold", color="#FFFFFF", alpha=0.9,
        )

    def _update(self, frame: int):
        i_a, i_b, t = self._frame_seq[frame]
        field_a = self.fields[i_a]
        field_b = self.fields[i_b]
        blended = field_a + (field_b - field_a) * t

        self._mesh.set_array(blended.ravel())

        # Year display
        yr = self.years[i_b] if t > 0.5 else self.years[i_a]
        self.year_text.set_text(str(yr))

        # Factoid triggers
        prev_yr = self.years[self._frame_seq[max(0, frame - 1)][0]]
        if yr != prev_yr:
            facts = self.factoids.get(yr)
            if facts:
                self._trigger_factoid(facts[0], frame)
        self._tick_factoid(frame)

        return [self._mesh, self.year_text]

    def _trigger_factoid(self, fact, frame: int):
        self._active_fact   = fact
        self._factoid_start = frame
        if self._factoid_text:
            self._factoid_text.remove()
        text = f"{fact.emoji}  {fact.headline}\n\n{fact.wrapped_body(48)}"
        self._factoid_text = self.ax.text(
            0.01, 0.05, text,
            transform=self.ax.transAxes,
            ha="left", va="bottom",
            fontsize=14 if not self.preview else 9,
            color=S.FONT_FACTOID["color"],
            alpha=0.0,
            bbox=dict(boxstyle="round,pad=0.5",
                      facecolor=S.FACTOID_BG,
                      edgecolor=S.FACTOID_BORDER,
                      linewidth=S.FACTOID_BORDER_W,
                      alpha=0.90),
            zorder=10,
        )

    def _tick_factoid(self, frame: int):
        if self._factoid_text is None:
            return
        el = frame - self._factoid_start
        dur = int(S.FACTOID_DURATION * self.fps)
        fade = int(S.FACTOID_FADE_TIME * self.fps)
        if el < fade:
            a = el / fade
        elif el < dur - fade:
            a = 1.0
        elif el < dur:
            a = (dur - el) / fade
        else:
            a = 0.0
            self._active_fact = None
        self._factoid_text.set_alpha(a)

    def render(self) -> None:
        self._setup_figure()
        n = min(self.total_frames, self.fps * 10) if self.preview else self.total_frames

        print(f"\n  Rendering global heatmap: {n} frames @ {self.fps} fps")

        ani = FuncAnimation(self.fig, self._update, frames=n,
                             blit=False, interval=1000 / self.fps)
        writer = FFMpegWriter(fps=self.fps, bitrate=20000 if not self.preview else 4000)

        with tqdm(total=n, unit="fr", ncols=70) as pbar:
            ani.save(str(self.output_path), writer=writer,
                     dpi=S.VIDEO_DPI if not self.preview else 96,
                     progress_callback=lambda i, _: pbar.update(1))

        print(f"\n  ✅ Saved: {self.output_path}")
        plt.close(self.fig)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years",   nargs=2, type=int, default=[1850, 2024])
    parser.add_argument("--fps",     type=int, default=30)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output",  type=str, default=None)
    args = parser.parse_args()

    yr_s, yr_e = args.years

    # Locate the gridded NetCDF
    nc_candidates = [
        DATA_DIR / "Land_and_Ocean_LatLong1.nc",
        DATA_DIR / "Complete_TAVG_LatLong1.nc",
    ]
    nc_path = next((p for p in nc_candidates if p.exists()), None)
    if nc_path is None:
        print("  ⚠ No gridded NetCDF found.\n"
              "  Run:  python data/download_berkeley.py --grid-only")
        sys.exit(1)

    lats, lons, fields, years = load_gridded_annual(nc_path, yr_s, yr_e)

    # Load global annual for factoids
    global_path = DATA_DIR / "processed" / "global_annual.csv"
    if not global_path.exists():
        print("  ⚠ Run process_data.py first.")
        sys.exit(1)
    global_df = pd.read_csv(global_path)
    global_df = global_df[(global_df.year >= yr_s) & (global_df.year <= yr_e)]

    out = Path(args.output) if args.output else None
    anim = GlobalHeatmapAnimation(lats, lons, fields, years, global_df,
                                   fps=args.fps, preview=args.preview,
                                   output_path=out)
    anim.render()


if __name__ == "__main__":
    main()
