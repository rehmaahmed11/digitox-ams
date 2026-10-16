# AMS Caps Lock OSD - 65s promo renderer (pycairo + PIL + ffmpeg)
import cairo, math, re, os, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from timeline import *

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
PI = math.pi
ACC1 = (64/255, 156/255, 255/255); ACC2 = (0, 92/255, 214/255)
RED = (1.0, 0.33, 0.36)

FD = '/usr/share/fonts/opentype/inter/'
FONTS = {
    'reg': FD + 'Inter-Regular.otf', 'med': FD + 'Inter-Medium.otf', 'semi': FD + 'Inter-SemiBold.otf',
    'bold': FD + 'Inter-Bold.otf', 'xbold': FD + 'Inter-ExtraBold.otf',
    'disp': FD + 'InterDisplay-Black.otf', 'dispx': FD + 'InterDisplay-ExtraBold.otf',
}

# ------------------------------------------------------------------ helpers
def cl(x): return 0.0 if x < 0 else 1.0 if x > 1 else x
def p(t, a, d): return cl((t - a) / d)
def eo(x): x = cl(x); return 1 - (1 - x) ** 3
def eio(x): x = cl(x); return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eback(x, s=1.70158):
    x = cl(x)
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    c3 = s + 1; return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2
def lerp(a, b, k): return a + (b - a) * k

def pil_to_surface(img):
    a = np.asarray(img.convert('RGBA'), dtype=np.uint16)
    al = a[..., 3:4]
    rgb = (a[..., :3] * al + 127) // 255
    h, w = a.shape[:2]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    stride = surf.get_stride()
    buf = np.ndarray((h, stride // 4, 4), np.uint8, surf.get_data())
    buf[:, :w, 0] = rgb[..., 2]; buf[:, :w, 1] = rgb[..., 1]; buf[:, :w, 2] = rgb[..., 0]; buf[:, :w, 3] = a[..., 3]
    surf.mark_dirty()
    return surf

_fonts = {}
def font(name, size):
    k = (name, size)
    if k not in _fonts: _fonts[k] = ImageFont.truetype(FONTS[name], size)
    return _fonts[k]

_tc = {}
def text(txt, fname, size, color=(1, 1, 1), track=0.0, grad=None):
    """Returns (surface, w, h). color floats 0..1. grad=(c1,c2) horizontal gradient."""
    k = (txt, fname, size, color, track, grad)
    if k in _tc: return _tc[k]
    f = font(fname, size); asc, desc = f.getmetrics()
    if track: w = int(sum(f.getlength(c) for c in txt) + track * (len(txt) - 1)) + 8
    else: w = int(f.getlength(txt)) + 8
    h = asc + desc + 8
    mask = Image.new('L', (max(1, w), h), 0); d = ImageDraw.Draw(mask)
    if track:
        x = 4
        for c in txt: d.text((x, 4), c, font=f, fill=255); x += f.getlength(c) + track
    else: d.text((4, 4), txt, font=f, fill=255)
    if grad:
        c1, c2 = np.array(grad[0]), np.array(grad[1])
        g = np.linspace(0, 1, w)[None, :, None]
        col = (c1 * (1 - g) + c2 * g) * 255
        arr = np.repeat(col, h, 0).astype(np.uint8)
        img = Image.fromarray(arr, 'RGB').convert('RGBA')
    else:
        img = Image.new('RGBA', mask.size, tuple(int(c * 255) for c in color[:3]) + (0,))
    img.putalpha(mask)
    r = (pil_to_surface(img), w, h); _tc[k] = r
    return r

def blit(ctx, s, x, y, alpha=1.0, sc=1.0, anchor=(0.5, 0.5), filt=cairo.FILTER_GOOD):
    if alpha <= 0.002: return
    surf, w, h = s
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc); ctx.translate(-w * anchor[0], -h * anchor[1])
    ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(filt)
    ctx.paint_with_alpha(min(1, alpha)); ctx.restore()

def rr(ctx, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -PI / 2, 0); ctx.arc(x + w - r, y + h - r, r, 0, PI / 2)
    ctx.arc(x + r, y + h - r, r, PI / 2, PI); ctx.arc(x + r, y + r, r, PI, 1.5 * PI); ctx.close_path()

_sh = {}
def shadow(w, h, r, blur, alpha=0.5):
    k = (int(w), int(h), int(r), int(blur), alpha)
    if k not in _sh:
        pad = int(blur * 3)
        im = Image.new('RGBA', (int(w) + pad * 2, int(h) + pad * 2), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle([pad, pad, pad + int(w), pad + int(h)], int(r), fill=(0, 0, 0, int(255 * alpha)))
        im = im.filter(ImageFilter.GaussianBlur(blur))
        _sh[k] = (pil_to_surface(im), im.width, im.height)
    return _sh[k]

def lin(x0, y0, x1, y1, stops):
    g = cairo.LinearGradient(x0, y0, x1, y1)
    for o, c in stops: g.add_color_stop_rgba(o, *c) if len(c) == 4 else g.add_color_stop_rgb(o, *c)
    return g

def glow(ctx, cx, cy, r, col, a):
    g = cairo.RadialGradient(cx, cy, 0, cx, cy, r)
    g.add_color_stop_rgba(0, *col, a); g.add_color_stop_rgba(1, *col, 0)
    ctx.set_source(g); ctx.arc(cx, cy, r, 0, 2 * PI); ctx.fill()

def glyph(ctx, x, y, gw, gh, rad=2.0):
    pts = [(.5, 0), (1, .5), (.72, .5), (.72, .74), (.28, .74), (.28, .5), (0, .5)]
    ctx.move_to(x + pts[0][0] * gw, y + pts[0][1] * gh)
    for u, v in pts[1:]: ctx.line_to(x + u * gw, y + v * gh)
    ctx.close_path()
    rr(ctx, x + .28 * gw, y + .86 * gh, .44 * gw, .14 * gh, rad)

# ------------------------------------------------------------------ assets
def load_cover(path, blur=0, dark=0.0):
    im = Image.open(path).convert('RGB')
    s = max(W * 1.2 / im.width, H * 1.2 / im.height)
    im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    if dark: im = Image.blend(im, Image.new('RGB', im.size, (0, 0, 0)), dark)
    return (pil_to_surface(im.convert('RGBA')), im.width, im.height)

def make_bg():
    im = Image.new('RGB', (W, H), (6, 8, 15)); d = ImageDraw.Draw(im)
    for x in range(0, W, 48):
        for y in range(0, H, 48): d.ellipse([x - 1, y - 1, x + 1, y + 1], fill=(20, 26, 40))
    return pil_to_surface(im.convert('RGBA'))

def make_blobs():
    im = Image.new('RGBA', (W + 400, H + 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse([200, 150, 1100, 900], fill=(30, 90, 255, 70))
    d.ellipse([1300, 600, 2100, 1300], fill=(110, 60, 255, 55))
    d.ellipse([900, -100, 1600, 500], fill=(0, 180, 255, 35))
    im = im.filter(ImageFilter.GaussianBlur(160))
    return (pil_to_surface(im), im.width, im.height)

def make_vignette():
    y, x = np.mgrid[0:H, 0:W]
    d = np.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
    a = np.clip((d - 0.6) / 0.9, 0, 1) ** 1.6 * 200
    im = Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), a.astype(np.uint8)]), 'RGBA')
    return (pil_to_surface(im), W, H)

