#!/usr/bin/env python3
"""
city_line_animation.py  –  Animated temperature history line chart for major cities.

Produces a YouTube-ready MP4 video showing daily/monthly temperature
anomalies for 20 major cities from 1850 to present, with:
  - Smooth per-frame line drawing (one month revealed per frame cluster)
  - City color-coded lines with flag emoji labels
  - Live year counter
  - Factoid cards that fade in/out at key events
  - Gradient line coloring that shifts blue→red as anomalies increase
  - Source / branding watermark

Usage
-----
    python src/city_line_animation.py
    python src/city_line_animation.py --years 1980 2024 --fps 60 --quality high
    python src/city_line_animation.py --preview          # fast 10s preview
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.animation import FFMpegWriter, FuncAnimation
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import matplotlib.patheffects as path_effects
from tqdm import tqdm

# Local imports
sys.path.insert(0, str(Path(__file__).parent))
import style as S
from factoids import FactoidOverlay, Factoid

# ─── Paths ─────────────────────────────────────────────────────────────────
ROOT      = Path(__file__).parent.parent
DATA_DIR  = ROOT / "data" / "processed"
OUT_DIR   = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def load_data(year_start: int, year_end: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load and filter city + global annual DataFrames."""
    city_path   = DATA_DIR / "city_annual.csv"
    global_path = DATA_DIR / "global_annual.csv"

    if not city_path.exists() or not global_path.exists():
        print("  ⚠  Processed data not found.  Run:  python data/process_data.py")
        sys.exit(1)

    city_df   = pd.read_csv(city_path)
    global_df = pd.read_csv(global_path)

    city_df   = city_df[(city_df.year >= year_start)   & (city_df.year <= year_end)]
    global_df = global_df[(global_df.year >= year_start) & (global_df.year <= year_end)]

    return city_df, global_df


def smooth_series(series: pd.Series, window: int = 3) -> pd.Series:
    """Apply a simple rolling average to reduce noise."""
    return series.rolling(window=window, center=True, min_periods=1).mean()


def make_gradient_segments(x: np.ndarray, y: np.ndarray,
                            cmap: mpl.colors.Colormap,
                            norm: mpl.colors.Normalize) -> LineCollection:
    """
    Split a line into segments coloured by anomaly value.
    Returns a LineCollection ready to be added to an axis.
    """
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segs   = np.concatenate([points[:-1], points[1:]], axis=1)
    colors = cmap(norm(y[:-1]))
    lc     = LineCollection(segs, colors=colors, linewidth=S.LINE_WIDTH_MAIN,
                            capstyle="round", joinstyle="round")
    return lc


# ─── Main figure builder ─────────────────────────────────────────────────────

