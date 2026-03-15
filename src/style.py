"""
style.py  –  Visual design constants for all temperature channel animations.

All videos share this style for brand consistency:
  - 4K dark-theme output
  - Warm-to-cool color semantics for temperature
  - Inter/Helvetica font stack
  - 30 fps smooth animation
"""

# ─── Canvas & Output ──────────────────────────────────────────────────────────
VIDEO_WIDTH  = 3840   # 4K UHD
VIDEO_HEIGHT = 2160
VIDEO_FPS    = 30
VIDEO_DPI    = 200    # for matplotlib figure sizing (figsize = px/dpi)

FIGSIZE = (VIDEO_WIDTH / VIDEO_DPI, VIDEO_HEIGHT / VIDEO_DPI)  # (19.2, 10.8)

# For YouTube Shorts (9:16)
SHORT_WIDTH  = 1080
SHORT_HEIGHT = 1920
SHORT_FIGSIZE = (SHORT_WIDTH / VIDEO_DPI, SHORT_HEIGHT / VIDEO_DPI)

# ─── Background & Panel Colors ───────────────────────────────────────────────
BG_COLOR        = "#0D1117"   # near-black (GitHub dark mode inspired)
PANEL_COLOR     = "#161B22"   # slightly lighter panels / cards
PANEL_BORDER    = "#30363D"   # subtle border / grid lines
HIGHLIGHT_COLOR = "#1F6FEB"   # electric blue accent

# ─── Typography ───────────────────────────────────────────────────────────────
FONT_FAMILY   = "DejaVu Sans"   # always available in matplotlib; swap for
                                 # 'Helvetica Neue' / 'Inter' if installed

FONT_TITLE    = {"family": FONT_FAMILY, "size": 52, "weight": "bold",  "color": "#FFFFFF"}
FONT_SUBTITLE = {"family": FONT_FAMILY, "size": 28, "weight": "normal","color": "#8B949E"}
FONT_LABEL    = {"family": FONT_FAMILY, "size": 22, "weight": "normal","color": "#C9D1D9"}
FONT_VALUE    = {"family": FONT_FAMILY, "size": 26, "weight": "bold",  "color": "#FFFFFF"}
FONT_YEAR     = {"family": FONT_FAMILY, "size": 88, "weight": "bold",  "color": "#FFFFFF"}
FONT_FACTOID  = {"family": FONT_FAMILY, "size": 24, "weight": "normal","color": "#E6EDF3"}
FONT_SOURCE   = {"family": FONT_FAMILY, "size": 18, "weight": "normal","color": "#484F58"}

# ─── Temperature Color Scale ─────────────────────────────────────────────────
# Used for temperature anomaly coloring:
#   deep blue  = very cold anomaly  (-3°C or more below baseline)
#   white/grey = near baseline
#   deep red   = very hot anomaly   (+3°C or more above baseline)

TEMP_COLD_EXTREME   = "#053061"   # dark blue
TEMP_COLD           = "#2166AC"   # blue
TEMP_COOL           = "#74ADD1"   # light blue
TEMP_NEUTRAL        = "#F7F7F7"   # near white
TEMP_WARM           = "#F46D43"   # orange
TEMP_HOT            = "#D73027"   # red
TEMP_HOT_EXTREME    = "#67001F"   # deep red

# ─── Matplotlib Colormap (for heatmaps & lines colored by anomaly) ───────────
import matplotlib.colors as mcolors

TEMP_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "temp_channel",
    [
        (0.0,  TEMP_COLD_EXTREME),
        (0.2,  TEMP_COLD),
        (0.35, TEMP_COOL),
        (0.5,  TEMP_NEUTRAL),
        (0.65, TEMP_WARM),
        (0.8,  TEMP_HOT),
        (1.0,  TEMP_HOT_EXTREME),
    ]
)

def anomaly_to_color(anomaly_c: float, vmin: float = -3.0, vmax: float = 3.0) -> str:
    """Return a hex color string for a given temperature anomaly (°C)."""
    norm_val = (anomaly_c - vmin) / (vmax - vmin)
    norm_val = max(0.0, min(1.0, norm_val))
    rgba = TEMP_CMAP(norm_val)
    return mcolors.to_hex(rgba)


# ─── Grid & Axes ─────────────────────────────────────────────────────────────
GRID_ALPHA    = 0.15
GRID_COLOR    = "#8B949E"
GRID_LINESTYLE = "--"
SPINE_COLOR   = "#30363D"

# ─── Line chart defaults ─────────────────────────────────────────────────────
LINE_WIDTH_MAIN   = 2.8   # active / highlighted city
LINE_WIDTH_BG     = 1.2   # other cities in background
LINE_ALPHA_BG     = 0.35
MARKER_SIZE       = 7     # dot at the line's current endpoint

# ─── Bar chart defaults ──────────────────────────────────────────────────────
BAR_HEIGHT        = 0.72   # fraction of row height (0–1)
BAR_CORNER_RADIUS = 8      # px, for rounded bar ends (drawn manually)
BAR_LABEL_PAD     = 12     # px gap between bar end and value label

# ─── Animation easing ────────────────────────────────────────────────────────
import numpy as np

def ease_in_out_cubic(t: float) -> float:
    """Smooth start/stop easing, t ∈ [0, 1]."""
    if t < 0.5:
        return 4 * t ** 3
    return 1 - (-2 * t + 2) ** 3 / 2

def ease_out_expo(t: float) -> float:
    """Fast start, soft landing – good for bar updates."""
    if t >= 1.0:
        return 1.0
    return 1 - 2 ** (-10 * t)

def ease_in_out_frames(n_frames: int) -> np.ndarray:
    """Return array of eased positions 0→1 over n_frames."""
    t = np.linspace(0, 1, n_frames)
    return np.array([ease_in_out_cubic(x) for x in t])


# ─── Factoid Card ────────────────────────────────────────────────────────────
FACTOID_BG        = "#161B22"
FACTOID_BORDER    = "#388BFD"
FACTOID_BORDER_W  = 3       # pt
FACTOID_ALPHA     = 0.92
FACTOID_DURATION  = 5.0     # seconds on screen
FACTOID_FADE_TIME = 0.5     # seconds fade in / out

# ─── Watermark / branding ────────────────────────────────────────────────────
CHANNEL_NAME   = "Data Vibe"
SOURCE_TEXT    = "Data: Berkeley Earth  •  Baseline: 1951–1980  •  @DataVibe"

# ─── Matplotlib rcParams snapshot ────────────────────────────────────────────
# Apply with:  plt.rcParams.update(RC_PARAMS)
import matplotlib as mpl

RC_PARAMS = {
    "figure.facecolor":    BG_COLOR,
    "axes.facecolor":      BG_COLOR,
    "axes.edgecolor":      SPINE_COLOR,
    "axes.labelcolor":     "#C9D1D9",
    "axes.titlecolor":     "#FFFFFF",
    "xtick.color":         "#8B949E",
    "ytick.color":         "#8B949E",
    "text.color":          "#E6EDF3",
    "grid.color":          GRID_COLOR,
    "grid.alpha":          GRID_ALPHA,
    "grid.linestyle":      GRID_LINESTYLE,
    "lines.linewidth":     LINE_WIDTH_MAIN,
    "font.family":         FONT_FAMILY,
    "font.size":           22,
    "savefig.facecolor":   BG_COLOR,
    "savefig.dpi":         VIDEO_DPI,
    "animation.writer":    "ffmpeg",
    "animation.bitrate":   20000,   # kbps – high quality for YouTube
}