A = {}
def init_assets():
    A['bg'] = make_bg(); A['blobs'] = make_blobs(); A['vig'] = make_vignette()
    A['photo'] = load_cover(os.path.join(HERE, 'img/frustrated.jpg'))
    A['photo_blur'] = load_cover(os.path.join(HERE, 'img/frustrated.jpg'), blur=14, dark=0.35)
    A['wall'] = load_cover(os.path.join(HERE, 'img/wallpaper.jpg'))
    A['desk'] = load_cover(os.path.join(HERE, 'img/desk.jpg'), blur=6, dark=0.55)

def draw_cover(ctx, img, zoom=1.0, fx=0.5, fy=0.5, alpha=1.0):
    surf, w, h = img
    base = max(W / w, H / h) * zoom
    dw, dh = w * base, h * base
    fx = min(max(fx, (W / 2) / dw), 1 - (W / 2) / dw); fy = min(max(fy, (H / 2) / dh), 1 - (H / 2) / dh)
    ctx.save()
    ctx.translate(W / 2, H / 2); ctx.scale(base, base)
    ctx.translate(-w * fx, -h * fy)
    ctx.set_source_surface(surf, 0, 0); ctx.get_source().set_filter(cairo.FILTER_GOOD)
    ctx.paint_with_alpha(alpha); ctx.restore()

def dark_bg(ctx, t, blob_a=1.0):
    ctx.set_source_surface(A['bg'], 0, 0); ctx.paint()
    s, w, h = A['blobs']
    ctx.save(); ctx.translate(-200 + 80 * math.sin(t * 0.35), -200 + 60 * math.cos(t * 0.27))
    ctx.set_source_surface(s, 0, 0); ctx.paint_with_alpha(blob_a); ctx.restore()

def vignette(ctx, a=1.0):
    ctx.set_source_surface(A['vig'][0], 0, 0); ctx.paint_with_alpha(a)

# ------------------------------------------------------------------ components
def draw_osd(ctx, cx, cy, on, s, alpha=1.0, zoom=1.0):
    if alpha <= 0.003: return
    w, h, r = 176 * s, 198 * s, 26 * s
    ctx.save(); ctx.translate(cx, cy); ctx.scale(zoom, zoom); ctx.translate(-w / 2, -h / 2)
    ctx.push_group()
    blit(ctx, shadow(w, h, r, 16 * s, 0.6), w / 2, h / 2 + 7 * s)
    rr(ctx, 0, 0, w, h, r)
    ctx.set_source(lin(0, 0, 0, h, [(0, (40/255, 42/255, 48/255, .95)), (1, (24/255, 25/255, 29/255, .95))])); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, .18); ctx.set_line_width(1.0 * s); ctx.stroke()
    rr(ctx, 1, 1, w - 2, h - 2, r)
    ctx.set_source(lin(0, 0, 0, h, [(0, (1, 1, 1, .07)), (.5, (1, 1, 1, 0)), (1, (1, 1, 1, 0))])); ctx.fill()
    d = 78 * s; bcx = w / 2; bcy = 26 * s + d / 2
    if on:
        glow(ctx, bcx, bcy, d / 2 + 22 * s, ACC1, .45)
        ctx.arc(bcx, bcy, d / 2, 0, 2 * PI)
        ctx.set_source(lin(0, bcy - d / 2, 0, bcy + d / 2, [(0, ACC1), (1, ACC2)])); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, .27); ctx.set_line_width(1 * s); ctx.stroke()
        glyph(ctx, bcx - d * .23, bcy - d * .25, d * .46, d * .5, 2 * s); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    else:
        ctx.arc(bcx, bcy, d / 2, 0, 2 * PI); ctx.set_source_rgba(1, 1, 1, .11); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, .23); ctx.set_line_width(1.2 * s); ctx.stroke()
        glyph(ctx, bcx - d * .23, bcy - d * .25, d * .46, d * .5, 2 * s)
        ctx.set_source_rgba(1, 1, 1, .8); ctx.set_line_width(2.4 * s); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ctx.stroke()
    ly = 26 * s + d + 14 * s + 9 * s
    blit(ctx, text('CAPS LOCK', 'semi', 48, (1, 1, 1), track=20), w / 2, ly, .6, s / 4)
    blit(ctx, text('ON' if on else 'OFF', 'bold', 88), w / 2, ly + 9 * s + 1 * s + 15 * s, 1 if on else .73, s / 4)
    fy = h - 22 * s
    ctx.move_to(40 * s, fy - 4 * s); ctx.line_to(w - 40 * s, fy - 4 * s)
    ctx.set_source_rgba(1, 1, 1, .1); ctx.set_line_width(1 * s); ctx.stroke()
    blit(ctx, text('AMS', 'bold', 44, (120/255, 185/255, 1) if on else (1, 1, 1), track=16), w / 2, fy + 8 * s, .8 if on else .43, s / 4)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha)
    ctx.restore()

def draw_appicon(ctx, cx, cy, size, alpha=1.0, glow_a=0.6):
    ctx.save(); ctx.translate(cx, cy)
    ctx.push_group()
    if glow_a: glow(ctx, 0, 0, size * 1.1, ACC1, glow_a * .5)
    blit(ctx, shadow(size, size, size * .22, size * .08, .6), 0, size * .05)
    rr(ctx, -size / 2, -size / 2, size, size, size * .22)
    ctx.set_source(lin(0, -size / 2, 0, size / 2, [(0, ACC1), (1, ACC2)])); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, .25); ctx.set_line_width(max(1, size * .01)); ctx.stroke()
    rr(ctx, -size / 2 + 2, -size / 2 + 2, size - 4, size * .5, size * .2)
    ctx.set_source(lin(0, -size / 2, 0, 0, [(0, (1, 1, 1, .18)), (1, (1, 1, 1, 0))])); ctx.fill()
    gw, gh = size * .47, size * .55
    glyph(ctx, -gw / 2, -gh / 2 + size * .02, gw, gh, size * .025); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha); ctx.restore()

def draw_key(ctx, x, y, w, h, press=0.0, led=0.0, alpha=1.0, label='Caps Lock'):
    ctx.save(); ctx.push_group()
    depth = 16; off = press * 10
    blit(ctx, shadow(w, h, 22, 18, .7), x + w / 2, y + h / 2 + 14)
    rr(ctx, x, y + 4, w, h, 22)
    ctx.set_source(lin(0, y, 0, y + h, [(0, (.13, .14, .17)), (1, (.07, .075, .09))])); ctx.fill()
    tx, ty, tw, th = x + 10, y + off, w - 20, h - depth - 4
    rr(ctx, tx, ty, tw, th, 16)
    ctx.set_source(lin(0, ty, 0, ty + th, [(0, (.27, .29, .34)), (1, (.19, .2, .24))])); ctx.fill_preserve()
    ctx.set_source_rgba(1, 1, 1, .12); ctx.set_line_width(1.5); ctx.stroke()
    lx, ly = tx + 30, ty + 30
    if led > 0:
        glow(ctx, lx, ly, 60, (.35, .7, 1), .9 * led)
    ctx.arc(lx, ly, 9, 0, 2 * PI)
    ctx.set_source_rgb(lerp(.22, .75, led), lerp(.24, .9, led), lerp(.28, 1, led)); ctx.fill()
    blit(ctx, text(label, 'semi', 30, (.9, .92, .96)), tx + 24, ty + th - 30, 1, 1, (0, .5))
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha); ctx.restore()

