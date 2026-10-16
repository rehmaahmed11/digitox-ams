# Synthesizes music + SFX and mixes with the voice-over -> mix.wav
import numpy as np, subprocess, wave, os
from scipy.signal import butter, sosfilt, lfilter
from timeline import *

SR = 44100
N = int(SR * DURATION)
rng = np.random.default_rng(7)
HERE = os.path.dirname(os.path.abspath(__file__))

def T(sec): return np.arange(int(sec * SR)) / SR
def hz(note):  # 'A3' etc
    names = {'C':-9,'C#':-8,'D':-7,'D#':-6,'E':-5,'F':-4,'F#':-3,'G':-2,'G#':-1,'A':0,'A#':1,'B':2}
    n, o = note[:-1], int(note[-1])
    return 440.0 * 2 ** ((names[n] + (o - 4) * 12) / 12)
def lp(x, f, order=2): return sosfilt(butter(order, f / (SR / 2), 'low', output='sos'), x)
def hp(x, f, order=2): return sosfilt(butter(order, f / (SR / 2), 'high', output='sos'), x)
def bp(x, lo, hi, order=2): return sosfilt(butter(order, [lo / (SR / 2), hi / (SR / 2)], 'band', output='sos'), x)

L = np.zeros(N); R = np.zeros(N)
def add(sig, t0, gain=1.0, pan=0.0, bus=None):
    i = int(t0 * SR)
    if i >= N: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]
    l = gain * np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
    r = gain * np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
    (bus or (L, R))[0][i:i + len(sig)] += sig * l
    (bus or (L, R))[1][i:i + len(sig)] += sig * r

# ----------------------------------------------------------------- MUSIC
ML = np.zeros(N); MR = np.zeros(N); MUS = (ML, MR)
BPM = 120; BEAT = 60 / BPM; BAR = BEAT * 4
CHORDS = {
    'Am': ('A2', ['A3', 'C4', 'E4'], ['A4', 'C5', 'E5', 'C5']),
    'F':  ('F2', ['F3', 'A3', 'C4'], ['F4', 'A4', 'C5', 'A4']),
    'C':  ('C3', ['G3', 'C4', 'E4'], ['G4', 'C5', 'E5', 'C5']),
    'G':  ('G2', ['G3', 'B3', 'D4'], ['G4', 'B4', 'D5', 'B4']),
}
PROG = ['Am', 'F', 'C', 'G']
nbars = int(DURATION / BAR) + 1

def saw_pad(f, dur):
    t = T(dur); s = np.zeros_like(t)
    for det in (-0.12, 0.0, 0.11):
        ff = f * 2 ** (det / 12)
        for k in range(1, 9):
            s += np.sin(2 * np.pi * ff * k * t + rng.random() * 6.28) / k
    return s / 12

def env_adsr(n, a, r):
    e = np.ones(n); na = int(a * SR); nr = int(r * SR)
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr)
    return e

def pluck(f, dur=0.45):
    t = T(dur)
    s = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) + 0.25 * np.sin(2 * np.pi * 3 * f * t))
    return s * np.exp(-t * 9) * np.minimum(1, t * 400)

def kick():
    t = T(0.45)
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7)
    s += 0.3 * hp(rng.standard_normal(len(t)), 2000) * np.exp(-t * 120)
    return np.tanh(s * 1.6)

def clap():
    t = T(0.25); n = rng.standard_normal(len(t))
    e = np.exp(-t * 22) + 0.6 * np.exp(-np.maximum(0, t - 0.012) * 30) * (t > 0.012)
    return bp(n, 900, 5000) * e * 0.8

def hat(open_=False):
    t = T(0.18 if open_ else 0.06); n = rng.standard_normal(len(t))
    return hp(n, 7000) * np.exp(-t * (18 if open_ else 70))

def bass_note(f, dur):
    t = T(dur)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
    return np.tanh(1.4 * s) * env_adsr(len(t), 0.005, 0.06)