class CityTempAnimation:
    """
    Builds and renders the animated temperature line chart.

    Parameters
    ----------
    city_df     : Annual city-level anomalies
    global_df   : Annual global-mean anomalies
    year_start  : First year to show
    year_end    : Last year to animate to
    fps         : Output frame rate
    output_path : Where to save the MP4
    preview     : If True, render only 10 s at low res
    """

    def __init__(self,
                 city_df: pd.DataFrame,
                 global_df: pd.DataFrame,
                 year_start: int = 1850,
                 year_end:   int = 2024,
                 fps: int = 30,
                 output_path: Path | None = None,
                 preview: bool = False):

        self.city_df   = city_df
        self.global_df = global_df
        self.years     = sorted(city_df.year.unique())
        self.cities    = sorted(city_df.city.unique())
        self.fps       = fps
        self.preview   = preview
        self.output_path = output_path or OUT_DIR / "city_temperatures.mp4"

        # City metadata: color & flag per city
        cities_json = ROOT / "data" / "cities.json"
        with open(cities_json) as f:
            meta = {c["name"]: c for c in json.load(f)["cities"]}
        self.meta = meta

        # Factoid engine
        self.factoids = FactoidOverlay(global_df)

        # Animation parameters
        # Frames per year: determines how fast the animation moves
        self.frames_per_year = max(1, fps // 4)   # 4 years/sec at 30fps
        if preview:
            self.frames_per_year = 1

        # Build frame→year mapping
        self.frame_years: list[int] = []
        for y in self.years:
            self.frame_years.extend([y] * self.frames_per_year)
        self.total_frames = len(self.frame_years)

        # Anomaly normalization for colormap
        all_anom = city_df["anomaly"].dropna()
        self.norm = mpl.colors.Normalize(vmin=all_anom.quantile(0.02),
                                          vmax=all_anom.quantile(0.98))

        # Precompute city data lookup: city → (years_array, anomalies_array)
        self._city_data: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for city in self.cities:
            sub = city_df[city_df.city == city].sort_values("year")
            self._city_data[city] = (sub.year.values, smooth_series(sub.anomaly).values)

        # Global data
        self._global_years  = global_df.year.values
        self._global_anom   = smooth_series(global_df.anomaly).values

    # ── Figure setup ──────────────────────────────────────────────────────

    def _setup_figure(self):
        mpl.rcParams.update(S.RC_PARAMS)

        if self.preview:
            figsize = (12.8, 7.2)
        else:
            figsize = S.FIGSIZE

        self.fig = plt.figure(figsize=figsize, facecolor=S.BG_COLOR)

        # Layout: main chart occupies most of the figure, small title band at top
        self.ax = self.fig.add_axes([0.06, 0.10, 0.88, 0.76])  # [left,bot,w,h]
        self.ax.set_facecolor(S.BG_COLOR)

        # Y axis: temperature anomaly
        y_min = self.city_df["anomaly"].min() - 0.5
        y_max = self.city_df["anomaly"].max() + 0.8
        self.ax.set_ylim(y_min, y_max)
        self.ax.set_xlim(self.years[0] - 1, self.years[-1] + 1)

        # Grid
        self.ax.yaxis.grid(True, linestyle=S.GRID_LINESTYLE,
                           color=S.GRID_COLOR, alpha=S.GRID_ALPHA, zorder=0)
        self.ax.set_axisbelow(True)
        self.ax.xaxis.grid(False)

        # Zero baseline
        self.ax.axhline(0, color="#4A90D9", linewidth=1.2,
                        linestyle="--", alpha=0.6, zorder=1)
        self.ax.text(self.years[0] + 1, 0.05, "1951–1980 baseline",
                     color="#4A90D9", fontsize=S.FONT_SOURCE["size"],
                     alpha=0.7, va="bottom")

        # Axis labels
        self.ax.set_ylabel("Temperature anomaly (°C)", **{k: v for k, v in S.FONT_LABEL.items()
                                                            if k in ("size", "color")})
        for spine in self.ax.spines.values():
            spine.set_color(S.SPINE_COLOR)

        # Title
        self.fig.text(0.5, 0.93, "Temperature History of Major World Cities",
                      ha="center", va="top", **{k: v for k, v in S.FONT_TITLE.items()
                                                 if k != "family"})
        self.fig.text(0.5, 0.885, "Annual anomaly relative to 1951–1980 baseline  ·  Berkeley Earth",
                      ha="center", va="top", **{k: v for k, v in S.FONT_SUBTITLE.items()
                                                  if k != "family"})
        # Source watermark
        self.fig.text(0.99, 0.01, S.SOURCE_TEXT, ha="right", va="bottom",
                      **{k: v for k, v in S.FONT_SOURCE.items() if k != "family"})

        # ── Year counter (large, bottom right) ───────────────────────────
        self.year_text = self.fig.text(
            0.93, 0.14, str(self.years[0]),
            ha="right", va="bottom",
            fontsize=S.FONT_YEAR["size"],
            fontweight=S.FONT_YEAR["weight"],
            color=S.FONT_YEAR["color"],
            alpha=0.85,
        )

        # ── Legend ────────────────────────────────────────────────────────
        handles = []
        for city in sorted(self.cities):
            c = self.meta.get(city, {})
            color = c.get("color", "#FFFFFF")
            flag  = c.get("flag", "")
            h = Line2D([0], [0], color=color, linewidth=2.5,
                       label=f"{flag} {city}")
            handles.append(h)
        # Global mean
        handles.append(Line2D([0], [0], color="#FFFFFF", linewidth=3,
                               linestyle="--", label="🌍 Global mean"))

        leg = self.ax.legend(
            handles=handles, loc="upper left",
            fontsize=12, ncol=4,
            facecolor=S.PANEL_COLOR, edgecolor=S.PANEL_BORDER,
            labelcolor="#C9D1D9", framealpha=0.9,
            handlelength=1.8, columnspacing=1.2,
        )

        # ── Line containers (will be updated each frame) ─────────────────
        self._city_lines: dict[str, mpl.lines.Line2D] = {}
        self._city_dots:  dict[str, mpl.lines.Line2D] = {}

        for city in self.cities:
            color = self.meta.get(city, {}).get("color", "#FFFFFF")
            line, = self.ax.plot([], [], color=color,
                                  linewidth=S.LINE_WIDTH_BG,
                                  alpha=S.LINE_ALPHA_BG, zorder=3)
            dot, = self.ax.plot([], [], "o", color=color,
                                 markersize=S.MARKER_SIZE, zorder=5)
            self._city_lines[city] = line
            self._city_dots[city]  = dot

        # Global mean line (dashed white, thicker)
        self._global_line, = self.ax.plot([], [], color="#FFFFFF",
                                           linewidth=3, linestyle="--",
                                           alpha=0.9, zorder=6)

        # ── Factoid box (initially hidden) ───────────────────────────────
        self._factoid_box  = None
        self._factoid_text = None
        self._active_factoid: Factoid | None = None
        self._factoid_frame_start: int = -9999

    # ── Frame update ──────────────────────────────────────────────────────

    def _init(self):
        """Matplotlib animation init function."""
        for line in self._city_lines.values():
            line.set_data([], [])
        for dot in self._city_dots.values():
            dot.set_data([], [])
        self._global_line.set_data([], [])
        return list(self._city_lines.values()) + list(self._city_dots.values()) + [self._global_line]

    def _update(self, frame: int):
        """Matplotlib animation update function — called once per frame."""
        current_year = self.frame_years[frame]

        # ── Update each city line ────────────────────────────────────────
        for city in self.cities:
            xs, ys = self._city_data[city]
            mask   = xs <= current_year
            if mask.sum() == 0:
                continue
            self._city_lines[city].set_data(xs[mask], ys[mask])
            self._city_dots[city].set_data([xs[mask][-1]], [ys[mask][-1]])

        # ── Update global mean line ───────────────────────────────────────
        gmask = self._global_years <= current_year
        self._global_line.set_data(self._global_years[gmask],
                                    self._global_anom[gmask])

        # ── Year counter ─────────────────────────────────────────────────
        self.year_text.set_text(str(current_year))

        # ── Factoid cards ─────────────────────────────────────────────────
        # Trigger factoid at first frame of a new year
        prev_year = self.frame_years[max(0, frame - 1)]
        if current_year != prev_year:
            new_facts = self.factoids.get(current_year)
            if new_facts:
                self._show_factoid(new_facts[0], frame)

        self._update_factoid_alpha(frame)

        # Return all artists for blitting
        artists = (list(self._city_lines.values()) +
                   list(self._city_dots.values()) +
                   [self._global_line, self.year_text])
        if self._factoid_box:
            artists.append(self._factoid_box)
        return artists

    def _show_factoid(self, fact: Factoid, frame: int) -> None:
        """Create or update the factoid box."""
        self._active_factoid       = fact
        self._factoid_frame_start  = frame

        # Remove old box
        if self._factoid_box:
            self._factoid_box.remove()
            self._factoid_box = None
        if self._factoid_text:
            self._factoid_text.remove()
            self._factoid_text = None

        # Build text
        text = f"{fact.emoji}  {fact.headline}\n\n{fact.wrapped_body(52)}"

        # Place in lower-right quadrant
        self._factoid_text = self.ax.text(
            0.97, 0.04, text,
            transform=self.ax.transAxes,
            ha="right", va="bottom",
            fontsize=17,
            color=S.FONT_FACTOID["color"],
            alpha=0.0,
            bbox=dict(
                boxstyle="round,pad=0.6",
                facecolor=S.FACTOID_BG,
                edgecolor=S.FACTOID_BORDER,
                linewidth=S.FACTOID_BORDER_W,
                alpha=S.FACTOID_ALPHA,
            ),
            zorder=10,
            wrap=True,
        )

    def _update_factoid_alpha(self, frame: int) -> None:
        if self._factoid_text is None or self._active_factoid is None:
            return

        elapsed_frames = frame - self._factoid_frame_start
        duration_frames = int(S.FACTOID_DURATION * self.fps)
        fade_frames     = int(S.FACTOID_FADE_TIME  * self.fps)

        if elapsed_frames < fade_frames:
            alpha = elapsed_frames / fade_frames
        elif elapsed_frames < duration_frames - fade_frames:
            alpha = 1.0
        elif elapsed_frames < duration_frames:
            alpha = (duration_frames - elapsed_frames) / fade_frames
        else:
            alpha = 0.0
            self._active_factoid = None

        self._factoid_text.set_alpha(alpha)

    # ── Render ────────────────────────────────────────────────────────────

    def render(self) -> None:
        self._setup_figure()

        n_frames = self.total_frames
        if self.preview:
            n_frames = min(n_frames, self.fps * 10)   # 10 s preview

        print(f"\n  Rendering {n_frames} frames @ {self.fps} fps → {self.output_path.name}")
        print(f"  Estimated duration: {n_frames / self.fps:.1f}s")

        ani = FuncAnimation(
            self.fig,
            self._update,
            frames=n_frames,
            init_func=self._init,
            blit=False,   # blit=True is faster but buggy with text artists
            interval=1000 / self.fps,
        )

        bitrate = 20000 if not self.preview else 5000
        writer  = FFMpegWriter(fps=self.fps, bitrate=bitrate,
                                metadata={"title": "Temperature History – Data Vibe",
                                          "artist": S.CHANNEL_NAME,
                                          "comment": "Berkeley Earth data"})

        with tqdm(total=n_frames, unit="fr", ncols=70) as pbar:
            def progress_cb(i, _total):
                pbar.update(1)

            ani.save(str(self.output_path), writer=writer,
                     dpi=S.VIDEO_DPI if not self.preview else 96,
                     progress_callback=progress_cb)

        print(f"\n  ✅ Saved: {self.output_path}")
        plt.close(self.fig)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Render city temperature line animation")
    parser.add_argument("--years",    nargs=2, type=int, default=[1850, 2024],
                        metavar=("START", "END"))
    parser.add_argument("--fps",      type=int, default=30)
    parser.add_argument("--preview",  action="store_true",
                        help="Render a quick 10-second preview at low res")
    parser.add_argument("--output",   type=str, default=None)
    parser.add_argument("--quality",  choices=["draft", "normal", "high"],
                        default="normal")
    args = parser.parse_args()

    if args.quality == "high":
        args.fps = 60
    elif args.quality == "draft":
        args.fps = 15

    year_start, year_end = args.years
    city_df, global_df   = load_data(year_start, year_end)

    out = Path(args.output) if args.output else None

    anim = CityTempAnimation(
        city_df    = city_df,
        global_df  = global_df,
        year_start = year_start,
        year_end   = year_end,
        fps        = args.fps,
        output_path= out,
        preview    = args.preview,
    )
    anim.render()


if __name__ == "__main__":
    main()
