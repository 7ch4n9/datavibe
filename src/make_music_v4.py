#!/usr/bin/env python3
"""
make_music_v4.py  —  Generate a ~172-second ambient cinematic soundtrack for
                     "Hottest Years in Recorded History" v4 (GloSAT 1781–2025).

Video specs (from demo_v4_render.py):
  FPS=30, FPY=12, HOLD=8  →  FPY+HOLD=20 frames/year  (slowed for readability)
  INTRO_F = 90, FIRST_HOLD = HOLD*3 = 24, END_F = 180
  Years: 1781–2025 → 244 transitions
  Total frames: 90 + 244×20 + 180 = 5150 frames
  DUR = 5150 / 30 = 171.667 s

Beat drop timing — year 1937 (offset 156 from START=1781):
  INTRO_F(90) + FIRST_HOLD(24) + 156 × 20 = 3234 frames
  3234 / 30 fps = 107.8 s

Sound design arc (matching 245 years of history):
  0–40s    : Cold/ominous (C minor bass drone + low pad) — pre-industrial era
  40–108s  : Tension builds (chord layers stack in) — industrialisation
  108s     : BEAT DROP — year 1937, modern era begins
  108–160s : Full intensity, shimmer layers — rapid warming
  160–172s : Fade out

Usage:
    python make_music_v4.py
Outputs:
    output/soundtrack_v4.wav
    mnt/data_viz/temperature_channel/output/hottest_years_v4_music.mp4
"""

import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt
from scipy.io import wavfile
import subprocess, os, sys

# ─── Timing constants (must match demo_v4_render.py) ─────────────────────────
# FPY=12, HOLD=8 → FPY+HOLD=20;  FIRST_HOLD = HOLD*3 = 24
TOTAL_FRAMES = 90 + 244 * 20 + 180         # = 5150
FPS          = 30
SR           = 44100
DUR          = TOTAL_FRAMES / FPS          # = 171.667 s
N            = int(SR * DUR)
t            = np.linspace(0, DUR, N, endpoint=False)

# Year 1937 is at offset 156 from START=1781
# Frame: INTRO_F(90) + FIRST_HOLD(24) + 156*20 = 3234
T_DROP      = (90 + 24 + 156 * 20) / FPS   # = 107.8 s (year 1937)
RISER_START = T_DROP - 15.0                 # = 92.8 s — extended 15s riser

print(f"  DUR        = {DUR:.3f} s")
print(f"  T_DROP     = {T_DROP:.3f} s  (year 1937)")
print(f"  RISER_START= {RISER_START:.3f} s")

# ─── Synthesis helpers ────────────────────────────────────────────────────────
def osc(freq, detune_cents=0, wave="sine"):
    f = freq * (2 ** (detune_cents / 1200.0))
    if wave == "sine":
        return np.sin(2 * np.pi * f * t)
    if wave == "tri":
        return 2 * np.abs(2 * (f * t % 1) - 1) - 1
    if wave == "saw":
        return 2 * (f * t % 1) - 1

def adsr(attack, decay, sustain_lv, release, total, start=0.0):
    """Vectorised ADSR envelope over the global time array."""
    tr  = np.clip(t - start, 0, None)
    env = np.zeros(N)
    m = tr < attack
    env[m] = tr[m] / max(attack, 1e-9)
    m = (tr >= attack) & (tr < attack + decay)
    env[m] = 1.0 - (1.0 - sustain_lv) * (tr[m] - attack) / max(decay, 1e-9)
    m = (tr >= attack + decay) & (tr < total - release)
    env[m] = sustain_lv
    m = (tr >= total - release) & (tr < total)
    rem = total - t[m]
    env[m] = sustain_lv * rem / max(release, 1e-9)
    return env

def smooth_ramp(t0, t1, v0=0.0, v1=1.0):
    """Smooth S-curve ramp between two values over a time window."""
    x = np.clip((t - t0) / max(t1 - t0, 1e-9), 0, 1)
    s = 3*x**2 - 2*x**3    # smoothstep
    return v0 + (v1 - v0) * s