INTRO_END = 18.0
for b in range(nbars):
    t0 = b * BAR
    if t0 >= DURATION: break
    name = PROG[b % 4] if t0 >= INTRO_END else ['Am', 'F'][b % 2]
    root, pad, arp = CHORDS[name]
    final = t0 >= 62.0
    # Pad
    padsig = sum(saw_pad(hz(n), BAR + 0.6) for n in pad)
    padsig = lp(padsig, 900 if t0 < INTRO_END else 2200) * env_adsr(len(padsig), 0.35, 0.6)
    pg = 1.0 if t0 < INTRO_END else 0.42
    if final: pg = 0.0
    add(padsig, t0, pg * 0.5, -0.3, MUS); add(padsig, t0 + 0.01, pg * 0.5, 0.3, MUS)

    if t0 < INTRO_END:
        # building pulse from 8s
        if t0 >= 8.0:
            for i in range(8):
                g = 0.22 + 0.25 * (t0 - 8) / 10
                add(lp(pluck(hz(root.replace('2', '3'))), 1500), t0 + i * BEAT / 2, g, 0.0, MUS)
        continue
    if final: continue
    # Main groove
    for i in range(8):
        tt = t0 + i * BEAT / 2
        add(pluck(hz(arp[i % 4])), tt, 0.16, -0.4 if i % 2 else 0.4, MUS)
        add(bass_note(hz(root), BEAT / 2 - 0.02), tt, 0.32, 0, MUS)
        if i % 2 == 1: add(hat(), tt, 0.10, 0.25, MUS)
    for i in range(4):
        add(kick(), t0 + i * BEAT, 0.62, 0, MUS)
        if i in (1, 3): add(clap(), t0 + i * BEAT, 0.28, 0, MUS)

# Sidechain pump (from kicks) on music
pump = np.ones(N)
for b in range(int(INTRO_END / BEAT), int(62.0 / BEAT)):
    i = int(b * BEAT * SR); n = int(0.25 * SR)
    pump[i:i + n] = np.minimum(pump[i:i + n], 0.55 + 0.45 * np.linspace(0, 1, n) ** 0.7)

# Final chord (62s) - big sustained Am with shimmer
fin = sum(saw_pad(hz(n), 3.0) for n in ['A2', 'E3', 'A3', 'C4', 'E4', 'A4'])
fin = lp(fin, 2600) * np.exp(-T(3.0) * 0.45) * np.minimum(1, T(3.0) * 60)
add(fin, 62.0, 0.30, -0.2, MUS); add(fin, 62.01, 0.30, 0.2, MUS)
add(kick(), 62.0, 0.7, 0, MUS)

# Riser into reveal & CTA
def riser(dur, f0=300, f1=6000):
    t = T(dur); n = rng.standard_normal(len(t))
    out = np.zeros_like(t); seg = 2048
    for s in range(0, len(t), seg):
        fc = f0 * (f1 / f0) ** (s / len(t))
        out[s:s + seg] = bp(n[s:s + seg + 0], max(60, fc * 0.7), min(SR / 2 - 100, fc * 1.3), 1)
    return out * (t / dur) ** 2
add(riser(2.4), 15.6, 0.35, 0, MUS)
add(riser(1.4, 500, 8000), 54.6, 0.25, 0, MUS)

# ----------------------------------------------------------------- SFX
SL = np.zeros(N); SRR = np.zeros(N); SFX = (SL, SRR)
def keyclick():
    t = T(0.05)
    s = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 180) * 0.6
    s += np.sin(2 * np.pi * (1800 + rng.random() * 600) * t) * np.exp(-t * 250) * 0.4
    return s
def capsclack():
    t = T(0.12)
    s = np.sin(2 * np.pi * 170 * t) * np.exp(-t * 45)
    s += hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 140) * 0.7
    return s
def bell(freqs, dur=0.9, gap=0.07):
    out = np.zeros(int(dur * SR) + int(gap * SR * len(freqs)))
    for k, f in enumerate(freqs):
        t = T(dur)
        s = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2.01 * f * t) + 0.12 * np.sin(2 * np.pi * 3.02 * f * t))
        s *= np.exp(-t * 5) * np.minimum(1, t * 300)
        i = int(k * gap * SR); out[i:i + len(s)] += s
    return out
def whoosh(dur=0.7):
    t = T(dur); n = rng.standard_normal(len(t)); out = np.zeros_like(t); seg = 1024
    for s in range(0, len(t), seg):
        x = s / len(t); fc = 400 + 3500 * np.sin(np.pi * x)
        out[s:s + seg] = bp(n[s:s + seg], fc * 0.6, fc * 1.4, 1)
    return out * np.sin(np.pi * t / dur) ** 2
