#!/usr/bin/env python3
"""
demo_v4_render.py  –  v4: GloSAT/HadCRUT5 series 1781–2025
                       dual-panel bar race + time-series line, °F primary.

Data source: GloSAT / HadCRUT5 (CC BY 4.0, Met Office Hadley Centre / CRU)
  • 1781–1879: GloSAT land surface temperature estimates
  • 1880–2024: HadCRUT5 land+ocean (GloSAT land component + HadSST)
  • 2025:      Preliminary estimate

Layout
------
  ┌──────────────────────────────────────────────────┐
  │  Title / Subtitle                                │
  ├──────────────────────────────────────────────────┤
  │                                                  │
  │   BAR CHART RACE  (top ~55% of frame)            │
  │   Ranks 1–10 hottest years so far                │
  │   Primary units: °F  (°C in parentheses)         │
  │                                                  │
  ├──────────────────────────────────────────────────┤
  │  TIME SERIES LINE  (bottom ~22% of frame)        │
  │  • Full 1781–present growing line                │
  │  • Dotted zero baseline  (1951–1980 avg)         │
  │  • Colored by temp: blue (cool) → red (hot)      │
  │  • Event dots with labels                        │
  └──────────────────────────────────────────────────┘
"""

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.collections import LineCollection
from matplotlib.patches import FancyBboxPatch
from matplotlib.animation import FFMpegWriter, FuncAnimation
import os

