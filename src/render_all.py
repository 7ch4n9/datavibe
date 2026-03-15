#!/usr/bin/env python3
"""
render_all.py  –  Master render script: runs all videos in sequence.

Usage
-----
    # Full 4K renders (takes hours — run overnight)
    python src/render_all.py

    # Quick previews of all videos (10 s each)
    python src/render_all.py --preview

    # Render only specific videos
    python src/render_all.py --only line heatmap

    # Specify a custom output directory
    python src/render_all.py --outdir /Volumes/Export/youtube_exports
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT    = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(exist_ok=True)


# ─── Video definitions ───────────────────────────────────────────────────────

VIDEOS = [
    {
        "id":     "line",
        "label":  "City Temperature Line Chart (1850–2024)",
        "script": SRC_DIR / "city_line_animation.py",
        "args":   ["--years", "1850", "2024", "--fps", "30"],
    },
    {
        "id":     "race_years",
        "label":  "Hottest Years Bar Chart Race (1950–2024)",
        "script": SRC_DIR / "bar_chart_race.py",
        "args":   ["--mode", "hottest_years", "--years", "1950", "2024", "--fps", "30"],
    },
    {
        "id":     "race_cities",
        "label":  "City Anomaly Bar Chart Race (1950–2024)",
        "script": SRC_DIR / "bar_chart_race.py",
        "args":   ["--mode", "city_anomaly", "--years", "1950", "2024", "--fps", "30"],
    },
    {
        "id":     "heatmap",
        "label":  "Global Heatmap Animation (1850–2024)",
        "script": SRC_DIR / "global_heatmap.py",
        "args":   ["--years", "1850", "2024", "--fps", "30"],
    },
]


def run_video(video: dict, preview: bool, outdir: Path) -> bool:
    cmd = [sys.executable, str(video["script"])] + video["args"]
    if preview:
        cmd.append("--preview")
    print(f"\n{'═'*60}")
    print(f"  Rendering: {video['label']}")
    print(f"  Command:   {' '.join(cmd)}")
    print(f"{'═'*60}")

    t0 = time.time()
    result = subprocess.run(cmd, check=False)
    elapsed = time.time() - t0

    if result.returncode == 0:
        print(f"  ✅ Done in {elapsed/60:.1f} min")
        return True
    else:
        print(f"  ❌ Failed (exit code {result.returncode})")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true",
                        help="Render 10-s low-res previews of each video")
    parser.add_argument("--only", nargs="+",
                        metavar="ID",
                        help=f"Render only these IDs: {[v['id'] for v in VIDEOS]}")
    parser.add_argument("--outdir", type=str, default=str(OUT_DIR))
    args = parser.parse_args()

    to_render = VIDEOS
    if args.only:
        to_render = [v for v in VIDEOS if v["id"] in args.only]
        if not to_render:
            print(f"No matching video IDs. Options: {[v['id'] for v in VIDEOS]}")
            sys.exit(1)

    print("\n  ┌─ Data Vibe – Render Pipeline ─────────────────┐")
    print( "  │  Videos to render:", len(to_render))
    print( "  │  Preview mode:    ", args.preview)
    print(f"  │  Output dir:       {args.outdir}")
    print( "  └───────────────────────────────────────────────────────┘")

    results = {}
    for video in to_render:
        ok = run_video(video, preview=args.preview, outdir=Path(args.outdir))
        results[video["id"]] = ok

    print("\n\n  ── Summary ──────────────────────────────────────────")
    for vid_id, ok in results.items():
        icon = "✅" if ok else "❌"
        print(f"  {icon}  {vid_id}")
    print()


if __name__ == "__main__":
    main()