# ─── Note frequencies (Hz) ───────────────────────────────────────────────────
C2, G2       = 65.41,  98.00
C3, Eb3, G3  = 130.81, 155.56, 196.00
Bb3, F3      = 233.08, 174.61
C4, Eb4, G4  = 261.63, 311.13, 392.00
Bb4, Ab4     = 466.16, 415.30
C5, Eb5      = 523.25, 622.25

# ─── Build mix ────────────────────────────────────────────────────────────────
mix = np.zeros(N)

# ── 1. Bass drone  (C2, full length, slow fade-in over 5s) ───────────────────
e1   = adsr(attack=5.0, decay=4.0, sustain_lv=0.60, release=6.0, total=DUR)
bass = (osc(C2)*0.60 + osc(C2*2)*0.22 + osc(C2*3)*0.10 + osc(C2*4)*0.06)
bass *= e1 * 0.28
# Slow tremolo (0.07 Hz) — longer arc, more glacial feel
bass *= 1.0 + 0.06 * np.sin(2*np.pi*0.07*t)
mix += bass
print("  ✅  Layer 1: bass drone")

# ── 2. Low Cm pad  (enters ~5s, hushed pre-drop, swells to full at T_DROP) ───
e2 = adsr(attack=10.0, decay=5.0, sustain_lv=0.65, release=10.0, total=DUR, start=4.0)
pre_drop_gain = smooth_ramp(T_DROP - 2.0, T_DROP + 2.0, 0.25, 1.0)
pad_low = (osc(C3,  -6) + osc(C3,  +6) +
           osc(Eb3, -5) + osc(Eb3, +5) +
           osc(G3,  -7) + osc(G3,  +7)) / 6.0
pad_low *= e2 * pre_drop_gain * 0.18
mix += pad_low
print("  ✅  Layer 2: low Cm pad")

# ── 3. Tension chord  (enters ~40s, Bb3/F3 for Cm7 darkness) ─────────────────
# Builds across industrialisation era (~1850–1937)
e3    = adsr(attack=16.0, decay=5.0, sustain_lv=0.70, release=14.0, total=DUR, start=38.0)
swell3 = smooth_ramp(38, 105, 0.0, 1.0)
pad_mid = (osc(Bb3, -4) + osc(Bb3, +4) +
           osc(F3,  -5) + osc(F3,  +5)) / 4.0
pad_mid *= e3 * swell3 * 0.16
mix += pad_mid
print("  ✅  Layer 3: tension chord (Cm7)")

# ── 4. Mid shimmer  (enters ~90s, C4/Eb4/G4) — post-WWII warming era ─────────
e4    = adsr(attack=14.0, decay=4.0, sustain_lv=0.72, release=13.0, total=DUR, start=88.0)
swell4 = smooth_ramp(88, 138, 0.0, 1.0)
pad_hi = (osc(C4,  -3) + osc(C4,  +3) +
          osc(Eb4, -4) + osc(Eb4, +4) +
          osc(G4,  -5) + osc(G4,  +5)) / 6.0
pad_hi *= e4 * swell4 * 0.15
mix += pad_hi
print("  ✅  Layer 4: mid shimmer (C4)")

# ── 5. High climax layer  (enters ~130s, C5+Eb5 — intense heat) ──────────────
e5    = adsr(attack=10.0, decay=2.0, sustain_lv=0.80, release=10.0, total=DUR, start=128.0)
swell5 = smooth_ramp(128, 158, 0.0, 1.0)
pad_top = (osc(C5,  -2) + osc(C5,  +2) +
           osc(Eb5, -3) + osc(Eb5, +3)) / 4.0
pad_top *= e5 * swell5 * 0.18
mix += pad_top
print("  ✅  Layer 5: high shimmer (C5)")

