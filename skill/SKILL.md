# Data Vibe — Animated Chart Video Skill

## What This Skill Is For

Use this skill when creating animated data visualization videos for the Data Vibe YouTube channel. These are Matplotlib bar chart race + time-series combo animations, exported as H.264 MP4 and published to YouTube.

---

## Quick Start

Base scripts live in `src/`:
- `demo_v4_render.py` — copy this as your starting point for any new video
- `make_music_v4.py` — reuse music as-is or update `T_DROP` / `DUR`
- `factoids.py` — template for factoid citations

Run order:
```bash
python src/demo_v4_render.py          # ~11 min → output/hottest_years_v4.mp4
python src/make_music_v4.py           # ~2 min  → output/soundtrack_v4.mp4 + final mix
```

If video-only changes (no music changes), skip re-synthesis and just re-run the ffmpeg step from `make_music_v4.py` directly.

---

## Architecture: Two-Panel Layout

```
1280×720 @ 30fps  (dpi=100 → 12.8" × 7.2")

y=0.972  Title              fontsize=22 (max — 30pt overlaps subtitle)
y=0.930  Subtitle           fontsize=10.5
─────────────────────────────────────────────────────────────
BAR_AX   [left=0.21, bottom=0.300, width=0.695, height=0.570]
         • Bar chart race: top-10 hottest years seen so far
         • All spines hidden (including bottom — remove it to avoid artifact line)
         • ylim=(0.15, TOP_N+1.60) for gridline label clearance
─────────────────────────────────────────────────────────────
y=0.298  Factoid strip      fig.text() — thin headline between panels
─────────────────────────────────────────────────────────────
LINE_AX  [left=0.07, bottom=0.065, width=0.875, height=0.215]
         • Time-series growing line, colored blue→red by temp
         • 5 y-ticks max; two-line labels "±X.X°F\n(±X.X°C)"
─────────────────────────────────────────────────────────────
y=0.010  Footer             fontsize=9, right-aligned
```

---

## Key Constants to Change for Each New Video

```python
START = 1781         # first year in dataset
END   = 2025         # last year
FPS   = 30
FPY   = 12           # animation frames per year (transition)
HOLD  = 8            # hold frames per year (still)
# 20 total frames/year → ~11 min render for 245-year span

BASELINE_ABS = 14.0  # °C — 1951–1980 absolute mean (update for other baselines)
BAR_FLOOR    = 12.5  # °C — left edge of bar chart x-axis
MAX_BAR      = (BASELINE_ABS + MAX_C - BAR_FLOOR) * 1.42  # 1.42x headroom for label
```

---

## Absolute Temperature Display (°F Primary)

All labels show absolute °F + anomaly delta:
```
59.5°F  (+2.3°F / +1.29°C)
```

Formula:
```python
abs_c   = BASELINE_ABS + val_c          # absolute °C
bar_len = (abs_c - BAR_FLOOR) * 1.8     # x-axis length in °F delta units
abs_f   = abs_c * 1.8 + 32              # displayable absolute °F
anom_f  = val_c * 1.8                   # anomaly in °F (no +32)
```

Y-axis ticks — always two-line to prevent left-edge cutoff:
```python
f"{c_to_f(c):+.1f}°F\n({c:+.1f}°C)"   # ✅ two lines
f"{c_to_f(c):+.1f}°F ({c:+.1f}°C)"    # ❌ too wide, gets cut off
```

---

## Factoid System

```python
FACTOIDS = {
    year: ("Headline text", "", "emoji"),
    ...
}

fstate = {"text": "", "start": -9999, "last_yr": -1}
```

- `fdr = int(10.0 * FPS)` → 10 seconds display per factoid (300 frames)
- `FLASH_DUR = 2.0` years for burst dot phase
- Three dot phases: burst (0–2yr) → twinkle (while header visible) → settle (permanent, alpha=0.50)
- Factoid years must exist in `GLOBAL_TEMP` to get a dot on the time-series

**Tone rule**: factoid headlines must be factual, neutral, no editorializing.
- ✅ "Pacific Ocean circulation reverses"
- ❌ "cooling trend ends" (implies causation/narrative)

---

## Industrial Revolution Lines

```python
IR_ERAS = [
    (1840, "1st IR"),  # steam/coal peak
    (1890, "2nd IR"),  # steel/electricity/oil peak
    (1982, "3rd IR"),  # digital mainstream
]
```
- Fade in over 2 years: `alpha = min(1.0, (yr_float - ir_yr) / 2.0) * 0.38`
- Style: `linestyle=(0, (4, 4))`, `color="#B0B8C8"`, `linewidth=0.8`
- Maintain ≥5 year clearance from any factoid dot

---

## Music Timing Formula

```
T_DROP = (INTRO_F + FIRST_HOLD + (drop_year - START) * (FPY + HOLD)) / FPS

Where:
  INTRO_F    = FPS * 3  = 90 frames (3s intro hold)
  FIRST_HOLD = HOLD * 3 = 24 frames
  FPY + HOLD = 20 frames/year

v4 example: drop_year=1937, START=1781
  T_DROP = (90 + 24 + 156*20) / 30 = 107.8s
```

Beat drop year should be:
- Historically meaningful (inflection point in the data)
- ~60–70% through the total runtime (building tension, not too early)
- Visually dramatic when it hits (a year where ranking shifts happen)

---

## Render Performance Rules

| Rule | Detail |
|------|--------|
| Max resolution | **720p** (1280×720) — 1080p times out at ~10 min |
| Draw each bar once | Single `barh` only — double-draw (glow) adds 40% render time |
| No bottom spine | `ax.spines["bottom"].set_visible(False)` — visible spine looks like an artifact |
| Reuse wav if possible | `make_music_v4.py` takes ~2 min; skip if music unchanged |
| Broken mp4 = timeout | Missing `moov` atom → re-render from scratch, cannot recover |

---

## Data Licensing — Always Check Before Publishing

| Dataset | License | OK for YouTube Monetization? |
|---------|---------|------------------------------|
| GloSAT (land, 1781–) | CC BY 4.0 | ✅ Yes |
| HadCRUT5 (land+ocean, 1850–) | CC BY 4.0 | ✅ Yes |
| GISTEMP (NASA) | Public domain | ✅ Yes |
| NOAA GlobalTemp | Public domain | ✅ Yes |
| Berkeley Earth BEST | CC BY-NC 4.0 | ❌ No (non-commercial only) |
| Copernicus C3S | CC BY 4.0 | ✅ Yes (check individual products) |

---

## YouTube Description Template

See `youtube_description.md` in this project for the full template with factoid citations and data links.

Standard attribution block to include in every video:
```
Data: GloSAT / HadCRUT5 (CC BY 4.0)
Met Office Hadley Centre / Climatic Research Unit, University of East Anglia
https://www.metoffice.gov.uk/hadobs/hadcrut5/

Music: original composition, synthesized with Python (numpy/scipy)
Animation: Python / Matplotlib — source code: https://github.com/7ch4n9/datavibe
```
