# Data Vibe — Production Notes & Lessons Learned

Channel: **Data Vibe** (@DataVibe)
Goal: animated time-series / bar chart race videos → $5,000/yr passive income
Last updated: 2026-03-14

---

## Current Videos

| File | Description | Duration | Status |
|------|-------------|----------|--------|
| `hottest_years_v4_music.mp4` | GloSAT/HadCRUT5 1781–2025 with music, °F primary | 172.5s | ✅ **final** |
| `hottest_years_v3_BE.mp4` | Berkeley Earth 1880–2024, 87s | 87s | archived (non-commercial license) |

### Production scripts (all in `src/`)
- `demo_v4_render.py` — main animation script, GloSAT/HadCRUT5 data, **active**
- `make_music_v4.py` — synthesized 172s soundtrack for v4
- `factoids.py` — factoid dict with full citations (reference; working FACTOIDS lives in render script)

---

## Architecture

### Animation pipeline
- **Matplotlib FuncAnimation + FFMpegWriter** → H.264 MP4 at 720p (1280×720), dpi=100, 30fps
- Two panels: `BAR_AX` (bar chart race, top ~58%) + `LINE_AX` (time-series, bottom ~22%)
- Factoid header strip: `fig.text()` at y=0.298 between the two panels
- All figure-level text uses `fig.text()` so `ax.cla()` calls don't clear them

### Bar chart race — cumulative absolute temperature
- **Cumulative**: all years seen so far appear on bars from year 1; no filter on positives
- `get_ranking(up_to)` returns all years 1781–up_to sorted by anomaly, top 10
- `lerp_rankings(ya, yb, t)` with `ease_out(t) = 1-(1-t)^3` for smooth transitions
- `FPY=12` (transition frames) + `HOLD=8` (hold frames) = **20 frames/year** at FPS=30
- **Absolute display**: `bar_len = (BASELINE_ABS + val_c - BAR_FLOOR) * 1.8` in °F delta units
  - `BASELINE_ABS = 14.0°C` (1951–1980 mean), `BAR_FLOOR = 12.5°C`
  - Label: `59.5°F (+2.3°F / +1.29°C)` — absolute + anomaly vs baseline
- **°F primary**: US-focused audience; Celsius in parentheses throughout
- `MAX_BAR = (BASELINE_ABS + MAX_C - BAR_FLOOR) * 1.42` — 42% headroom for 2024 label
- `ylim = (0.15, TOP_N + 1.60)` — extra vertical room below rank 10 for reference gridline labels

### Time-series line
- **Pre-built segment arrays** (`_INT_XF`, `_INT_YF`, `_SEGS_INT`, `_COLS_INT`) computed once at startup → O(1) slice per frame
- **Independent smooth clock** in `update()`: `tl_yr = START + (ri - FIRST_HOLD) / (FPY + HOLD)` — decoupled from bar chart ease-out
- **Fractional tip segment** appended when `yr_frac > 0` — prevents backward-jump dot bug
- Y-axis: 5 ticks `[-0.5, 0, +0.5, +1.0, +1.5°C]`, two-line labels `+0.9°F\n(+0.5°C)` (two lines prevent left-edge cutoff)

### Factoid system
- `FACTOIDS` dict: year → (headline, body, emoji) — 22 entries, 1783–2024
- `fstate = {"text": "", "start": -9999, "last_yr": -1}` — single shared state dict
- Header display duration: `fdr = int(10.0 * FPS) = 300 frames = 10 seconds`
- **Three-phase factoid dot**:
  1. **Burst** (0–2 years after event): pulsing halo `cos(age/2π·6)` envelope
  2. **Twinkle** (while header visible): `0.55 + 0.45·sin(2π·0.6·t)` — only on active dot
  3. **Settle** (permanent): `markersize=3.5`, `alpha=0.50`, faint persistent dot
- `FLASH_DUR = 2.0` years for burst phase

### Industrial Revolution dotted lines
- `IR_ERAS = [(1840, "1st IR"), (1890, "2nd IR"), (1982, "3rd IR")]`
- Fade in over 2 years as timeline reaches each: `alpha = min(1.0, (yr_float - ir_yr) / 2.0) * 0.38`
- Style: `linestyle=(0, (4, 4))`, color `#B0B8C8`, linewidth 0.8
- **Placement rule**: ≥5 year clearance from any nearby factoid dot