def win_controls(ctx, x, y, col):
    ctx.set_source_rgba(*col); ctx.set_line_width(1.6)
    ctx.move_to(x, y); ctx.line_to(x + 14, y); ctx.stroke()
    ctx.rectangle(x + 46, y - 7, 13, 13); ctx.stroke()
    ctx.move_to(x + 92, y - 7); ctx.line_to(x + 106, y + 7); ctx.move_to(x + 106, y - 7); ctx.line_to(x + 92, y + 7); ctx.stroke()

def draw_window(ctx, x, y, w, h, title, light=False, alpha=1.0):
    blit(ctx, shadow(w, h, 14, 30, .55), x + w / 2, y + h / 2 + 18, alpha)
    rr(ctx, x, y, w, h, 14)
    ctx.set_source_rgba(*((.96, .965, .975) if light else (.118, .125, .157)), alpha); ctx.fill_preserve()
    ctx.set_source_rgba(*((0, 0, 0, .12) if light else (1, 1, 1, .1))); ctx.set_line_width(1); ctx.stroke()
    ctx.save(); rr(ctx, x, y, w, h, 14); ctx.clip()
    ctx.rectangle(x, y, w, 50); ctx.set_source_rgba(*((.9, .91, .93) if light else (.15, .16, .2)), alpha); ctx.fill()
    ctx.restore()
    blit(ctx, text(title, 'med', 19, (.15, .15, .2) if light else (.85, .87, .92)), x + 22, y + 25, alpha, 1, (0, .5))
    win_controls(ctx, x + w - 150, y + 25, (0, 0, 0, .6 * alpha) if light else (1, 1, 1, .7 * alpha))

def layout(segs, fname, size, maxw):
    f = font(fname, size); sp = f.getlength(' ')
    x = 0; line = 0; out = []
    for txt, col in segs:
        for part in re.split(r'(\n| )', txt):
            if part == '': continue
            if part == '\n': x = 0; line += 1; continue
            if part == ' ': x += sp; continue
            w = f.getlength(part)
            if x + w > maxw and x > 0: x = 0; line += 1
            out.append((x, line, part, col, w)); x += w
    return out, (x, line)

def ntyped(text_, a, b, t):
    if t < a: return 0
    return min(len(text_), int((t - a) / (b - a) * len(text_)) + 1)

def pill(ctx, x, y, label, fname='semi', size=30, bg=(.08, .09, .13, .82), border=(1, 1, 1, .15), col=(1, 1, 1), alpha=1.0, padx=28, h=64, dot=None, anchor=0.0):
    s = text(label, fname, size, col)
    w = s[1] + padx * 2 + (34 if dot else 0)
    x0 = x - w * anchor
    ctx.save(); ctx.push_group()
    blit(ctx, shadow(w, h, h / 2, 14, .5), x0 + w / 2, y + 6)
    rr(ctx, x0, y - h / 2, w, h, h / 2); ctx.set_source_rgba(*bg); ctx.fill_preserve()
    ctx.set_source_rgba(*border); ctx.set_line_width(1.5); ctx.stroke()
    tx = x0 + padx
    if dot:
        glow(ctx, tx + 8, y, 20, dot, .6); ctx.arc(tx + 8, y, 7, 0, 2 * PI); ctx.set_source_rgb(*dot); ctx.fill(); tx += 34
    blit(ctx, s, tx, y, 1, 1, (0, .5))
    ctx.pop_group_to_source(); ctx.paint_with_alpha(alpha); ctx.restore()
    return w

# ------------------------------------------------------------------ scenes
def scene_hook(ctx, t):
    dark_bg(ctx, t)
    shake = 0
    if HOOK_ALERT <= t < HOOK_ALERT + 0.45:
        k = (t - HOOK_ALERT) / 0.45; shake = math.sin(k * 40) * 14 * (1 - k)
    zoom = 1 + 0.05 * eio(p(t, 0, 8))
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(zoom, zoom); ctx.translate(-W / 2 + shake, -H / 2)
    a = eo(p(t, 0.1, 0.7))
    x, y, w, h = 260, 130 + 30 * (1 - a), 1400, 560
    if t >= HOOK_ALERT:
        glow(ctx, x + w / 2, y + h / 2, 800, RED, .22 * eo(p(t, HOOK_ALERT, .3)))
    ctx.push_group()
    draw_window(ctx, x, y, w, h, 'New message  \u2014  Mail')
    for i, (lab, val) in enumerate([('To', 'john@company.com'), ('Subject', 'Project update')]):
        yy = y + 105 + i * 72
        blit(ctx, text(lab, 'med', 30, (.55, .58, .66)), x + 50, yy, 1, 1, (0, .5))
        blit(ctx, text(val, 'med', 30, (.9, .92, .96)), x + 200, yy, 1, 1, (0, .5))
        ctx.rectangle(x + 50, yy + 34, w - 100, 1); ctx.set_source_rgba(1, 1, 1, .08); ctx.fill()
    bx, by = x + 50, y + 280
    blit(ctx, text('Hi John,', 'reg', 42, (.9, .92, .96)), bx, by, 1, 1, (0, 0))
    na = ntyped(HOOK_A[0], HOOK_A[1], HOOK_A[2], t); nb = ntyped(HOOK_B[0], HOOK_B[1], HOOK_B[2], t)
    alert = t >= HOOK_ALERT
    segs = [(HOOK_A[0][:na], (.9, .92, .96)), (HOOK_B[0][:nb], RED if alert else (.9, .92, .96))]
    toks, (cx, cl_) = layout(segs, 'reg', 42, w - 100)
    lh = 66; y0 = by + 86
    for (tx, line, part, col, tw) in toks:
        blit(ctx, text(part, 'reg', 42, col), bx + tx, y0 + line * lh, 1, 1, (0, 0))
        if alert and col == RED:
            ctx.save(); ctx.set_source_rgba(*RED, .9); ctx.set_line_width(2.2)
            yy = y0 + line * lh + 60; ctx.move_to(bx + tx, yy)
            xx = bx + tx
            while xx < bx + tx + tw: xx += 6; ctx.line_to(xx, yy + (3 if int((xx - bx) / 6) % 2 else -3))
            ctx.stroke(); ctx.restore()
    if (t * 2) % 1 < 0.6 or (HOOK_A[1] < t < HOOK_B[2] + .2):
        ctx.rectangle(bx + cx + 3, y0 + cl_ * lh + 10, 3, 50); ctx.set_source_rgba(.4, .7, 1, 1); ctx.fill()
    ctx.pop_group_to_source(); ctx.paint_with_alpha(a)
    ctx.restore()
    # headline
    if t > 6.0:
        k = eo(p(t, 6.0, .6))
        s = text('Sound familiar?', 'disp', 92)
        blit(ctx, s, W / 2, 925 + 40 * (1 - k), k)
    vignette(ctx)

def x_icon(ctx, cx, cy, r, a):
    ctx.arc(cx, cy, r, 0, 2 * PI); ctx.set_source_rgba(*RED, a); ctx.fill()
    ctx.set_source_rgba(1, 1, 1, a); ctx.set_line_width(4); ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    d = r * .4
    ctx.move_to(cx - d, cy - d); ctx.line_to(cx + d, cy + d); ctx.move_to(cx + d, cy - d); ctx.line_to(cx - d, cy + d); ctx.stroke()