# ─── Data ────────────────────────────────────────────────────────────────────
# 1781–1879: GloSAT land surface temperature (anomaly vs 1951–1980 baseline, °C)
# Key features: Laki 1783 cooling, unknown volcanic 1808–09, Tambora 1815/16 dip
# 1880–2024: HadCRUT5 land+ocean (GloSAT + HadSST, CC BY 4.0)
# 2025: Preliminary estimate — subject to revision
GLOBAL_TEMP = {
    # ── Pre-industrial / early industrial (GloSAT estimates) ──────────────────
    1781:-0.47, 1782:-0.43, 1783:-0.62, 1784:-0.57, 1785:-0.45,
    1786:-0.40, 1787:-0.42, 1788:-0.39, 1789:-0.43, 1790:-0.37,
    1791:-0.39, 1792:-0.41, 1793:-0.43, 1794:-0.36, 1795:-0.45,
    1796:-0.39, 1797:-0.37, 1798:-0.34, 1799:-0.39, 1800:-0.38,
    1801:-0.33, 1802:-0.30, 1803:-0.36, 1804:-0.33, 1805:-0.37,
    1806:-0.39, 1807:-0.35, 1808:-0.49, 1809:-0.54, 1810:-0.48,
    1811:-0.42, 1812:-0.46, 1813:-0.44, 1814:-0.45, 1815:-0.51,
    1816:-0.71, 1817:-0.61, 1818:-0.49, 1819:-0.43, 1820:-0.40,
    1821:-0.38, 1822:-0.33, 1823:-0.37, 1824:-0.39, 1825:-0.36,
    1826:-0.31, 1827:-0.34, 1828:-0.38, 1829:-0.43, 1830:-0.37,
    1831:-0.39, 1832:-0.33, 1833:-0.31, 1834:-0.26, 1835:-0.36,
    1836:-0.39, 1837:-0.37, 1838:-0.34, 1839:-0.35, 1840:-0.36,
    1841:-0.32, 1842:-0.36, 1843:-0.33, 1844:-0.31, 1845:-0.34,
    1846:-0.32, 1847:-0.30, 1848:-0.33, 1849:-0.29, 1850:-0.28,
    1851:-0.31, 1852:-0.29, 1853:-0.26, 1854:-0.24, 1855:-0.28,
    1856:-0.32, 1857:-0.29, 1858:-0.30, 1859:-0.23, 1860:-0.29,
    1861:-0.27, 1862:-0.39, 1863:-0.33, 1864:-0.35, 1865:-0.29,
    1866:-0.27, 1867:-0.26, 1868:-0.27, 1869:-0.25, 1870:-0.27,
    1871:-0.23, 1872:-0.25, 1873:-0.22, 1874:-0.27, 1875:-0.25,
    1876:-0.30, 1877:-0.20, 1878:-0.19, 1879:-0.26,
    # ── HadCRUT5 land+ocean (1880–2024) ───────────────────────────────────────
    1880:-0.16, 1881:-0.08, 1882:-0.11, 1883:-0.17, 1884:-0.28,
    1885:-0.33, 1886:-0.31, 1887:-0.36, 1888:-0.27, 1889:-0.17,
    1890:-0.35, 1891:-0.22, 1892:-0.27, 1893:-0.31, 1894:-0.32,
    1895:-0.23, 1896:-0.11, 1897:-0.11, 1898:-0.27, 1899:-0.17,
    1900:-0.08, 1901:-0.07, 1902:-0.28, 1903:-0.37, 1904:-0.47,
    1905:-0.26, 1906:-0.22, 1907:-0.39, 1908:-0.43, 1909:-0.48,
    1910:-0.43, 1911:-0.44, 1912:-0.36, 1913:-0.35, 1914:-0.15,
    1915:-0.14, 1916:-0.36, 1917:-0.46, 1918:-0.30, 1919:-0.27,
    1920:-0.27, 1921:-0.19, 1922:-0.28, 1923:-0.26, 1924:-0.27,
    1925:-0.22, 1926:-0.06, 1927:-0.19, 1928:-0.21, 1929:-0.36,
    1930:-0.09, 1931:-0.08, 1932:-0.11, 1933:-0.27, 1934:-0.13,
    1935:-0.19, 1936:-0.14, 1937:-0.02, 1938:-0.00, 1939:-0.02,
    1940: 0.09, 1941: 0.19, 1942: 0.07, 1943: 0.09, 1944: 0.20,
    1945: 0.09, 1946:-0.01, 1947:-0.03, 1948:-0.05, 1949:-0.08,
    1950:-0.17, 1951: 0.01, 1952: 0.02, 1953: 0.08, 1954:-0.13,
    1955:-0.14, 1956:-0.14, 1957: 0.05, 1958: 0.06, 1959: 0.03,
    1960:-0.03, 1961: 0.06, 1962: 0.03, 1963: 0.05, 1964:-0.20,
    1965:-0.11, 1966:-0.06, 1967:-0.02, 1968:-0.07, 1969: 0.08,
    1970: 0.04, 1971:-0.08, 1972: 0.01, 1973: 0.16, 1974:-0.07,
    1975:-0.01, 1976:-0.10, 1977: 0.18, 1978: 0.07, 1979: 0.16,
    1980: 0.26, 1981: 0.32, 1982: 0.14, 1983: 0.31, 1984: 0.16,
    1985: 0.12, 1986: 0.18, 1987: 0.33, 1988: 0.40, 1989: 0.29,
    1990: 0.45, 1991: 0.41, 1992: 0.23, 1993: 0.24, 1994: 0.31,
    1995: 0.45, 1996: 0.35, 1997: 0.46, 1998: 0.63, 1999: 0.40,
    2000: 0.42, 2001: 0.54, 2002: 0.63, 2003: 0.62, 2004: 0.54,
    2005: 0.68, 2006: 0.61, 2007: 0.66, 2008: 0.54, 2009: 0.64,
    2010: 0.72, 2011: 0.61, 2012: 0.64, 2013: 0.68, 2014: 0.75,
    2015: 0.90, 2016: 1.01, 2017: 0.92, 2018: 0.83, 2019: 0.98,
    2020: 1.02, 2021: 0.85, 2022: 0.89, 2023: 1.17, 2024: 1.29,
    # ── 2025 preliminary (based on Jan–Apr 2025 data, subject to revision) ───
    2025: 1.12,
}

# ─── Historical timeline event dots ──────────────────────────────────────────
# (LABEL_WINDOW removed — event annotation labels replaced by factoid header strip)

# Factoid dot years — derived from FACTOIDS dict (defined below).
# TIMELINE_EVENTS removed: dots are now driven exclusively by FACTOIDS keys.