def boom():
    t = T(2.2)
    f = 30 + 60 * np.exp(-t * 6)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.8)
    s += lp(rng.standard_normal(len(t)), 900) * np.exp(-t * 5) * 0.5
    return np.tanh(s * 1.5)
def buzz():
    t = T(0.16); s = np.sign(np.sin(2 * np.pi * 120 * t)) * 0.5
    return lp(s, 1800) * env_adsr(len(t), 0.005, 0.04)
def pop():
    t = T(0.12); f = 380 + 700 * np.exp(-t * 40)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
def shimmer():
    out = np.zeros(int(2.5 * SR))
    notes = ['A5', 'C6', 'E6', 'A6', 'C7', 'E7']
    for k, n in enumerate(notes):
        b = bell([hz(n)], 1.6, 0)
        i = int(k * 0.07 * SR); out[i:i + len(b)] += b * 0.5
    return out

for t in char_times():
    add(keyclick(), t, 0.22, rng.uniform(-0.3, 0.3), SFX)
for t, on in DEMO_PRESSES:
    add(capsclack(), t, 0.5, 0, SFX)
    add(bell([hz('E6'), hz('B6')] if on else [hz('B5'), hz('E5')], 0.8), t + 0.05, 0.16, 0, SFX)
add(capsclack(), HOOK_B[1] - 0.12, 0.45, 0, SFX)
add(buzz(), HOOK_ALERT, 0.18, 0, SFX); add(buzz(), HOOK_ALERT + 0.2, 0.18, 0, SFX)
add(buzz(), PROB_CHIPS[0][1] + 0.35, 0.16, -0.2, SFX); add(buzz(), PROB_CHIPS[0][1] + 0.55, 0.16, -0.2, SFX)
for name, t in PROB_CHIPS: add(whoosh(0.4), t - 0.15, 0.18, -0.5, SFX)
add(capsclack(), PROB_KEY + 0.25, 0.4, 0, SFX)
for c in CUTS: add(whoosh(0.8), c - 0.45, 0.30, 0, SFX)
add(boom(), 18.0, 0.42, 0, SFX)
add(shimmer(), 18.15, 0.25, 0, SFX)
for t in FEATURE_TIMES: add(pop(), t, 0.30, 0, SFX)
for t in INSTALL_CHECKS: add(bell([hz('A6')], 0.6), t, 0.14, 0.2, SFX)
add(shimmer(), 56.2, 0.22, 0, SFX)
add(pop(), 59.3, 0.3, 0, SFX); add(pop(), 59.6, 0.3, 0, SFX)

# ----------------------------------------------------------------- VOICE
VL = np.zeros(N)
for name, t0 in VO:
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(HERE, 'vo', name + '.wav'), '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'],
                         capture_output=True).stdout
    v = np.frombuffer(raw, np.int16).astype(np.float64) / 32768
    i = int(t0 * SR); v = v[: N - i]; VL[i:i + len(v)] += v
# gentle voice EQ / presence
VL = hp(VL, 80) + 0.15 * bp(VL, 2500, 6000)
VL = VL / (np.max(np.abs(VL)) + 1e-9) * 0.85

# Duck music under voice
env = np.abs(VL)
env = lfilter([1 - 0.9995], [1, -0.9995], env)  # smooth
env = env / (env.max() + 1e-9)
duck = 1 - 0.62 * np.clip(env * 6, 0, 1)
duck = lfilter([1 - 0.9998], [1, -0.9998], duck - 1) + 1
# master fades
fade = np.ones(N)
fi = int(0.4 * SR); fade[:fi] = np.linspace(0, 1, fi)
fo = int(1.6 * SR); fade[-fo:] = np.linspace(1, 0, fo) ** 1.5

mus_gain = 0.30
outL = (ML * pump * duck * mus_gain + SL * 0.9 + VL) * fade
outR = (MR * pump * duck * mus_gain + SRR * 0.9 + VL) * fade
peak = max(np.abs(outL).max(), np.abs(outR).max())
outL = np.tanh(outL / peak * 1.1) * 0.92; outR = np.tanh(outR / peak * 1.1) * 0.92
st = np.stack([outL, outR], 1)
with wave.open(os.path.join(HERE, 'mix.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print('mix.wav written', st.shape[0] / SR, 's')