# ── 6. Sub-bass rumble  (enters ~150s, G2 — building dread / climax) ─────────
e6 = adsr(attack=6.0, decay=2.0, sustain_lv=0.85, release=8.0, total=DUR, start=148.0)
sub_ramp = smooth_ramp(148, 165, 0.0, 1.0)
sub = osc(G2) * 0.40 + osc(G2*2) * 0.18
sub *= e6 * sub_ramp * 0.18
# Slow tension LFO
sub *= 1.0 + 0.12 * np.sin(2*np.pi*0.4*t)
mix += sub
print("  ✅  Layer 6: sub-bass rumble (G2)")

# ── 7. Frequency riser — 15s build leading into beat drop ────────────────────
# Layer A: quadratic chirp from 40 Hz → 900 Hz (wider sweep, starts deeper)
# Layer B: filtered white noise sweep for density and tension
riser_dur     = T_DROP - RISER_START
n_riser       = int(riser_dur * SR)
t_r           = np.linspace(0, riser_dur, n_riser, endpoint=False)
rng_r         = np.random.RandomState(17)

# Chirp (wide sweep, power-curve envelope — nearly silent for first 5s, then builds fast)
phase_r   = 2 * np.pi * (40.0 * t_r + (900.0 - 40.0) / (2 * riser_dur) * t_r ** 2)
riser_env = (t_r / riser_dur) ** 2.8    # stays quiet long, then roars
chirp_sig = np.sin(phase_r) * riser_env * 0.14

# Octave-doubled chirp for thickness
phase_r2  = 2 * np.pi * (80.0 * t_r + (1800.0 - 80.0) / (2 * riser_dur) * t_r ** 2)
chirp2    = np.sin(phase_r2) * riser_env * 0.07

# White noise sweep — band-pass filtered, gains up over final 6s
noise_raw  = rng_r.randn(n_riser)
sos_nb = butter(4, [300/(SR/2), 5000/(SR/2)], btype='band', output='sos')
noise_filt = sosfilt(sos_nb, noise_raw)
noise_env  = np.clip((t_r - (riser_dur * 0.55)) / (riser_dur * 0.45), 0, 1) ** 1.8
noise_sig  = noise_filt * noise_env * 0.055

riser_sig     = chirp_sig + chirp2 + noise_sig
riser_start_n = int(RISER_START * SR)
mix[riser_start_n : riser_start_n + n_riser] += riser_sig
print(f"  ✅  Layer 7: riser {RISER_START:.2f}s → {T_DROP:.2f}s (15s sweep + noise)")

# ── 8. Bass hit + impact burst + post-drop pulse (T_DROP = year 1937) ─────────
C1 = 32.70   # sub-octave for seismic weight

# Main impact: C1 sub-bass + C2 punch + transient click
hit_dur = 5.0
t_h     = np.linspace(0, hit_dur, int(hit_dur * SR), endpoint=False)
hit_sig = (np.sin(2 * np.pi * C1       * t_h) * 0.55 +   # seismic sub
           np.sin(2 * np.pi * C2       * t_h) * 0.55 +   # main bass
           np.sin(2 * np.pi * (C2*2.0) * t_h) * 0.20 +   # upper harmonic
           np.exp(-90.0 * t_h) * 0.45                     # transient click
           ) * np.exp(-1.5 * t_h) * 0.80                  # slow decay for weight
drop_n = int(T_DROP * SR)
mix[drop_n : drop_n + len(hit_sig)] += hit_sig

# Impact noise burst — a short white-noise crack at the exact drop moment
rng_h       = np.random.RandomState(7)
crack_dur   = 0.08
n_crack     = int(crack_dur * SR)
crack_env   = np.exp(-60.0 * np.linspace(0, crack_dur, n_crack))
crack_sig   = rng_h.randn(n_crack) * crack_env * 0.30
sos_crack   = butter(4, [800/(SR/2), 12000/(SR/2)], btype='band', output='sos')
crack_sig   = sosfilt(sos_crack, crack_sig)
mix[drop_n : drop_n + n_crack] += crack_sig