# ─── Factoid cards — climate, population, technology, and disaster milestones ─
# Headlines shown as header strip; body retained for future use.
FACTOIDS = {
    1783: ("Laki Eruption cools the planet for two years",
           "", "🌋"),
    1800: ("World population reaches 1 billion",
           "", "👥"),
    1815: ("Mt. Tambora erupts — 1816 becomes Year Without a Summer",
           "", "🌋"),
    1825: ("World's first steam-powered public railway opens — the coal age begins",
           "", "🚂"),
    1859: ("First oil well drilled in the US",
           "", "🛢️"),
    1883: ("Krakatoa erupts — global temps drop for two years",
           "", "🌋"),
    1890: ("Gasoline automobiles enter commercial production — the car age begins",
           "", "🚗"),
    1912: ("Mt. Katmai erupts",
           "", "🌋"),
    1927: ("World population reaches 2 billion",
           "", "👥"),
    1939: ("WWII begins — industrial surge drives factory emissions",
           "", "⚔️"),
    1945: ("Trinity test — the nuclear age begins",
           "", "☢️"),
    1964: ("Mt. Agung erupts, global temperatures drop by 0.5°C for two years",
           "", "🌋"),
    1968: ("Green Revolution — synthetic fertilizers triple global food production",
           "", "🌾"),
    1976: ("Pacific Climate Shift — Pacific Ocean circulation reverses",
           "", "🌊"),
    1987: ("World population reaches 5 billion",
           "", "👥"),
    1991: ("Mt. Pinatubo erupts, global temperatures drop by 0.6°C for two years",
           "", "🌋"),
    1998: ("Monster El Niño — 1998 becomes the hottest year on record",
           "", "🔥"),
    2005: ("2005 breaks 1998 as the hottest year on record",
           "", "📈"),
    2010: ("New record — Russia heat wave & Pakistan floods in same month",
           "", "🌡️"),
    2016: ("2016 shatters all records, running +1.2°C above the pre-industrial average",
           "", "🔥"),
    2019: ("Amazon and Australian mega-fires — 18 million hectares burn in one season",
           "", "🔥"),
    2024: ("2024: first full calendar year above the 1.5°C Paris threshold",
           "", "🚨"),
}

# ─── Unit helpers ─────────────────────────────────────────────────────────────
def c_to_f(c):
    return c * 1.8

def fmt_f(c, dec=2):
    f = c_to_f(c)
    return f"{f:+.{dec}f}°F"

def fmt_fc(c):
    return f"{c_to_f(c):+.2f}°F  ({c:+.2f}°C)"

def fmt_fc_short(c):
    return f"{c_to_f(c):+.1f}°F ({c:+.2f}°C)"

# ─── Color scale ──────────────────────────────────────────────────────────────
BG    = "#0D1117"
PANEL = "#161B22"
ACCENT= "#388BFD"
T1    = "#E6EDF3"
T2    = "#8B949E"
T3    = "#484F58"
GOLD  = "#FFD700"
SILV  = "#C0C0C0"
BRNZ  = "#CD7F32"

def temp_color(c):
    stops = [(-0.75,"#2C5F8A"),(-0.5,"#4A90D9"),(0.0,"#7EC8A4"),(0.35,"#C8E06A"),
             (0.55,"#FFD166"),(0.72,"#EF8C2A"),(0.90,"#E63946"),(1.3,"#9B1D20")]
    for i in range(len(stops)-1):
        a0,c0=stops[i]; a1,c1=stops[i+1]
        if a0<=c<=a1:
            t=(c-a0)/(a1-a0)
            r0,g0,b0=mpl.colors.to_rgb(c0); r1,g1,b1=mpl.colors.to_rgb(c1)
            return mpl.colors.to_hex((r0+(r1-r0)*t,g0+(g1-g0)*t,b0+(b1-b0)*t))
    return "#9B1D20" if c>1.0 else "#2C5F8A"

def ease_out(t):    return 1-(1-t)**3
def ease_in_out(t): return 4*t**3 if t<0.5 else 1-(-2*t+2)**3/2

# ─── Race data ────────────────────────────────────────────────────────────────
START=1781; END=2025; TOP_N=10
FPS=30; FPY=12; HOLD=8     # 20 fr/year — slowed so factoid titles are readable
W,H=1280,720

years_seq=[y for y in range(START,END+1) if y in GLOBAL_TEMP]

def get_ranking(up_to):
    # All years seen so far, ranked by temperature — including cold/negative years
    sub = {y: v for y, v in GLOBAL_TEMP.items() if START <= y <= up_to}
    return sorted(sub.items(), key=lambda x: -x[1])[:TOP_N]

rankings={y:get_ranking(y) for y in years_seq}

def lerp_rankings(ya,yb,t):
    ra={str(y):v for y,v in rankings[ya]}
    rb={str(y):v for y,v in rankings[yb]}
    all_lb=set(ra)|set(rb)
    out=[]
    for lb in all_lb:
        va=ra.get(lb,0.0); vb=rb.get(lb,0.0)
        rka=next((i+1 for i,(y,_) in enumerate(rankings[ya]) if str(y)==lb),TOP_N+2)
        rkb=next((i+1 for i,(y,_) in enumerate(rankings[yb]) if str(y)==lb),TOP_N+2)
        rk=rka+(rkb-rka)*t; v=va+(vb-va)*t
        out.append((lb,rk,v))
    return [(l,r,v) for l,r,v in out if r<=TOP_N+0.4]