### Music synthesis (`make_music_v4.py`)
- Pure Python: numpy + scipy (no external audio libraries needed)
- 8 layers stacked over 172s: bass drone → low Cm pad → tension chord → mid shimmer → high shimmer → sub-bass → frequency riser → bass hit
- `T_DROP = 107.8s` → year 1937 (when global temperatures first started consistently rising above baseline)
- **Riser**: 15s quadratic chirp 40→900 Hz + octave double (80→1800 Hz) + filtered white noise sweep
- **Bass hit**: C1 (32.7 Hz) sub + C2 + transient crack + 8-beat rhythmic pulse at 120 BPM post-drop
- `rt60=4.0s` reverb, wet/dry=0.45/0.55; stereo widener 13ms delay
- Mix via ffmpeg: `volume=0.42`, 2s fade-in, 5s fade-out

---

## Layout (1280×720, dpi=100)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Title (fontsize=22, y=0.972)                                                │
│  Subtitle (fontsize=10.5, y=0.930)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│   BAR_AX  [0.21, 0.300, 0.695, 0.570]                                        │
│   Bar chart race, ranks 1–10 hottest years                                   │
│   Year watermark at fig (0.895, 0.312), fontsize=60                          │
│                                                                               │
│   Factoid strip  fig.text(0.5, 0.298)  — between panels                     │
│                                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│   LINE_AX [0.07, 0.065, 0.875, 0.215]                                        │
│   Time-series 1781–2025, colored by temp                                     │
│   Y-ticks: 5 ticks at [-0.5, 0, +0.5, +1.0, +1.5°C], two-line °F labels    │
│   X-ticks: every 25 years from 1800                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Critical layout rules for 720p:**
- Title at fontsize=30 **overlaps** the subtitle — use ≤22pt
- 9 y-axis ticks with two-line labels are too crowded — use 5 ticks max
- Y-axis two-line labels (`+0.9°F\n(+0.5°C)`) prevent left-edge cutoff vs single-line
- `va="top"` text bottom edge ≈ `y_fig - fontsize_pt/72/fig_height_inches`
- `MAX_BAR * 1.42` scaling needed to fit 2024's label (`59.5°F (+2.3°F / +1.29°C)`)
- Reference gridline labels at `TOP_N+1.15`, `va="top"` with `ylim=(0.15, TOP_N+1.60)` to clear rank-10 bar

---

## Data & Licensing

### GloSAT / HadCRUT5 (✅ commercial-friendly)
- **License**: CC BY 4.0 — fully commercial-friendly for YouTube monetization
- **GloSAT**: land surface temperature, University of East Anglia / Met Office Hadley Centre, 1781–2023
- **HadCRUT5**: land+ocean (GloSAT + HadSST), Met Office Hadley Centre / CRU, 1850–2024
- **Baseline**: 1951–1980 anomaly; `BASELINE_ABS = 14.0°C` for absolute display
- **2025 data**: preliminary (+1.12°C), labeled as such in code — remove or update when official

### Berkeley Earth (❌ non-commercial — archived)
- **License**: CC BY-NC 4.0 — **requires permission for YouTube monetization**
- Kept in `demo_v3_render.py` for reference only
- **Do not use** in any published video without explicit permission from Berkeley Earth

---

## Rendering Constraints

- **Bash timeout**: ~10–12 minutes per render at 720p/30fps/20fpyear
- **1080p** at 5175 frames times out — use **720p (1280×720)** only
- **720p at 5175 frames** renders in ~11 minutes ✅
- **Render time regression warning**: anything that draws each bar twice (e.g., secondary glow barh) costs ~40% extra render time. Use single `barh` per bar.
- After a timeout, the output `.mp4` has a missing `moov` atom and is unplayable — must re-render from scratch
- Music re-synthesis takes ~2 min; **reuse existing `soundtrack_v4.wav`** if only video changes — just re-run the ffmpeg mix step

---

## Design Decisions & Lessons