# Post-drop rhythmic pulse — 8 beats at ~120 BPM starting one beat after drop
BEAT_DUR  = 0.50   # 120 BPM
n_pulse   = int(0.35 * SR)
t_p       = np.linspace(0, 0.35, n_pulse, endpoint=False)
pulse_sig = (np.sin(2 * np.pi * C2 * t_p) * 0.65 +
             np.sin(2 * np.pi * C1 * t_p) * 0.35) * np.exp(-10.0 * t_p) * 0.45
# Beat 1 lands at T_DROP itself (already covered by hit), beats 2-8 follow
for i in range(1, 9):
    beat_t = T_DROP + i * BEAT_DUR
    beat_n = int(beat_t * SR)
    end_n  = min(N, beat_n + n_pulse)
    mix[beat_n : end_n] += pulse_sig[: end_n - beat_n]

print(f"  ✅  Layer 8: bass hit + crack + 8-beat pulse at {T_DROP:.2f}s (year 1937)")

# ─── Reverb ───────────────────────────────────────────────────────────────────
print("  Building reverb IR ...")
rng     = np.random.RandomState(42)
rt60    = 4.0                              # longer reverb for more cinematic space
n_ir    = int(rt60 * SR)
decay_e = np.exp(-6.9 * np.arange(n_ir) / n_ir)
ir      = decay_e * rng.randn(n_ir) * 0.12
sos = butter(4, [80/(SR/2), 8000/(SR/2)], btype='band', output='sos')
ir  = sosfilt(sos, ir)

print("  Applying convolution reverb ...")
wet = fftconvolve(mix, ir)[:N]
mix = mix * 0.55 + wet * 0.45   # more wet for bigger cinematic space

# ─── High-pass to remove DC / mud ────────────────────────────────────────────
sos_hp = butter(4, 35/(SR/2), btype='high', output='sos')
mix    = sosfilt(sos_hp, mix)

# ─── Master envelope (fade in 2s, fade out 5s) ───────────────────────────────
master = adsr(attack=2.0, decay=0.01, sustain_lv=1.0, release=5.0, total=DUR)
mix   *= master

# ─── Normalise ───────────────────────────────────────────────────────────────
peak = np.max(np.abs(mix))
if peak > 0:
    mix = mix / peak * 0.78

# ─── Soft stereo widener ─────────────────────────────────────────────────────
delay_n = int(0.013 * SR)
right   = np.roll(mix, delay_n)
stereo  = np.stack([mix, right], axis=1).astype(np.float32)

# ─── Save WAV ────────────────────────────────────────────────────────────────
os.makedirs("output", exist_ok=True)
wav_path = "output/soundtrack_v4.wav"
wavfile.write(wav_path, SR, stereo)
wav_mb = os.path.getsize(wav_path) / 1e6
print(f"  ✅  {wav_path}  ({wav_mb:.1f} MB, {DUR:.2f}s)")

# ─── Mix with video via ffmpeg ────────────────────────────────────────────────
video_in  = "mnt/data_viz/temperature_channel/output/hottest_years_v4.mp4"
video_out = "mnt/data_viz/temperature_channel/output/hottest_years_v4_music.mp4"

print(f"\n  Mixing audio into video ...")
fade_out_start = DUR - 8.0   # slightly longer fade for the longer video
cmd = [
    "ffmpeg", "-y",
    "-i", video_in,
    "-i", wav_path,
    "-c:v", "copy",
    "-c:a", "aac", "-b:a", "192k",
    "-filter_complex",
    f"[1:a]volume=0.42,afade=t=in:st=0:d=2,afade=t=out:st={fade_out_start:.2f}:d=5[music];"
    "[music]apad[a]",
    "-map", "0:v", "-map", "[a]",
    "-shortest",
    video_out,
]
result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0:
    size_mb = os.path.getsize(video_out) / 1e6
    print(f"  ✅  {video_out}  ({size_mb:.1f} MB)")
else:
    print("  ❌  ffmpeg error:")
    print(result.stderr[-800:])
    sys.exit(1)