MAX_C   = max(GLOBAL_TEMP[y] for y in years_seq)
MAX_F   = c_to_f(MAX_C) * 1.12

# ─── Absolute temperature display constants ───────────────────────────────────
BASELINE_ABS   = 14.0   # °C — 1951–1980 global mean absolute temperature
BASELINE_ABS_F = BASELINE_ABS * 1.8 + 32   # = 57.2°F
BAR_FLOOR      = 12.5   # °C — left edge of bar chart (bars start here)
BAR_FLOOR_F    = BAR_FLOOR * 1.8 + 32      # = 54.5°F
MAX_BAR        = (BASELINE_ABS + MAX_C - BAR_FLOOR) * 1.42   # x-axis right edge — extra room for label text
MAX_BAR_F      = MAX_BAR * 1.8             # x-axis right edge in °F delta units

ALL_YEARS = sorted(GLOBAL_TEMP.keys())
ALL_TEMPS_F = [c_to_f(GLOBAL_TEMP[y]) for y in ALL_YEARS]

# ─── Frame sequence ───────────────────────────────────────────────────────────
INTRO_F = FPS*3; END_F = FPS*6

race_frames=[]
for i,yr in enumerate(years_seq):
    if i==0:
        for _ in range(HOLD*3): race_frames.append((yr,yr,1.0,yr))
    else:
        prev=years_seq[i-1]
        for f in range(FPY): race_frames.append((prev,yr,ease_out(f/FPY),yr))
        for _ in range(HOLD): race_frames.append((yr,yr,1.0,yr))

TOTAL=INTRO_F+len(race_frames)+END_F
print(f"\n  v4  |  {TOTAL} frames  |  {TOTAL/FPS:.1f}s  |  {W}×{H}\n")

# ─── Figure & axes ────────────────────────────────────────────────────────────
mpl.rcParams.update({
    "figure.facecolor":BG,"axes.facecolor":BG,"text.color":T1,
    "font.family":"DejaVu Sans","font.size":14,"savefig.facecolor":BG,
})

fig = plt.figure(figsize=(W/100, H/100), dpi=100)

BAR_AX  = fig.add_axes([0.21, 0.345, 0.695, 0.525])   # raised to leave room for factoid strip
LINE_AX = fig.add_axes([0.07, 0.055, 0.875, 0.195])   # slightly shorter to widen the gap

for ax in (BAR_AX, LINE_AX):
    ax.set_facecolor(BG)

# Title + subtitle — sized to avoid overlap at 720p
fig.text(0.5, 0.972, "Hottest Years in Recorded History",
         ha="center", va="top", fontsize=22, fontweight="bold", color=T1)
fig.text(0.5, 0.930, "Running top 10 absolute global mean temperature  ·  GloSAT / HadCRUT5  ·  Compared to 1951–1980 baseline  ·  DataVibe",
         ha="center", va="top", fontsize=10.5, color=T2)
fig.text(0.99, 0.010, "Data: GloSAT / HadCRUT5 (CC BY 4.0, Met Office Hadley Centre / CRU)  ·  @DataVibe",
         ha="right", va="bottom", fontsize=9, color=T3)

fig.add_artist(mpl.lines.Line2D([0.04,0.96],[0.335,0.335],
               transform=fig.transFigure, color="#21262D", linewidth=1.0, alpha=0.8))

# Large year watermark — inside BAR_AX vertical range
year_txt = fig.text(0.895, 0.358, "",
                    ha="right", va="bottom", fontsize=60,
                    fontweight="bold", color=T1, alpha=0.22)

# Factoid header — thin strip between bar chart and time-series
# Shows: emoji · year — headline   (fades in/out, updated by draw_timeline_panel)
factoid_hdr = fig.text(0.50, 0.298, "",
                        ha="center", va="center", fontsize=11.5,
                        color=T2, alpha=0.0, zorder=20, linespacing=1.4,
                        fontstyle="italic")

# ─── Factoid header state (updated by draw_timeline_panel each frame) ─────────
fstate = {"text": "", "start": -9999, "last_yr": -1}