### What works well
- **Cumulative absolute temperature race**: showing all years from the very first frame (even cold blue years) creates engagement immediately. Viewers can watch ranks shift even in the 1800s.
- **°F primary with °C parenthetical**: US-focused audience responds better; using `val_c * 1.8` anomaly delta avoids the +32 offset confusion in difference display
- **Independent timeline clock**: decoupling the line's time from the bar chart's ease-out was the key insight for smooth animation. Line advances at exactly 1/(FPY+HOLD) year per frame.
- **Fractional tip segment**: interpolating one extra segment to the current fractional year makes the endpoint dot glide continuously without branching.
- **Three-phase factoid dots**: burst → twinkle → settle gives the viewer a visual cue that "something happened here" without cluttering the chart permanently
- **2 glow passes** (vs 3) looks nearly identical but renders faster
- **5 y-axis ticks** at 720p — 9 ticks with two-line labels overlap and are unreadable
- **Beat drop at year 1937**: historically meaningful (pre-WWII industrialization surge) and musically satisfying
- **15s riser** (vs 7s): builds sufficient tension across the mid-industrial period
- **No Paris 1.5°C line in bar chart**: let viewers discover the threshold naturally at the end

### What didn't work
- **Factoid cards** (long text overlaid on bar chart): competed for attention, too much to read mid-animation. Replaced with single-line header strip between panels.
- **Subscribe banner at end**: felt tacky. Simple `@DataVibe` text only.
- **Era text overlays** ("Pre-industrial era — warming has not yet begun"): confusing alongside IR dotted lines. Removed naturally when switching to cumulative absolute race (filter condition never triggers).
- **Monthly sub-step grid**: killed by render timeout (97.2% complete), abandoned entirely.
- **Top y-axis label cut off**: single-line `+0.9°F (+0.5°C)` was too wide. Two-line format fixed it.
- **Bottom spine on bar chart**: faint horizontal line through x-axis area looks like a chart artifact — remove it entirely.

### Visual hierarchy rule
The animation has three simultaneous tracks (bar chart, line chart, year counter). A fourth track (factoid text) is at the absolute limit. Keep to three main visual tracks; factoid header strip is thin enough to not count as a fourth.

### Tone rule
Factoid headlines: factual, neutral, no editorializing. "Pacific Ocean circulation reverses" ✅ — "cooling trend ends" ❌ (implies causation, pushes a narrative).

---

## Next Videos

### Ideas for Data Vibe series
1. **Sea level rise** — tide gauge + satellite altimetry, 1900–2025
2. **CO₂ concentration** — Keeling Curve (1958 Mauna Loa) + ice core proxies back to 1000 CE
3. **Arctic sea ice extent** — NSIDC monthly minimum 1979–2025
4. **Extreme weather events** — NOAA billion-dollar disasters 1980–2025
5. **Renewable energy growth** — global solar/wind capacity race 2000–2025

### Reuse checklist for next video
- [ ] Copy `demo_v4_render.py` as new base
- [ ] Update `GLOBAL_TEMP` dict (or equivalent data dict) — verify CC BY license
- [ ] Update `START`, `END`, `BAR_FLOOR`, `BASELINE_ABS`
- [ ] Update `FACTOIDS` for domain-appropriate events with citations
- [ ] Update title, subtitle, footer text
- [ ] Recalculate `T_DROP` for music: `(INTRO_F + FIRST_HOLD + offset*(FPY+HOLD)) / FPS`
- [ ] Update `DUR` in `make_music_v4.py`
- [ ] Check 720p layout: title fontsize ≤22, 5 y-ticks max, two-line y-labels
- [ ] Verify CC BY data license before publishing to YouTube

---

## Quick Reference: Frame Timing Formula

```
Total frames = INTRO_F + FIRST_HOLD + (END-START) * (FPY+HOLD) + END_F
             = 90 + (HOLD*3) + years * (FPY+HOLD) + (FPS*6)

Beat drop at year Y (START=1781):
  T_DROP = (INTRO_F + FIRST_HOLD + (Y - START) * (FPY + HOLD)) / FPS

Example (v4): year 1937
  T_DROP = (90 + 24 + (1937-1781) * 20) / 30 = (90 + 24 + 3120) / 30 = 107.8s
```

---

## Attribution Block (for YouTube description)

```
Data: GloSAT / HadCRUT5 (CC BY 4.0)
Met Office Hadley Centre / Climatic Research Unit, University of East Anglia
https://www.metoffice.gov.uk/hadobs/hadcrut5/
https://www.glosatproject.org/

Music: original composition, synthesized with Python (numpy/scipy)
Animation: Python / Matplotlib
```