def scene_problem(ctx, t):
    lt = t - 8.0
    z = 1.04 + 0.08 * (lt / 10)
    draw_cover(ctx, A['photo'], z, 0.56, 0.45)
    kb = eio(p(t, PROB_KEY, .8))
    if kb > 0: draw_cover(ctx, A['photo_blur'], z, 0.56, 0.45, kb)
    ctx.rectangle(0, 0, W, H)
    ctx.set_source(lin(0, 0, W, 0, [(0, (0.02, 0.03, 0.06, .92)), (.45, (0.02, 0.03, 0.06, .6)), (.75, (0, 0, 0, 0))])); ctx.fill()
    if kb > 0: ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(0.02, 0.03, 0.06, .55 * kb); ctx.fill()
    out = 1 - eio(p(t, PROB_KEY - .1, .5))
    if out > 0:
        k0 = eo(p(t, 8.25, .5))
        blit(ctx, text('THE PROBLEM', 'bold', 26, RED, track=8), 120, 250, k0 * out, 1, (0, .5))
        for i, (lab, tc) in enumerate(PROB_CHIPS):
            k = eo(p(t, tc, .5))
            if k <= 0: continue
            dx = 0
            if i == 0 and tc + .35 < t < tc + .85:
                kk = (t - tc - .35) / .5; dx = math.sin(kk * 36) * 12 * (1 - kk)
            y = 360 + i * 130
            w = pill(ctx, 120 - 60 * (1 - k) + dx + 0, y, '      ' + lab, 'bold', 46, bg=(.06, .07, .1, .78), border=(1, .4, .4, .35),
                     alpha=k * out, h=96, padx=30)
            x_icon(ctx, 120 - 60 * (1 - k) + dx + 58, y, 22, k * out)
    if t >= PROB_KEY:
        k = eback(p(t, PROB_KEY, .6), 1.3)
        pr = 0.0; x = t - (PROB_KEY + .25)
        if -0.05 <= x < 0: pr = (x + .05) / .05
        elif 0 <= x < .12: pr = 1
        elif .12 <= x < .25: pr = 1 - (x - .12) / .13
        ka = eo(p(t, PROB_KEY, .4))
        ctx.save(); ctx.translate(W / 2, 410); ctx.scale(lerp(.6, 1.35, k), lerp(.6, 1.35, k)); ctx.translate(-W / 2, -410)
        draw_key(ctx, W / 2 - 190, 410 - 95, 380, 190, pr, 0, ka)
        ctx.restore()
        # question mark badge
        kq = eback(p(t, PROB_KEY + .45, .4))
        if kq > 0:
            ctx.save(); ctx.translate(W / 2 + 262, 290); ctx.scale(kq, kq)
            ctx.arc(0, 0, 34, 0, 2 * PI); ctx.set_source_rgb(*RED); ctx.fill()
            blit(ctx, text('?', 'disp', 48), 0, 0)
            ctx.restore()
        k1 = eo(p(t, 13.5, .5)); k2 = eo(p(t, 14.35, .5))
        blit(ctx, text('One tiny key.', 'disp', 96), W / 2, 700 + 30 * (1 - k1), k1)
        blit(ctx, text('Zero visibility.', 'disp', 96, grad=((1, .45, .45), (1, .62, .3))), W / 2, 815 + 30 * (1 - k2), k2)
    # pre-reveal intensify
    if t > 17.2:
        k = p(t, 17.2, .8)
        ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(1, 1, 1, .5 * k ** 3); ctx.fill()
    vignette(ctx)

def scene_reveal(ctx, t):
    lt = t - 18.0
    dark_bg(ctx, t, 1.3)
    z = 1 + 0.035 * eio(p(t, 18, 6))
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
    cx, cy = W / 2, 400
    # rays
    ctx.save(); ctx.translate(cx, cy); ctx.rotate(lt * 0.08)
    ra = .10 * eo(p(t, 18, .5))
    for i in range(14):
        ctx.save(); ctx.rotate(i * 2 * PI / 14)
        g = cairo.LinearGradient(0, 0, 1100, 0); g.add_color_stop_rgba(0, *ACC1, ra); g.add_color_stop_rgba(1, *ACC1, 0)
        ctx.move_to(0, 0); ctx.line_to(1100, -70); ctx.line_to(1100, 70); ctx.close_path(); ctx.set_source(g); ctx.fill()
        ctx.restore()
    ctx.restore()
    # ring
    for d, col in ((0, ACC1), (.18, (1, 1, 1))):
        k = p(t, 18.0 + d, 1.1)
        if 0 < k < 1:
            ctx.arc(cx, cy, 120 + 800 * eo(k), 0, 2 * PI); ctx.set_source_rgba(*col, .5 * (1 - k)); ctx.set_line_width(3 + 6 * (1 - k)); ctx.stroke()
    k = eback(p(t, 18.05, .75), 1.6)
    if k > 0:
        ctx.save(); ctx.translate(cx, cy); ctx.scale(max(0.01, k), max(0.01, k)); ctx.rotate((1 - eo(p(t, 18.05, .75))) * -0.25)
        draw_appicon(ctx, 0, 0, 250, 1, .9)
        ctx.restore()
    ki = eo(p(t, 18.85, .5))
    blit(ctx, text('INTRODUCING', 'bold', 26, (.6, .75, 1), track=12), W / 2, 600, ki)
    kt = eio(p(t, 19.2, .8))
    if kt > 0:
        s1 = text('AMS ', 'disp', 116, grad=(ACC1, (.55, .82, 1)))
        s2 = text('Caps Lock OSD', 'disp', 116)
        tw = s1[1] + s2[1] - 8; x0 = W / 2 - tw / 2
        ctx.save(); ctx.rectangle(x0 - 20, 600, (tw + 40) * kt, 200); ctx.clip()
        blit(ctx, s1, x0, 700 + 20 * (1 - kt), 1, 1, (0, .5)); blit(ctx, s2, x0 + s1[1] - 8, 700 + 20 * (1 - kt), 1, 1, (0, .5))
        ctx.restore()
    ks = eo(p(t, 20.4, .6))
    blit(ctx, text('The Caps Lock indicator Windows forgot.', 'med', 38, (.72, .76, .85)), W / 2, 805 + 20 * (1 - ks), ks)
    ctx.restore()
    vignette(ctx)
    fl = 1 - eo(p(t, 18.0, .45))
    if fl > 0: ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(1, 1, 1, fl * .9); ctx.fill()

def caps_state(t, presses):
    st = False
    for tp, on in presses:
        if t >= tp: st = on
    return st

def osd_anim(t, presses, hold=OSD_HOLD, last_hold=None):
    last = None
    for i, (tp, on) in enumerate(presses):
        if t >= tp: last = (i, tp, on)
    if not last: return None
    i, tp, on = last; dt = t - tp
    hd = last_hold if (last_hold and i == len(presses) - 1) else hold
    if dt < OSD_FADE_IN: e = eo(dt / OSD_FADE_IN)
    elif dt < OSD_FADE_IN + hd: e = 1.0
    else: e = eio(1 - (dt - OSD_FADE_IN - hd) / OSD_FADE_OUT)
    return on, e

def key_press(t, presses):
    best = 0
    for tp, _ in presses:
        x = t - tp
        if -0.05 <= x < 0: v = (x + .05) / .05
        elif 0 <= x < .12: v = 1
        elif .12 <= x < .25: v = 1 - (x - .12) / .13
        else: v = 0
        best = max(best, v)
    return best