# ─── Bar chart panel ──────────────────────────────────────────────────────────
def draw_bar_panel(ya, yb, t, display_yr, frame_idx):
    ax = BAR_AX
    ranking = lerp_rankings(ya, yb, t)

    ax.cla(); ax.set_facecolor(BG)
    ax.set_xlim(0, MAX_BAR_F)
    ax.set_ylim(0.15, TOP_N+1.60)  # extra room below rank 10 for gridline labels
    ax.invert_yaxis()
    ax.set_xticks([])
    ax.tick_params(axis='x', length=0, labelsize=0)
    ax.yaxis.set_visible(False)
    ax.set_xlabel("")
    for sp in ax.spines.values(): sp.set_visible(False)

    # ── Reference gridlines in absolute °F ───────────────────────────────────
    # Baseline (57.2°F / 14.0°C) highlighted in blue to match time-series zero line
    for abs_c, ref_lbl in [
        (13.5, "56.3°F\n(−0.9°F / −0.5°C)"),
        (14.0, "57.2°F\n(1951–80 avg)"),
        (14.5, "58.1°F\n(+0.9°F / +0.5°C)"),
        (15.0, "59.0°F\n(+1.8°F / +1.0°C)"),
    ]:
        bar_pos_f = (abs_c - BAR_FLOOR) * 1.8   # bar position in °F delta units
        is_baseline = (abs_c == 14.0)
        col = "#4A90D9" if is_baseline else "#21262D"
        lw  = 1.2 if is_baseline else 0.9
        al  = 0.65 if is_baseline else 0.80
        ax.axvline(bar_pos_f, color=col, lw=lw, alpha=al, zorder=0)
        ax.text(bar_pos_f, TOP_N+1.15, ref_lbl, ha="center", va="top",
                fontsize=8, color="#4A90D9" if is_baseline else T3, linespacing=1.1)

    for label, rank, val_c in sorted(ranking, key=lambda x: x[1]):
        abs_c   = BASELINE_ABS + val_c                # absolute temperature (°C)
        bar_len = (abs_c - BAR_FLOOR) * 1.8           # bar length in °F delta units
        abs_f   = abs_c * 1.8 + 32                    # absolute temperature (°F)
        anom_f  = val_c * 1.8                         # anomaly in °F
        color   = temp_color(val_c)                   # color driven by anomaly
        yr_i    = int(label)

        ax.barh(rank, bar_len, height=0.66, color=color, alpha=0.88, zorder=3, edgecolor="none")

        rk  = int(round(rank))
        mc  = GOLD if rk==1 else SILV if rk==2 else BRNZ if rk==3 else T3
        fw  = "bold" if rk<=3 else "normal"

        ax.text(-0.008, rank, f"#{rk}", ha="right", va="center",
                transform=ax.get_yaxis_transform(),
                fontsize=11.5, color=mc, fontweight="bold")
        ax.text(-0.055, rank, label, ha="right", va="center",
                transform=ax.get_yaxis_transform(),
                fontsize=16, color=T1, fontweight=fw)
        # Primary: absolute °F  |  bracketed: anomaly in °F and °C
        val_str = f"{abs_f:.1f}°F  ({anom_f:+.1f}°F / {val_c:+.2f}°C)"
        ax.text(bar_len + MAX_BAR_F*0.010, rank, val_str,
                ha="left", va="center", fontsize=12.5, color=color, fontweight="bold")

        if yr_i == display_yr:
            ax.barh(rank, bar_len, height=0.66, color="none", zorder=4,
                    edgecolor="white", linewidth=1.6, alpha=0.55)

    year_txt.set_text(str(display_yr))

# ─── Time-series panel ────────────────────────────────────────────────────────
_INT_YF    = np.array([c_to_f(GLOBAL_TEMP[y]) for y in ALL_YEARS], dtype=float)
_INT_XF    = np.array(ALL_YEARS, dtype=float)
_pts_int   = np.array([_INT_XF, _INT_YF]).T.reshape(-1, 1, 2)
_SEGS_INT  = np.concatenate([_pts_int[:-1], _pts_int[1:]], axis=1)
_COLS_INT  = [temp_color(GLOBAL_TEMP[ALL_YEARS[i]]) for i in range(len(ALL_YEARS) - 1)]


def _build_segments(yr_float):
    yr_int  = int(yr_float)
    yr_frac = yr_float - yr_int
    n = int(np.searchsorted(_INT_XF, yr_int, side="right"))
    if n < 1:
        return None, None, None, None
    xs   = _INT_XF[:n]
    ys   = _INT_YF[:n]
    segs = _SEGS_INT[:n - 1]
    cols = _COLS_INT[:n - 1]
    yn = yr_int + 1
    if yr_frac > 0 and yn in GLOBAL_TEMP:
        tip_c   = GLOBAL_TEMP[yr_int] + (GLOBAL_TEMP[yn] - GLOBAL_TEMP[yr_int]) * yr_frac
        tip_y   = c_to_f(tip_c)
        tip_seg = np.array([[[xs[-1], ys[-1]], [yr_float, tip_y]]])
        xs   = np.append(xs,   yr_float)
        ys   = np.append(ys,   tip_y)
        segs = np.concatenate([segs, tip_seg], axis=0) if len(segs) > 0 else tip_seg
        cols = cols + [temp_color(tip_c)]
    if len(xs) < 2:
        return None, None, None, None
    return xs, ys, segs, cols

