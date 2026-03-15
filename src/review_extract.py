#!/usr/bin/env python3
"""
review_extract.py  —  Post-render self-review tool for Data Vibe videos.

Usage:
    python src/review_extract.py output/hottest_years_v3.mp4

Extracts key storytelling frames, prints a QA summary, and flags any
layout or data issues to review before uploading to YouTube.
"""

import subprocess, json, sys, os

# ── Key frames to extract (label, timestamp) ──────────────────────────────────
REVIEW_FRAMES = [
    ("01_intro",           "00:00:02.5",  "Intro teaser bar — should show final anomaly value"),
    ("02_pre_industrial",  "00:00:15",    "~1900: all bars empty; timeline cool blue below baseline"),
    ("03_wwii_peak",       "00:00:37",    "~1944–45: first bars appear, subtle green; WWII factoid"),
    ("04_pinatubo",        "00:01:00",    "~1991: visible dip on timeline; Pinatubo factoid"),
    ("05_first_record",    "00:01:06",    "~1998: first gold #1 bar; record factoid fires"),
    ("06_acceleration",    "00:01:15",    "~2014: bars turning orange; 1990s events on timeline"),
    ("07_record_shatter",  "00:01:18",    "~2016: deep red bar; 'record shattered' factoid"),
    ("08_paris_events",    "00:01:21",    "~2020–21: US Paris withdraw/rejoin events on timeline"),
    ("09_final_state",     "00:01:23",    "~2024: all 10 bars deep crimson; correct final value"),
    ("10_end_card",        "00:01:24",    "End card: stats + subscribe button + final chart"),
]

CHECKLIST = [
    "Title/subtitle not clipped",
    "Bar labels readable, not overlapping",
    "Timeline callout labels legible (≥9pt)",
    "Year counter inside bar panel, NOT over timeline",
    "Y-axis °F/°C ticks readable",
    "1880 shows ~−0.29°F (−0.16°C)",
    "Volcanic dips visible (1883, 1912, 1964, 1991)",
    "1998 is first record year",
    "2016 is first year above +1.0°C / +1.8°F",
    "2024 shows +2.32°F (+1.29°C)",
    "Bars show °F primary, °C in parentheses",
    "Baseline labels ≈57.2°F / 14.0°C absolute",
    "Smooth year-to-year transitions",
    "Factoid cards don't obscure top 2 bars",
    "End card legible: stats + subscribe button",
]


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", "-show_streams", path],
        capture_output=True, text=True
    )
    return json.loads(r.stdout)


def extract_frames(video_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    extracted = []
    for label, ts, note in REVIEW_FRAMES:
        out = os.path.join(out_dir, f"{label}.jpg")
        r = subprocess.run(
            ["ffmpeg", "-ss", ts, "-i", video_path,
             "-vframes", "1", "-q:v", "2", out, "-y"],
            capture_output=True
        )
        size = os.path.getsize(out) // 1024 if os.path.exists(out) else 0
        status = "✅" if size > 10 else "❌"
        extracted.append((status, label, ts, note, size))
    return extracted


def main():
    if len(sys.argv) < 2:
        print("Usage: python src/review_extract.py <video.mp4>")
        sys.exit(1)

    video = sys.argv[1]
    if not os.path.exists(video):
        print(f"❌  File not found: {video}")
        sys.exit(1)

    out_dir = os.path.join(os.path.dirname(video), "review_frames",
                           os.path.splitext(os.path.basename(video))[0])

    print("\n" + "═" * 62)
    print("  DATA THROUGH TIME  —  Post-Render Self-Review")
    print("═" * 62)

    # ── Video metadata ──────────────────────────────────────────────────────
    info = probe(video)
    fmt = info["format"]
    vs  = next(s for s in info["streams"] if s["codec_type"] == "video")
    dur = float(fmt.get("duration", 0))
    size_mb = os.path.getsize(video) / 1e6

    print(f"\n  File    : {os.path.basename(video)}")
    print(f"  Size    : {size_mb:.1f} MB")
    print(f"  Duration: {dur:.1f}s  ({dur/60:.1f} min)")
    print(f"  Codec   : {vs['codec_name']}  {vs.get('pix_fmt','')}  "
          f"{vs['width']}×{vs['height']}  {vs.get('r_frame_rate','?')} fps")

    # ── Duration check ───────────────────────────────────────────────────────
    if dur < 60:
        print(f"\n  ⚠️  WARNING: Video is only {dur:.0f}s — target is >80s for monetisation")
    elif dur > 600:
        print(f"\n  ⚠️  NOTE: Video is {dur/60:.1f} min — consider YouTube Shorts version too")
    else:
        print(f"\n  ✅  Duration looks good ({dur:.0f}s)")

    # ── Frame extraction ────────────────────────────────────────────────────
    print(f"\n  Extracting {len(REVIEW_FRAMES)} review frames → {out_dir}\n")
    frames = extract_frames(video, out_dir)
    for status, label, ts, note, size in frames:
        print(f"  {status}  [{ts}]  {label}  ({size} KB)")
        print(f"       → {note}")

    # ── Checklist ────────────────────────────────────────────────────────────
    print("\n" + "─" * 62)
    print("  QA Checklist  (review frames above, tick off each item)\n")
    for item in CHECKLIST:
        print(f"  [ ]  {item}")

    print("\n" + "─" * 62)
    print("  Storytelling Beats  (watch video at these timestamps)\n")
    for _, label, ts, note in [(None,*f[1:4]) for f in frames]:
        print(f"  [ ]  {ts}  —  {note}")

    print("\n" + "═" * 62)
    print(f"  Review frames saved to:\n  {out_dir}")
    print("═" * 62 + "\n")


if __name__ == "__main__":
    main()