def tray_icon(ctx, cx, cy, on, size=30):
    rr(ctx, cx - size / 2, cy - size / 2, size, size, size * .22)
    if on: ctx.set_source(lin(0, cy - size / 2, 0, cy + size / 2, [(0, ACC1), (1, ACC2)]))
    else: ctx.set_source_rgb(.28, .29, .32)
    ctx.fill()
    gw, gh = size * .55, size * .62
    glyph(ctx, cx - gw / 2, cy - gh / 2, gw, gh, 1); ctx.set_source_rgba(1, 1, 1, 1 if on else .85); ctx.fill()

def taskbar(ctx, t, on):
    ty = H - 72
    ctx.rectangle(0, ty, W, 72); ctx.set_source_rgba(.07, .08, .11, .88); ctx.fill()
    ctx.rectangle(0, ty, W, 1); ctx.set_source_rgba(1, 1, 1, .1); ctx.fill()
    icons = [W / 2 - 150, W / 2 - 90, W / 2 - 30, W / 2 + 30, W / 2 + 90, W / 2 + 150]
    cy = ty + 36
    # start
    x = icons[0]
    for dx, dy in ((-10, -10), (1, -10), (-10, 1), (1, 1)):
        ctx.rectangle(x + dx, cy + dy, 9, 9); ctx.set_source_rgb(.2, .6, 1); ctx.fill()
    x = icons[1]; ctx.arc(x - 2, cy - 2, 8, 0, 2 * PI); ctx.set_source_rgba(1, 1, 1, .85); ctx.set_line_width(2.2); ctx.stroke()
    ctx.move_to(x + 4, cy + 4); ctx.line_to(x + 10, cy + 10); ctx.stroke()
    rr(ctx, icons[2] - 13, cy - 10, 26, 20, 3); ctx.set_source_rgb(1, .78, .25); ctx.fill()
    ctx.arc(icons[3], cy, 12, 0, 2 * PI); ctx.set_source(lin(0, cy - 12, 0, cy + 12, [(0, (.3, .8, 1)), (1, (.1, .4, .9))])); ctx.fill()
    rr(ctx, icons[4] - 10, cy - 13, 20, 26, 3); ctx.set_source_rgb(.85, .9, 1); ctx.fill()
    for k in range(3): ctx.rectangle(icons[4] - 6, cy - 7 + k * 6, 12, 2); ctx.set_source_rgb(.3, .4, .6); ctx.fill()
    rr(ctx, icons[4] - 26, cy - 26, 52, 52, 8); ctx.set_source_rgba(1, 1, 1, .08); ctx.fill()
    rr(ctx, icons[4] - 9, ty + 66, 18, 3, 1.5); ctx.set_source_rgb(.3, .65, 1); ctx.fill()
    rr(ctx, icons[5] - 12, cy - 12, 24, 24, 6); ctx.set_source_rgb(.55, .4, 1); ctx.fill()
    # tray
    tray_icon(ctx, 1640, cy, on, 30)
    blit(ctx, text('ENG', 'med', 17, (.9, .92, .96)), 1712, cy, 1)
    blit(ctx, text('10:24 AM', 'med', 17, (.9, .92, .96)), 1820, cy - 11, 1)
    blit(ctx, text('16/10/2026', 'med', 17, (.9, .92, .96)), 1820, cy + 12, 1)

def callout(ctx, px, py, lx, ly, label, k, anchor=0.0):
    if k <= 0: return
    ctx.save()
    ctx.arc(px, py, 7 * k, 0, 2 * PI); ctx.set_source_rgba(*ACC1, k); ctx.fill()
    glow(ctx, px, py, 26, ACC1, .5 * k)
    ex, ey = lerp(px, lx, eo(k)), lerp(py, ly, eo(k))
    ctx.move_to(px, py); ctx.line_to(ex, ey); ctx.set_source_rgba(*ACC1, .9 * k); ctx.set_line_width(2.5); ctx.stroke()
    ctx.restore()
    kk = eo(p(k, .4, .6))
    pill(ctx, lx, ly, label, 'semi', 28, bg=(.06, .08, .13, .9), border=(*ACC1, .6), alpha=kk, h=62, anchor=anchor)

def scene_demo(ctx, t):
    on_now = caps_state(t, DEMO_PRESSES)
    zk = eio(p(t, 33.3, .9)); z = 1 + 0.75 * zk
    osd_s = 1.35; osd_cx = W / 2; osd_h = 198 * osd_s
    osd_cy = H - 72 - 70 * osd_s - osd_h / 2
    fx, fy = W / 2, lerp(H / 2, osd_cy - 15, zk)
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-fx, -fy)
    draw_cover(ctx, A['wall'], 1.02 + 0.02 * p(t, 24, 12), 0.5, 0.5)
    # notepad
    x, y, w, h = 300, 110, 1320, 600
    draw_window(ctx, x, y, w, h, 'meeting-notes.txt  -  Notepad')
    for i, m in enumerate(['File', 'Edit', 'View']):
        blit(ctx, text(m, 'reg', 20, (.75, .78, .85)), x + 26 + i * 76, y + 78, 1, 1, (0, .5))
    ctx.rectangle(x, y + 102, w, 1); ctx.set_source_rgba(1, 1, 1, .08); ctx.fill()
    tx0, ty0 = x + 40, y + 130
    blit(ctx, text('Project kickoff \u2014 meeting notes', 'semi', 34, (1, 1, 1)), tx0, ty0, 1, 1, (0, 0))
    segs = []
    for txt, a_, b_ in DEMO_TYPING:
        segs.append((txt[:ntyped(txt, a_, b_, t)], (.88, .9, .95)))
    toks, (cx, cl_) = layout(segs, 'reg', 32, w - 80)
    lh = 54; y1 = ty0 + 72
    for (tx, line, part, col, tw) in toks:
        blit(ctx, text(part, 'reg', 32, col), tx0 + tx, y1 + line * lh, 1, 1, (0, 0))
    if (t * 2) % 1 < .6:
        ctx.rectangle(tx0 + cx + 3, y1 + cl_ * lh + 8, 2.5, 38); ctx.set_source_rgba(.85, .9, 1, 1); ctx.fill()
    taskbar(ctx, t, on_now)
    st = osd_anim(t, DEMO_PRESSES, OSD_HOLD, 99)
    if st:
        on, e = st
        draw_osd(ctx, osd_cx, osd_cy + (1 - e) * 14 * osd_s, on, osd_s, e, .94 + .06 * e)
    ctx.restore()
    # overlays (screen space)
    hide = 1 - eo(p(t, 33.1, .3))
    kA = p(t, 25.7, .6) * (1 - p(t, 28.0, .3)) * hide
    callout(ctx, osd_cx + 125, osd_cy - 40, 1240, osd_cy - 150, 'Instant ON / OFF feedback', kA)
    kB = p(t, 30.9, .6) * (1 - p(t, 32.8, .3)) * hide
    callout(ctx, osd_cx - 125, osd_cy - 40, 690, osd_cy - 150, 'Fades away on its own', kB, anchor=1.0)
    kC = p(t, 29.8, .6) * (1 - p(t, 32.8, .3)) * hide
    callout(ctx, 1640, H - 60, 1640, 880, 'Live status in your tray', kC, anchor=0.5)
    # keycap overlay
    ka = eo(p(t, 24.2, .5)) * (1 - p(t, 35.7, .3))
    if ka > 0:
        draw_key(ctx, 70, 760 + 40 * (1 - ka), 320, 160, key_press(t, DEMO_PRESSES), 1.0 if on_now else 0.0, ka)
    # caption during close-up
    kc = eo(p(t, 33.9, .6))
    if kc > 0:
        blit(ctx, text('Always know. Instantly.', 'disp', 72), W / 2, 150 + 30 * (1 - kc), kc)
    vignette(ctx, .7)