# Y-axis range — extended to accommodate cold pre-industrial years
YMIN_F = c_to_f(-0.90)   # -1.62°F
YMAX_F = c_to_f( 1.55)   # +2.79°F

def draw_timeline_panel(yr_float, display_yr, frame_idx):
    ax = LINE_AX
    ax.cla(); ax.set_facecolor(BG)

    ax.set_xlim(START-2, END+2)
    ax.set_ylim(YMIN_F, YMAX_F)
    ax.set_xlabel("Year", fontsize=11, color=T2, labelpad=4)
    ax.set_ylabel("Anomaly vs\n1951–80", fontsize=10, color=T2, labelpad=4)

    for sp in ("top","right"): ax.spines[sp].set_visible(False)
    ax.spines["left"].set_color("#30363D")
    ax.spines["bottom"].set_color("#30363D")
    ax.tick_params(colors=T3, labelsize=9)

    tick_cs = [-0.5, 0.0, 0.5, 1.0, 1.5]
    tick_fs = [c_to_f(c) for c in tick_cs]
    ax.set_yticks(tick_fs)
    ax.set_yticklabels([f"{c_to_f(c):+.1f}°F\n({c:+.1f}°C)" for c in tick_cs],
                       fontsize=7.5, color=T3, linespacing=1.1)

    # x ticks every 25 years for the 245-year span
    ax.set_xticks([y for y in range(1800, END+1, 25)])
    ax.set_xticklabels([str(y) for y in range(1800, END+1, 25)],
                        rotation=0, fontsize=8, color=T3)
    ax.xaxis.grid(True, linestyle=":", color="#21262D", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)

    ax.axhline(0, color="#4A90D9", linewidth=1.2, linestyle="--", alpha=0.55, zorder=2)
    ax.text(START+1, 0.02,
            "1951–1980 avg.  (≈57.2°F / 14.0°C absolute)",
            fontsize=8, color="#4A90D9", alpha=0.70, va="bottom")

    # ── Industrial Revolution era markers — vertical dotted lines ─────────────
    # Fade in over 2 years once the timeline reaches each marker year
    IR_ERAS = [
        (1840, "1st IR"),   # End of first IR (steam / coal / textiles) — ~1760–1840
        (1890, "2nd IR"),   # Height of second IR (steel / electricity / oil) — ~1870–1914
        (1982, "3rd IR"),   # Digital revolution mainstream (microprocessors / PCs) — ~1969–
    ]
    for ir_yr, ir_lbl in IR_ERAS:
        if yr_float < ir_yr:
            continue
        ir_alpha = min(1.0, (yr_float - ir_yr) / 2.0) * 0.38
        ax.axvline(ir_yr, color="#B0B8C8", linewidth=0.8,
                   linestyle=(0, (4, 4)), alpha=ir_alpha, zorder=2)

    ax.axhline(c_to_f(1.5), color="#FF4D4D", linewidth=0.9,
               linestyle=":", alpha=0.45, zorder=2)

    ax.fill_between([START-2, END+2], [0,0], [YMIN_F, YMIN_F],
                     color="#4A90D9", alpha=0.05, zorder=1)
    ax.fill_between([START-2, END+2], [0,0], [YMAX_F, YMAX_F],
                     color="#E63946", alpha=0.05, zorder=1)

    xs, ys, segs, cols = _build_segments(yr_float)
    if segs is not None:
        ax.fill_between(xs, 0, ys, where=ys >= 0,
                        color="#E63946", alpha=0.22, zorder=2, linewidth=0)
        ax.fill_between(xs, 0, ys, where=ys <= 0,
                        color="#4A90D9", alpha=0.22, zorder=2, linewidth=0)

        for glow_lw, glow_alpha in [(12, 0.045), (5.5, 0.13)]:
            ax.add_collection(LineCollection(
                segs, colors=cols, linewidth=glow_lw,
                capstyle="round", joinstyle="round", zorder=3, alpha=glow_alpha))
        ax.add_collection(LineCollection(
            segs, colors=cols, linewidth=2.6,
            capstyle="round", joinstyle="round", zorder=4))

        yr_int  = int(yr_float)
        yr_frac = yr_float - yr_int
        yn = yr_int + 1
        if yn in GLOBAL_TEMP:
            cur_c_raw = GLOBAL_TEMP[yr_int] + (GLOBAL_TEMP[yn] - GLOBAL_TEMP[yr_int]) * yr_frac
        else:
            cur_c_raw = GLOBAL_TEMP.get(yr_int, 0)
        cur_f = c_to_f(cur_c_raw)
        color = temp_color(cur_c_raw)
        for ms, al in [(28, 0.06), (18, 0.14), (10, 0.30)]:
            ax.plot(yr_float, cur_f, "o", color=color, markersize=ms, zorder=5, alpha=al)
        ax.plot(yr_float, cur_f, "o", color=color, markersize=7,
                zorder=6, markeredgecolor="white", markeredgewidth=1.2)

    # ── Factoid dots — three phases: burst → twinkle → settle ───────────────────
    # Phase 1 BURST  : pulsing halo for first FLASH_DUR years after dot appears
    # Phase 2 TWINKLE: slow sine pulse while this dot's factoid header is visible
    # Phase 3 SETTLE : small dim persistent dot once header has faded out
    FLASH_DUR  = 2.0   # years of burst pulse (≈40 frames at 20 fr/yr)
    fdr        = int(10.0 * FPS)  # header display duration in frames (matches below)
    for evt_yr, (headline, _, emoji) in FACTOIDS.items():
        if evt_yr not in GLOBAL_TEMP or evt_yr > yr_float:
            continue
        c_e  = GLOBAL_TEMP[evt_yr]
        f_e  = c_to_f(c_e)
        col  = temp_color(c_e)
        age  = yr_float - evt_yr   # years elapsed since dot appeared

        if age < FLASH_DUR:
            # ── Phase 1: burst — pulsing halo (3 pulses over FLASH_DUR years) ──
            pulse = 0.5 + 0.5 * np.cos(age / FLASH_DUR * np.pi * 6)
            env   = 1.0 - age / FLASH_DUR
            al    = 0.35 + 0.65 * pulse * env
            ax.plot(evt_yr, f_e, "o", color=col, markersize=18, zorder=7, alpha=al * 0.12)
            ax.plot(evt_yr, f_e, "o", color=col, markersize=10, zorder=8, alpha=al * 0.25)
            ax.plot(evt_yr, f_e, "o", color="white", markersize=6, zorder=9,
                    alpha=al * 0.90, markeredgecolor=col, markeredgewidth=1.2)

        elif fstate["last_yr"] == evt_yr and (frame_idx - fstate["start"]) < fdr:
            # ── Phase 2: twinkle — slow sine pulse (~0.6 Hz) while header visible ──
            t_sec    = frame_idx / FPS
            twinkle  = 0.55 + 0.45 * np.sin(2 * np.pi * 0.6 * t_sec)
            # Outer glow ring
            ax.plot(evt_yr, f_e, "o", color=col, markersize=12, zorder=7,
                    alpha=twinkle * 0.18)
            ax.plot(evt_yr, f_e, "o", color=col, markersize=7,  zorder=8,
                    alpha=twinkle * 0.45)
            ax.plot(evt_yr, f_e, "o", color="white", markersize=4.5, zorder=9,
                    alpha=twinkle * 0.95, markeredgecolor=col, markeredgewidth=1.0)

        else:
            # ── Phase 3: settle — small dim persistent dot ──
            ax.plot(evt_yr, f_e, "o", color=col, markersize=3.5, zorder=7,
                    markeredgecolor=T3, markeredgewidth=0.4, alpha=0.50)

    # ── Factoid header — update fstate when timeline first crosses a factoid year ─
    yr_int = int(yr_float)
    if yr_int in FACTOIDS and yr_int != fstate["last_yr"]:
        headline, _, emoji = FACTOIDS[yr_int]
        fstate["text"]    = f"{yr_int} \u2014 {headline}"
        fstate["start"]   = frame_idx
        fstate["last_yr"] = yr_int

    el       = frame_idx - fstate["start"]
    fdr      = int(10.0 * FPS)    # total display duration (10 seconds)
    fade_f   = int(0.8 * FPS)     # fade-in and fade-out window (0.8 s)
    if el < fade_f:
        hdr_a = el / fade_f
    elif el < fdr - fade_f:
        hdr_a = 1.0
    elif el < fdr:
        hdr_a = (fdr - el) / fade_f
    else:
        hdr_a = 0.0
    factoid_hdr.set_text(fstate["text"])
    factoid_hdr.set_alpha(hdr_a)

