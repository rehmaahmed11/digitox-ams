# Shared timeline for the AMS Caps Lock OSD promo (seconds)
DURATION = 65.0
FPS = 30

# Scene boundaries
SCENES = [
    ("hook",     0.0,  8.0),
    ("problem",  8.0, 18.0),
    ("reveal",  18.0, 24.0),
    ("demo",    24.0, 36.0),
    ("features",36.0, 50.0),
    ("install", 50.0, 56.0),
    ("cta",     56.0, 65.0),
]

# Voice-over start times
VO = [("s1", 0.6), ("s2", 8.6), ("s3", 19.0), ("s4", 24.6), ("s5", 36.6), ("s6", 50.4), ("s7", 56.8)]

def typing(start, end, text):
    """Return list of (time, partial_text) per character."""
    n = len(text)
    return [(start + (end - start) * i / max(1, n), text[: i + 1]) for i in range(n)]

# ---- Hook: e-mail typing
HOOK_A = ("Thanks for the update. I'll send the ", 1.0, 3.75)
HOOK_B = ("FINAL REPORT BY FRIDAY", 3.9, 5.35)
HOOK_ALERT = 5.6

# ---- Problem chips
PROB_CHIPS = [("Wrong passwords", 8.7), ("SHOUTING EMAILS", 10.1), ("Retyping whole paragraphs", 11.6)]
PROB_KEY = 13.3

# ---- Demo
DEMO_PRESSES = [(25.3, True), (29.4, False), (33.2, True)]
DEMO_TYPING = [
    ("\u2022 Deadline: ", 24.45, 25.15),
    ("FRIDAY", 25.65, 26.25),
    (" at noon.", 29.75, 30.35),
    ("\n\u2022 Remember to ", 30.6, 31.6),
    ("BACK UP FILES", 33.5, 34.4),
]
OSD_FADE_IN, OSD_HOLD, OSD_FADE_OUT = 0.17, 1.6, 0.42

# ---- Features (card reveal times)
FEATURE_TIMES = [36.7, 39.1, 41.0, 42.8, 44.6, 46.2]

# ---- Install checkmarks
INSTALL_CHECKS = [50.9, 52.1, 53.4]

# Transitions (for whooshes)
CUTS = [8.0, 24.0, 36.0, 50.0, 56.0]

def char_times():
    """All key-click times (typing) for the sound design."""
    ts = []
    for txt, a, b in (HOOK_A, HOOK_B):
        ts += [t for t, _ in typing(a, b, txt)]
    for txt, a, b in DEMO_TYPING:
        ts += [t for t, _ in typing(a, b, txt) if not txt.startswith("\n") or True]
    return ts