def ic_power(ctx, s):
    ctx.arc(0, 2, s * .42, -PI / 2 + .6, 1.5 * PI - .6); ctx.stroke(); ctx.move_to(0, -s * .5); ctx.line_to(0, -s * .02); ctx.stroke()
def ic_cursor(ctx, s):
    pts = [(-.3, -.5), (.35, .1), (.02, .12), (.2, .48), (.06, .54), (-.12, .18), (-.3, .36)]
    ctx.move_to(pts[0][0] * s, pts[0][1] * s)
    for u, v in pts[1:]: ctx.line_to(u * s, v * s)
    ctx.close_path(); ctx.stroke()
def ic_monitors(ctx, s):
    rr(ctx, -s * .55, -s * .38, s * .62, s * .44, 4); ctx.stroke()
    rr(ctx, -s * .02, -s * .22, s * .58, s * .42, 4); ctx.stroke()
    ctx.move_to(s * .27, s * .2); ctx.line_to(s * .27, s * .38); ctx.move_to(s * .1, s * .4); ctx.line_to(s * .44, s * .4); ctx.stroke()
def ic_spark(ctx, s):
    for (cx, cy, r) in ((-.08, .04, .42), (.34, -.3, .18)):
        r *= s; cx *= s; cy *= s
        ctx.move_to(cx, cy - r); ctx.curve_to(cx + r * .12, cy - r * .12, cx + r * .12, cy - r * .12, cx + r, cy)
        ctx.curve_to(cx + r * .12, cy + r * .12, cx + r * .12, cy + r * .12, cx, cy + r)
        ctx.curve_to(cx - r * .12, cy + r * .12, cx - r * .12, cy + r * .12, cx - r, cy)
        ctx.curve_to(cx - r * .12, cy - r * .12, cx - r * .12, cy - r * .12, cx, cy - r); ctx.close_path(); ctx.stroke()
def ic_bolt(ctx, s):
    pts = [(.08, -.55), (-.32, .06), (-.02, .06), (-.1, .55), (.32, -.08), (.02, -.08)]
    ctx.move_to(pts[0][0] * s, pts[0][1] * s)
    for u, v in pts[1:]: ctx.line_to(u * s, v * s)
    ctx.close_path(); ctx.stroke()
def ic_tray(ctx, s):
    rr(ctx, -s * .55, s * .02, s * 1.1, s * .36, 5); ctx.stroke()
    rr(ctx, s * .18, s * .09, s * .22, s * .22, 3); ctx.fill()
    ctx.move_to(-s * .2, -s * .12); ctx.line_to(0, -s * .45); ctx.line_to(s * .2, -s * .12); ctx.stroke()

FEATURES = [
    (ic_power, 'Starts with Windows', 'Launches automatically at boot'),
    (ic_cursor, 'Never steals focus', 'Click-through. Zero interruptions.'),
    (ic_monitors, 'Every monitor', 'Appears right where your mouse is'),
    (ic_spark, 'Sharp on any display', 'DPI-aware and pixel-perfect'),
    (ic_bolt, 'Ultra lightweight', 'Under 300 KB \u00b7 near-zero CPU'),
    (ic_tray, 'Status in the tray', 'Blue = ON  \u00b7  Grey = OFF'),
]

def scene_features(ctx, t):
    dark_bg(ctx, t)
    z = 1 + 0.03 * p(t, 36, 14)
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2)
    k0 = eo(p(t, 36.15, .6))
    blit(ctx, text('FEATURES', 'bold', 26, (.55, .75, 1), track=10), W / 2, 110, k0)
    blit(ctx, text('Built to stay out of your way', 'disp', 72), W / 2, 185 + 25 * (1 - k0), k0)
    cw, ch, gap = 490, 260, 36
    x0 = (W - (3 * cw + 2 * gap)) / 2; y0 = 290
    for i, (ic, title, sub) in enumerate(FEATURES):
        tc = FEATURE_TIMES[i]
        k = eback(p(t, tc, .6), 1.2); ka = eo(p(t, tc, .45))
        if ka <= 0: continue
        col, row = i % 3, i // 3
        x, y = x0 + col * (cw + gap), y0 + row * (ch + gap)
        act = p(t, tc, .3) * (1 - p(t, tc + 1.9, .6))
        ctx.save(); ctx.translate(x + cw / 2, y + ch / 2 + 40 * (1 - ka)); sc = lerp(.9, 1, k); ctx.scale(sc, sc); ctx.translate(-cw / 2, -ch / 2)
        ctx.push_group()
        blit(ctx, shadow(cw, ch, 26, 22, .55), cw / 2, ch / 2 + 12)
        if act > 0: glow(ctx, cw / 2, ch / 2, cw * .75, ACC1, .22 * act)
        rr(ctx, 0, 0, cw, ch, 26)
        ctx.set_source(lin(0, 0, 0, ch, [(0, (.12, .13, .17, .92)), (1, (.08, .085, .11, .92))])); ctx.fill_preserve()
        ctx.set_source_rgba(lerp(1, ACC1[0], act), lerp(1, ACC1[1], act), lerp(1, ACC1[2], act), .12 + .6 * act); ctx.set_line_width(1.5 + act); ctx.stroke()
        icx, icy = 40 + 38, 40 + 38
        glow(ctx, icx, icy, 70, ACC1, .25 + .25 * act)
        ctx.arc(icx, icy, 38, 0, 2 * PI); ctx.set_source(lin(0, icy - 38, 0, icy + 38, [(0, ACC1), (1, ACC2)])); ctx.fill()
        ctx.save(); ctx.translate(icx, icy); ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(3.2)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND); ic(ctx, 36); ctx.restore()
        blit(ctx, text(title, 'bold', 36), 40, 165, 1, 1, (0, .5))
        blit(ctx, text(sub, 'reg', 25, (.66, .7, .78)), 40, 212, 1, 1, (0, .5))
        ctx.pop_group_to_source(); ctx.paint_with_alpha(ka); ctx.restore()
    ctx.restore()
    vignette(ctx)

def check_icon(ctx, cx, cy, r, k, num):
    if k <= 0:
        ctx.arc(cx, cy, r, 0, 2 * PI); ctx.set_source_rgba(1, 1, 1, .08); ctx.fill_preserve()
        ctx.set_source_rgba(1, 1, 1, .3); ctx.set_line_width(2); ctx.stroke()
        blit(ctx, text(str(num), 'bold', 26, (.85, .88, .95)), cx, cy)
        return
    s = eback(k, 2)
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s)
    glow(ctx, 0, 0, r * 2, ACC1, .4)
    ctx.arc(0, 0, r, 0, 2 * PI); ctx.set_source(lin(0, -r, 0, r, [(0, ACC1), (1, ACC2)])); ctx.fill()
    ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(4.5); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    ctx.move_to(-r * .4, 0); ctx.line_to(-r * .1, r * .3); ctx.line_to(r * .42, -r * .3); ctx.stroke()
    ctx.restore()