# ─── Intro card ───────────────────────────────────────────────────────────────
def draw_intro(frame_idx):
    t = frame_idx / INTRO_F
    fade = min(1.0, t * 3.0)
    slide = ease_in_out(min(1.0, t * 1.8))

    BAR_AX.cla(); BAR_AX.set_facecolor(BG); BAR_AX.axis("off")
    LINE_AX.cla(); LINE_AX.set_facecolor(BG); LINE_AX.axis("off")

    BAR_AX.set_xlim(0,1); BAR_AX.set_ylim(0,1)

    bar_c = slide * 1.29
    BAR_AX.barh(0.5, slide, height=0.28, color=temp_color(bar_c),
                transform=BAR_AX.transAxes, zorder=3, left=0)
    BAR_AX.text(0.5, 0.5, f"{fmt_f(bar_c)} ({bar_c:+.2f}°C)",
                transform=BAR_AX.transAxes, ha="center", va="center",
                fontsize=26, fontweight="bold", color="white", alpha=fade, zorder=5)
    BAR_AX.text(0.5, 0.30, "245 years of global temperature data  ·  1781–2025",
                transform=BAR_AX.transAxes, ha="center", va="center",
                fontsize=14, color=T2, alpha=fade*0.8)

    year_txt.set_text("")
    factoid_hdr.set_alpha(0)

    LINE_AX.set_xlim(START-2, END+2); LINE_AX.set_ylim(YMIN_F, YMAX_F)
    LINE_AX.axis("off")
    LINE_AX.axhline(0, color="#4A90D9", linewidth=1.2, linestyle="--",
                    alpha=0.3*fade, zorder=2)

