#!/usr/bin/env python3
"""
bar_chart_race.py  –  Animated bar chart race for temperature rankings.

Shows one of several rankings over time:
  1. "hottest_years"    – Cumulative ranking of hottest years globally (rolling top-10)
  2. "country_warmth"   – Countries ranked by annual mean temperature anomaly
  3. "city_anomaly"     – Cities ranked by temperature anomaly vs their own baseline

The "hottest years" race is the most viral format — showing 1998, then 2005,
2010, 2015, 2016 successively breaking the record is satisfying to watch.

Usage
-----
    python src/bar_chart_race.py
    python src/bar_chart_race.py --mode hottest_years --years 1950 2024
    python src/bar_chart_race.py --mode city_anomaly  --preview
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as FancyBboxPatch
from matplotlib.animation import FFMpegWriter, FuncAnimation
import matplotlib.patheffects as pe
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
import style as S
from factoids import FactoidOverlay

ROOT     = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "processed"
OUT_DIR  = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


# ─── Color helpers ───────────────────────────────────────────────────────────

def rank_bar_color(rank: int, n: int, anom: float) -> str:
    """Color a bar by its anomaly value (blue→red) with saturation by rank."""
    base = S.anomaly_to_color(anom, vmin=-1.5, vmax=2.0)
    return base


# ─── Data loaders ────────────────────────────────────────────────────────────

def load_hottest_years(year_start: int, year_end: int) -> pd.DataFrame:
    """
    For each year Y, build a bar-chart frame showing the top-10 hottest years
    out of all years from year_start..Y.

    Returns long-form DataFrame with columns:
        frame_year, rank, year_label, anomaly, bar_color
    """
    path = DATA_DIR / "global_annual.csv"
    if not path.exists():
        print("Run: python data/process_data.py"); sys.exit(1)

    df = pd.read_csv(path)
    df = df[(df.year >= year_start) & (df.year <= year_end)].copy()
    df = df.sort_values("year")

    records = []
    TOP_N   = 10

    for i, row in df.iterrows():
        fy = int(row["year"])
        # All years up to and including this frame year, sorted hot→cold
        sub   = df[df.year <= fy].nlargest(TOP_N, "anomaly")
        for rank, (_, r) in enumerate(sub.iterrows(), 1):
            records.append({
                "frame_year": fy,
                "rank":       rank,
                "year_label": str(int(r["year"])),
                "anomaly":    r["anomaly"],
                "bar_color":  S.anomaly_to_color(r["anomaly"]),
            })

    return pd.DataFrame(records)


def load_city_anomaly(year_start: int, year_end: int) -> pd.DataFrame:
    """
    For each year, rank cities by their temperature anomaly.
    """
    path = DATA_DIR / "city_annual.csv"
    if not path.exists():
        print("Run: python data/process_data.py"); sys.exit(1)

    df    = pd.read_csv(path)
    meta_path = ROOT / "data" / "cities.json"
    with open(meta_path) as f:
        meta = {c["name"]: c for c in json.load(f)["cities"]}

    df = df[(df.year >= year_start) & (df.year <= year_end)].copy()

    records = []
    TOP_N   = 15

    for yr, grp in df.groupby("year"):
        ranked = grp.nlargest(TOP_N, "anomaly").reset_index(drop=True)
        for rank, row in ranked.iterrows():
            city = row["city"]
            city_meta = meta.get(city, {})
            records.append({
                "frame_year": int(yr),
                "rank":       rank + 1,
                "year_label": f"{city_meta.get('flag','')} {city}",
                "anomaly":    row["anomaly"],
                "bar_color":  city_meta.get("color", "#FFFFFF"),
            })

    return pd.DataFrame(records)


MODE_LOADERS = {
    "hottest_years": load_hottest_years,
    "city_anomaly":  load_city_anomaly,
}


# ─── Main animator ───────────────────────────────────────────────────────────

class BarChartRace:
    """
    Animated bar chart race.

    Parameters
    ----------
    race_df     : Long-form DataFrame (frame_year, rank, year_label, anomaly, bar_color)
    mode        : One of MODE_LOADERS keys — drives title/subtitle text
    fps         : Output frame rate
    preview     : True = fast low-res test
    output_path : Destination MP4
    """

    # Frames used to animate between two consecutive years
    TRANSITION_FRAMES = 15   # ~0.5 s at 30 fps; increase for slower races

    TITLE_MAP = {
        "hottest_years": ("Hottest Years in Recorded History",
                           "Running top 10 — updated each year  ·  Global mean anomaly vs 1951–1980"),
        "city_anomaly":  ("Cities Ranked by Temperature Anomaly",
                           "Annual anomaly vs each city's 1951–1980 baseline  ·  Berkeley Earth"),
    }

    def __init__(self,
                 race_df:     pd.DataFrame,
                 mode:        str = "hottest_years",
                 fps:         int = 30,
                 preview:     bool = False,
                 output_path: Optional[Path] = None):

        self.race_df     = race_df
        self.mode        = mode
        self.fps         = fps
        self.preview     = preview
        self.output_path = output_path or OUT_DIR / f"bar_race_{mode}.mp4"

        # All distinct frame years
        self.frame_years = sorted(race_df["frame_year"].unique())

        # Transition frames per year
        tf = max(1, self.TRANSITION_FRAMES)
        if preview:
            tf = 3

        # Build interpolated frame sequence: for each consecutive year pair,
        # generate tf lerp steps + 10 hold frames
        HOLD_FRAMES = max(1, fps // 3)   # ~0.33 s hold at each year

        self._interp_seq: list[tuple[int, int, float]] = []
        # (year_a, year_b, t)  where t=0 → year_a layout, t=1 → year_b layout
        for i, yr in enumerate(self.frame_years):
            if i == 0:
                # Intro hold
                for _ in range(HOLD_FRAMES * 2):
                    self._interp_seq.append((yr, yr, 0.0))
            else:
                prev_yr = self.frame_years[i - 1]
                for f in range(tf):
                    t = S.ease_out_expo(f / tf)
                    self._interp_seq.append((prev_yr, yr, t))
                for _ in range(HOLD_FRAMES):
                    self._interp_seq.append((yr, yr, 1.0))

        self.total_frames = len(self._interp_seq)

        # Precompute per-year layout: {year: {label: (rank, anomaly, color)}}
        self._year_layouts: dict[int, dict[str, tuple[int, float, str]]] = {}
        for yr, grp in race_df.groupby("frame_year"):
            self._year_layouts[int(yr)] = {
                row["year_label"]: (row["rank"], row["anomaly"], row["bar_color"])
                for _, row in grp.iterrows()
            }

        # Max anomaly for x-axis scaling
        self.max_anom = race_df["anomaly"].max() * 1.15
        self.min_anom = min(0, race_df["anomaly"].min() * 1.1)

        # Top N bars to show
        self.top_n = int(race_df["rank"].max())

    # ── Figure setup ──────────────────────────────────────────────────────

    def _setup_figure(self) -> None:
        mpl.rcParams.update(S.RC_PARAMS)

        figsize = (10.8, 6.0) if self.preview else S.FIGSIZE
        self.fig = plt.figure(figsize=figsize, facecolor=S.BG_COLOR)
        self.ax  = self.fig.add_axes([0.18, 0.06, 0.74, 0.80])
        self.ax.set_facecolor(S.BG_COLOR)

        title, subtitle = self.TITLE_MAP.get(self.mode, ("Bar Chart Race", ""))
        self.fig.text(0.5, 0.96, title,    ha="center", va="top",
                      fontsize=S.FONT_TITLE["size"] * 0.85,
                      fontweight="bold", color="#FFFFFF")
        self.fig.text(0.5, 0.91, subtitle, ha="center", va="top",
                      fontsize=S.FONT_SUBTITLE["size"] * 0.85,
                      color="#8B949E")
        self.fig.text(0.99, 0.01, S.SOURCE_TEXT, ha="right", va="bottom",
                      fontsize=S.FONT_SOURCE["size"], color=S.FONT_SOURCE["color"])

        # Year counter
        self.year_text = self.fig.text(
            0.92, 0.10, "", ha="right", va="bottom",
            fontsize=S.FONT_YEAR["size"] * 0.9,
            fontweight="bold", color="#FFFFFF", alpha=0.8,
        )

        # Axis
        self.ax.set_xlim(self.min_anom, self.max_anom)
        self.ax.set_ylim(0.3, self.top_n + 0.7)
        self.ax.invert_yaxis()
        self.ax.xaxis.grid(True, linestyle=S.GRID_LINESTYLE,
                           color=S.GRID_COLOR, alpha=S.GRID_ALPHA)
        self.ax.set_axisbelow(True)
        self.ax.yaxis.set_visible(False)
        self.ax.set_xlabel("Temperature anomaly (°C)", fontsize=S.FONT_LABEL["size"],
                           color=S.FONT_LABEL["color"])

        for sp in self.ax.spines.values():
            sp.set_visible(False)
        self.ax.spines["bottom"].set_visible(True)
        self.ax.spines["bottom"].set_color(S.SPINE_COLOR)

        # Placeholder bar artists (we'll rebuild each frame)
        self._bar_patches:  dict[str, mpl.patches.FancyBboxPatch] = {}
        self._label_texts:  dict[str, mpl.text.Text] = {}
        self._value_texts:  dict[str, mpl.text.Text] = {}

    # ── Interpolated layout ───────────────────────────────────────────────

    def _interpolate_layout(self, yr_a: int, yr_b: int, t: float
                             ) -> dict[str, tuple[float, float, str]]:
        """
        Return {label: (interp_rank, interp_anomaly, color)} for a transition
        between two year layouts.
        """
        la = self._year_layouts.get(yr_a, {})
        lb = self._year_layouts.get(yr_b, {})
        all_labels = set(la) | set(lb)
        out = {}
        for lbl in all_labels:
            rank_a, anom_a, color_a = la.get(lbl, (self.top_n + 2, 0, "#333333"))
            rank_b, anom_b, color_b = lb.get(lbl, (self.top_n + 2, 0, "#333333"))
            interp_rank = rank_a + (rank_b - rank_a) * t
            interp_anom = anom_a + (anom_b - anom_a) * t
            color        = color_b if t > 0.5 else color_a
            out[lbl]     = (interp_rank, interp_anom, color)
        return out

    # ── Frame update ──────────────────────────────────────────────────────

    def _draw_frame_layout(self,
                            layout: dict[str, tuple[float, float, str]]) -> None:
        """Completely redraw all bars from scratch (simpler than patch updates)."""
        self.ax.cla()

        # Reapply axis settings
        self.ax.set_facecolor(S.BG_COLOR)
        self.ax.set_xlim(self.min_anom, self.max_anom)
        self.ax.set_ylim(0.3, self.top_n + 0.7)
        self.ax.invert_yaxis()
        self.ax.xaxis.grid(True, linestyle=S.GRID_LINESTYLE,
                           color=S.GRID_COLOR, alpha=S.GRID_ALPHA)
        self.ax.set_axisbelow(True)
        self.ax.yaxis.set_visible(False)
        self.ax.set_xlabel("Temperature anomaly (°C)", fontsize=S.FONT_LABEL["size"],
                           color=S.FONT_LABEL["color"])
        for sp in self.ax.spines.values():
            sp.set_visible(False)
        self.ax.spines["bottom"].set_visible(True)
        self.ax.spines["bottom"].set_color(S.SPINE_COLOR)

        # Draw bars in rank order
        visible = {lbl: v for lbl, v in layout.items()
                   if v[0] <= self.top_n + 0.5 and v[1] > 0}

        for lbl, (rank, anom, color) in sorted(visible.items(), key=lambda x: x[1][0]):
            # Bar
            bar_h = S.BAR_HEIGHT
            y_center = rank
            self.ax.barh(y_center, anom,
                         height=bar_h,
                         color=color,
                         alpha=0.92,
                         edgecolor="none",
                         zorder=3)

            # Label (left of bar, or outside if negative)
            label_x = min(-0.02, self.min_anom) if anom >= 0 else anom - 0.02
            self.ax.text(label_x, y_center, lbl,
                         ha="right", va="center",
                         fontsize=16 if not self.preview else 10,
                         color="#C9D1D9",
                         fontweight="bold" if rank <= 3 else "normal")

            # Value label at bar end
            val_x = anom + (self.max_anom * 0.01)
            self.ax.text(val_x, y_center,
                         f"{anom:+.3f}°C",
                         ha="left", va="center",
                         fontsize=14 if not self.preview else 9,
                         color=color,
                         fontweight="bold")

            # Rank badge (very subtle)
            if rank <= self.top_n:
                self.ax.text(self.min_anom - (self.max_anom * 0.18),
                              y_center, f"#{int(round(rank))}",
                              ha="center", va="center",
                              fontsize=13, color="#484F58", fontweight="bold")

    def _update(self, frame: int):
        yr_a, yr_b, t = self._interp_seq[frame]
        layout = self._interpolate_layout(yr_a, yr_b, t)
        self._draw_frame_layout(layout)

        # Year counter
        display_year = yr_b if t > 0.5 else yr_a
        self.year_text.set_text(str(display_year))
        return []

    # ── Render ────────────────────────────────────────────────────────────

    def render(self) -> None:
        self._setup_figure()

        n_frames = self.total_frames
        if self.preview:
            n_frames = min(n_frames, self.fps * 10)

        print(f"\n  Rendering bar chart race ({self.mode}): "
              f"{n_frames} frames @ {self.fps} fps")

        ani = FuncAnimation(
            self.fig,
            self._update,
            frames=n_frames,
            blit=False,
            interval=1000 / self.fps,
        )

        bitrate = 18000 if not self.preview else 4000
        writer  = FFMpegWriter(fps=self.fps, bitrate=bitrate,
                                metadata={"title": f"Bar Chart Race – {self.mode}"})

        with tqdm(total=n_frames, unit="fr", ncols=70) as pbar:
            ani.save(str(self.output_path), writer=writer,
                     dpi=S.VIDEO_DPI if not self.preview else 96,
                     progress_callback=lambda i, _: pbar.update(1))

        print(f"\n  ✅ Saved: {self.output_path}")
        plt.close(self.fig)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode",    choices=list(MODE_LOADERS), default="hottest_years")
    parser.add_argument("--years",   nargs=2, type=int, default=[1950, 2024],
                        metavar=("START", "END"))
    parser.add_argument("--fps",     type=int, default=30)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--output",  type=str, default=None)
    args = parser.parse_args()

    yr_s, yr_e = args.years
    loader     = MODE_LOADERS[args.mode]
    race_df    = loader(yr_s, yr_e)

    out  = Path(args.output) if args.output else None
    race = BarChartRace(race_df, mode=args.mode, fps=args.fps,
                         preview=args.preview, output_path=out)
    race.render()


if __name__ == "__main__":
    main()