def scene_install(ctx, t):
    dark_bg(ctx, t)
    k0 = eo(p(t, 50.1, .6))
    blit(ctx, text('INSTALL', 'bold', 26, (.55, .75, 1), track=10), 150, 230, k0, 1, (0, .5))
    blit(ctx, text('Up and running', 'disp', 84), 150, 310 + 20 * (1 - k0), k0, 1, (0, .5))
    blit(ctx, text('in seconds.', 'disp', 84, grad=(ACC1, (.55, .85, 1))), 150, 405 + 20 * (1 - k0), k0, 1, (0, .5))
    steps = ['Download the installer', 'Click Install \u2014 no admin needed', 'Done. Starts with every boot.']
    for i, s in enumerate(steps):
        ka = eo(p(t, 50.4 + i * .2, .5)); y = 545 + i * 92
        if ka <= 0: continue
        ctx.save(); ctx.push_group()
        check_icon(ctx, 178 - 30 * (1 - ka), y, 26, p(t, INSTALL_CHECKS[i], .35), i + 1)
        blit(ctx, text(s, 'semi', 34, (.92, .94, .98)), 228 - 30 * (1 - ka), y, 1, 1, (0, .5))
        ctx.pop_group_to_source(); ctx.paint_with_alpha(ka); ctx.restore()
    bx = 150
    for i, b in enumerate(['No admin rights', 'Auto-start', '~300 KB']):
        kb = eo(p(t, 51.9 + i * .3, .4))
        if kb > 0:
            bx += pill(ctx, bx, 880 + 20 * (1 - kb), b, 'semi', 26, bg=(.08, .12, .2, .9), border=(*ACC1, .5), alpha=kb, h=56, padx=24, dot=ACC1) + 18
    # installer mock
    kw = eo(p(t, 50.15, .7))
    x, y, w, h = 1010, 250 + 60 * (1 - kw), 760, 540
    ctx.save(); ctx.push_group()
    draw_window(ctx, x, y, w, h, 'AMS Caps Lock OSD Setup  -  by AMS', light=True)
    ctx.rectangle(x, y + 50, w, 104); ctx.set_source_rgb(1, 1, 1); ctx.fill()
    ctx.rectangle(x, y + 154, w, 1); ctx.set_source_rgba(0, 0, 0, .12); ctx.fill()
    done = t >= 53.4
    blit(ctx, text('Installation Complete' if done else 'Installing', 'bold', 26, (.1, .1, .15)), x + 30, y + 88, 1, 1, (0, .5))
    blit(ctx, text('Setup was completed successfully.' if done else 'Please wait while AMS Caps Lock OSD is being installed.', 'reg', 19, (.35, .37, .45)),
         x + 30, y + 122, 1, 1, (0, .5))
    draw_appicon(ctx, x + w - 70, y + 102, 60, 1, 0)
    blit(ctx, text('AMS', 'disp', 26, (.04, .37, .84)), x + w - 120, y + 102, 1, 1, (1, .5))
    pk = eio(p(t, 50.5, 2.8))
    blit(ctx, text('Extract: CapsLockOSD.exe... 100%' if pk < 1 else 'Completed', 'reg', 20, (.2, .22, .3)), x + 40, y + 215, 1, 1, (0, .5))
    rr(ctx, x + 40, y + 250, w - 80, 26, 6); ctx.set_source_rgb(.88, .89, .92); ctx.fill()
    if pk > 0:
        rr(ctx, x + 40, y + 250, (w - 80) * pk, 26, 6); ctx.set_source(lin(x, 0, x + w, 0, [(0, ACC1), (1, ACC2)])); ctx.fill()
    lines = ['Output folder: %LOCALAPPDATA%\\Programs\\AMS', 'Extract: CapsLockOSD.exe', 'Create shortcut: AMS Caps Lock OSD',
             'Registering: Start with Windows', 'Completed']
    for i, l in enumerate(lines):
        if pk >= (i + 1) / len(lines) - .05:
            blit(ctx, text(l, 'reg', 18, (.3, .32, .4)), x + 40, y + 310 + i * 30, 1, 1, (0, .5))
    ctx.rectangle(x, y + h - 80, w, 1); ctx.set_source_rgba(0, 0, 0, .1); ctx.fill()
    fin = eo(p(t, 53.6, .3))
    for i, (lab, en) in enumerate([('< Back', False), ('Finish' if done else 'Next >', done), ('Cancel', False)]):
        bx2 = x + w - 3 * 130 - 10 + i * 130; by2 = y + h - 40
        rr(ctx, bx2, by2 - 20, 116, 40, 6)
        if en and fin > 0: ctx.set_source(lin(0, by2 - 20, 0, by2 + 20, [(0, ACC1), (1, ACC2)]))
        else: ctx.set_source_rgb(.92, .93, .95)
        ctx.fill_preserve(); ctx.set_source_rgba(0, 0, 0, .15); ctx.set_line_width(1); ctx.stroke()
        blit(ctx, text(lab, 'semi', 19, (1, 1, 1) if (en and fin > 0) else (.55, .57, .63)), bx2 + 58, by2)
    ctx.pop_group_to_source(); ctx.paint_with_alpha(kw); ctx.restore()
    vignette(ctx)

def pointer(ctx, x, y, sc=1.0):
    pts = [(0, 0), (0, 34), (8, 26), (14, 40), (20, 37), (14, 24), (25, 24)]
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc)
    ctx.move_to(*pts[0])
    for q in pts[1:]: ctx.line_to(*q)
    ctx.close_path(); ctx.set_source_rgb(1, 1, 1); ctx.fill_preserve(); ctx.set_source_rgb(0, 0, 0); ctx.set_line_width(2); ctx.stroke()
    ctx.restore()