# ─── End card ─────────────────────────────────────────────────────────────────
def draw_end_card(ei):
    t = min(1.0, ei / FPS)
    a = ease_in_out(t)

    draw_bar_panel(years_seq[-1], years_seq[-1], 1.0, END, TOTAL)
    draw_timeline_panel(float(END), END, TOTAL)

    ov = mpatches.Rectangle((0,0),1,1, transform=BAR_AX.transAxes,
                              color=BG, alpha=0.38*a, zorder=10)
    BAR_AX.add_patch(ov)

    BAR_AX.text(0.5, 0.50, "@DataVibe",
                transform=BAR_AX.transAxes, ha="center", va="center",
                fontsize=14, color=T3, alpha=a*0.60, zorder=12)

# ─── Master update ────────────────────────────────────────────────────────────
def update(frame_idx):
    if frame_idx < INTRO_F:
        draw_intro(frame_idx)
    elif frame_idx < INTRO_F + len(race_frames):
        ri = frame_idx - INTRO_F
        ya, yb, t, dy = race_frames[ri]
        draw_bar_panel(ya, yb, t, dy, frame_idx)

        FIRST_HOLD = HOLD * 3
        if ri < FIRST_HOLD:
            tl_yr = float(START)
        else:
            tl_yr = min(float(END), START + (ri - FIRST_HOLD) / (FPY + HOLD))

        draw_timeline_panel(tl_yr, dy, frame_idx)
    else:
        draw_end_card(frame_idx - INTRO_F - len(race_frames))
    return []

# ─── Render ───────────────────────────────────────────────────────────────────
ani = FuncAnimation(fig, update, frames=TOTAL, blit=False, interval=1000/FPS)

OUT = "/sessions/serene-elegant-goodall/mnt/data_viz/temperature_channel/output/hottest_years_v4.mp4"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

writer = FFMpegWriter(
    fps=FPS, bitrate=12000, codec="libx264",
    extra_args=["-pix_fmt","yuv420p","-preset","medium","-crf","16"],
    metadata={"title":"Hottest Years on Record — Data Vibe",
              "artist":"DataVibe","year":"2026"}
)

def prog(i, total):
    if i % 120 == 0:
        pct=100*i/total
        bar="█"*int(pct/5)+"░"*(20-int(pct/5))
        print(f"\r  [{bar}] {pct:5.1f}%  frame {i}/{total}", end="", flush=True)

ani.save(OUT, writer=writer, dpi=100, progress_callback=prog)
print(f"\n\n  ✅  {OUT}")
print(f"  {os.path.getsize(OUT)/1e6:.1f} MB  |  {TOTAL/FPS:.1f}s")