def scene_cta(ctx, t):
    draw_cover(ctx, A['desk'], 1.05 + 0.05 * p(t, 56, 9), .55, .5)
    ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(.02, .03, .06, .55); ctx.fill()
    s, w, h = A['blobs']
    ctx.save(); ctx.translate(-200 + 60 * math.sin(t * .3), -200); ctx.set_source_surface(s, 0, 0); ctx.paint_with_alpha(.8); ctx.restore()
    k = eback(p(t, 56.15, .7), 1.4)
    if k > 0:
        ctx.save(); ctx.translate(W / 2, 280); ctx.scale(max(.01, k), max(.01, k)); draw_appicon(ctx, 0, 0, 190, 1, .8); ctx.restore()
    kt = eio(p(t, 56.5, .8))
    if kt > 0:
        s1 = text('AMS ', 'disp', 104, grad=(ACC1, (.55, .82, 1))); s2 = text('Caps Lock OSD', 'disp', 104)
        tw = s1[1] + s2[1] - 8; x0 = W / 2 - tw / 2
        ctx.save(); ctx.rectangle(x0 - 20, 380, (tw + 40) * kt, 180); ctx.clip()
        blit(ctx, s1, x0, 470, 1, 1, (0, .5)); blit(ctx, s2, x0 + s1[1] - 8, 470, 1, 1, (0, .5)); ctx.restore()
    kg = eo(p(t, 57.9, .6))
    if kg > 0:
        a1 = text('Know your caps. ', 'semi', 48, (.92, .94, .98)); a2 = text('Every time.', 'semi', 48, grad=(ACC1, (.55, .85, 1)))
        tw = a1[1] + a2[1] - 8; x0 = W / 2 - tw / 2
        blit(ctx, a1, x0, 568 + 20 * (1 - kg), kg, 1, (0, .5)); blit(ctx, a2, x0 + a1[1] - 8, 568 + 20 * (1 - kg), kg, 1, (0, .5))
    # buttons
    bw1, bw2, bh, gap = 430, 520, 96, 40
    bx = W / 2 - (bw1 + bw2 + gap) / 2; by = 700
    kb1 = eback(p(t, 59.2, .5)); kb2 = eback(p(t, 59.5, .5))
    click = t - 61.15
    pulse = 1 - .05 * math.sin(PI * cl(click / .25)) if 0 <= click < .25 else 1
    if kb1 > 0:
        ctx.save(); ctx.translate(bx + bw1 / 2, by); ctx.scale(kb1, kb1); ctx.push_group()
        glow(ctx, 0, 0, 300, ACC1, .35)
        rr(ctx, -bw1 / 2, -bh / 2, bw1, bh, bh / 2); ctx.set_source(lin(0, -bh / 2, 0, bh / 2, [(0, ACC1), (1, ACC2)])); ctx.fill()
        ctx.set_source_rgb(1, 1, 1); ctx.set_line_width(4); ctx.set_line_cap(cairo.LINE_CAP_ROUND); ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ix = -bw1 / 2 + 62
        ctx.move_to(ix, -18); ctx.line_to(ix, 8); ctx.move_to(ix - 11, -3); ctx.line_to(ix, 8); ctx.line_to(ix + 11, -3); ctx.stroke()
        ctx.move_to(ix - 15, 18); ctx.line_to(ix + 15, 18); ctx.stroke()
        blit(ctx, text('Download now', 'bold', 36), 22, 0)
        ctx.pop_group_to_source(); ctx.paint(); ctx.restore()
    if kb2 > 0:
        cx2 = bx + bw1 + gap + bw2 / 2
        ctx.save(); ctx.translate(cx2, by); ctx.scale(kb2 * pulse, kb2 * pulse); ctx.push_group()
        glow(ctx, 0, 0, 320, (1, .1, .1), .3)
        rr(ctx, -bw2 / 2, -bh / 2, bw2, bh, bh / 2); ctx.set_source(lin(0, -bh / 2, 0, bh / 2, [(0, (1, .15, .15)), (1, (.8, 0, 0))])); ctx.fill()
        lx = -bw2 / 2 + 46
        rr(ctx, lx, -21, 60, 42, 12); ctx.set_source_rgb(1, 1, 1); ctx.fill()
        ctx.move_to(lx + 24, -11); ctx.line_to(lx + 24, 11); ctx.line_to(lx + 42, 0); ctx.close_path(); ctx.set_source_rgb(.85, 0, 0); ctx.fill()
        blit(ctx, text('Subscribe to AMS', 'bold', 36), 38, 0)
        ctx.pop_group_to_source(); ctx.paint(); ctx.restore()
        if 0 <= click < .7:
            kk = click / .7
            ctx.arc(cx2 + 120, by + 10, 30 + 140 * eo(kk), 0, 2 * PI); ctx.set_source_rgba(1, 1, 1, .45 * (1 - kk)); ctx.set_line_width(3); ctx.stroke()
    ku = eo(p(t, 60.0, .6))
    blit(ctx, text('youtube.com/channel/UCW5b5zJ1MW35P1x9--ExMvg', 'med', 26, (.7, .74, .82)), W / 2, 815, ku)
    kf = eo(p(t, 60.4, .6))
    blit(ctx, text('For Windows 10 & 11   \u00b7   \u00a9 2026 AMS', 'med', 22, (.55, .58, .66), track=1), W / 2, 1010, kf)
    # pointer
    if t > 60.3:
        km = eio(p(t, 60.3, .8))
        cx2 = bx + bw1 + gap + bw2 / 2
        px, py = lerp(1500, cx2 + 120, km), lerp(1000, by + 10, km)
        pointer(ctx, px, py, .9 if 0 <= click < .15 else 1)
    vignette(ctx, .8)

SCENE_FN = {'hook': scene_hook, 'problem': scene_problem, 'reveal': scene_reveal, 'demo': scene_demo,
            'features': scene_features, 'install': scene_install, 'cta': scene_cta}
HARD_CUTS = {18.0}
XF = 0.5

def watermark(ctx, t):
    a = eo(p(t, 24.3, .6)) * (1 - p(t, 55.7, .3)) * .55
    if a > 0:
        ctx.save(); ctx.translate(W - 70, 62)
        tray_icon(ctx, -78, 0, True, 26)
        ctx.restore()
        blit(ctx, text('AMS', 'disp', 30), W - 70, 62, a * 1.4, 1, (.5, .5))

def render(t):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    ctx.set_source_rgb(0, 0, 0); ctx.paint()
    active = []
    for name, a, b in SCENES:
        pre = 0 if a in HARD_CUTS or a == 0 else XF / 2
        post = 0 if b in HARD_CUTS or b >= DURATION else XF / 2
        if a - pre <= t < b + post: active.append((name, a, b))
    for idx, (name, a, b) in enumerate(active):
        if idx == 0:
            if len(active) > 1:
                k = eio((t - (b - XF / 2)) / XF)
                ctx.save(); ctx.translate(W / 2, H / 2); sc = 1 + .05 * k; ctx.scale(sc, sc); ctx.translate(-W / 2, -H / 2)
                SCENE_FN[name](ctx, t); ctx.restore()
            else:
                SCENE_FN[name](ctx, t)
        else:
            k = eio((t - (a - XF / 2)) / XF)
            ctx.save(); ctx.push_group()
            ctx.translate(W / 2, H / 2); sc = .96 + .04 * k; ctx.scale(sc, sc); ctx.translate(-W / 2, -H / 2)
            SCENE_FN[name](ctx, t)
            ctx.pop_group_to_source(); ctx.paint_with_alpha(k); ctx.restore()
    watermark(ctx, t)
    # global fades
    fi = 1 - p(t, 0, .5); fo = p(t, DURATION - .8, .8)
    a = max(fi, fo)
    if a > 0: ctx.rectangle(0, 0, W, H); ctx.set_source_rgba(0, 0, 0, a); ctx.fill()
    return surf

def frame_bytes(surf):
    return bytes(surf.get_data())

def encode_chunk(args):
    i0, i1, out = args
    cmd = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgra', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-threads', '1', out]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        pr.stdin.write(frame_bytes(render(i / FPS)))
        if i % 60 == 0: print(f'  frame {i}', flush=True)
    pr.stdin.close(); pr.wait()
    return out

if __name__ == '__main__':
    init_assets()
    mode = sys.argv[1]
    if mode == 'still':
        os.makedirs(os.path.join(HERE, 'stills'), exist_ok=True)
        for ts in sys.argv[2:]:
            render(float(ts)).write_to_png(os.path.join(HERE, 'stills', f't{float(ts):05.1f}.png'))
            print('still', ts)
    elif mode == 'video':
        from multiprocessing import Pool
        nf = int(DURATION * FPS)
        nw = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        os.makedirs('/tmp/chunks', exist_ok=True)
        bounds = [round(nf * k / nw) for k in range(nw + 1)]
        jobs = [(bounds[k], bounds[k + 1], f'/tmp/chunks/c{k}.mp4') for k in range(nw)]
        with Pool(nw) as pool: outs = pool.map(encode_chunk, jobs)
        with open('/tmp/chunks/list.txt', 'w') as f:
            for o in outs: f.write(f"file '{o}'\n")
        print('chunks done')
