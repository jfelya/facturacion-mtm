"""Generate crisp UI icons (flags + theme) as anti-aliased PNGs.

Run:  python assets/ui/make_icons.py
Outputs (in this folder): ve.png, us.png, sun.png, moon.png
Rendered at 4x and downsampled with LANCZOS so edges are smooth like the app icon.
"""
import math
import os
from PIL import Image, ImageChops, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SS = 6  # supersample factor


def _star_poly(cx, cy, r, points=5, rot=-90):
    pts = []
    for i in range(points * 2):
        rr = r if i % 2 == 0 else r * 0.42
        a = math.radians(rot + i * 180 / points)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _save(img, name, size):
    img = img.resize(size, Image.LANCZOS)
    img.save(os.path.join(HERE, name))
    print("wrote", name, size)


def _new(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


# ---------------- Venezuela ----------------
def venezuela(w, h):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    y1 = int(H * 0.5)          # yellow = top half
    y2 = int(H * 0.75)         # blue = quarter
    d.rectangle([0, 0, W, y1], fill=(247, 212, 23, 255))       # yellow
    d.rectangle([0, y1, W, y2], fill=(0, 51, 160, 255))        # blue
    d.rectangle([0, y2, W, H], fill=(207, 20, 43, 255))        # red
    # 8 white stars in a shallow arc on the blue band
    cx, cy = W / 2, y2 - (y2 - y1) * 0.12
    R = min(W * 0.30, (y2 - y1) * 1.15)
    r = max(2.0 * SS, (y2 - y1) * 0.16)
    for i in range(8):
        a = math.radians(205 + i * (130 / 7))
        sx = cx + R * math.cos(a)
        sy = cy + R * math.sin(a) * 0.55
        d.polygon(_star_poly(sx, sy, r), fill=(255, 255, 255, 255))
    _save(img, "ve.png", (w, h))


# ---------------- USA ----------------
def usa(w, h):
    img = _new(w, h)
    d = ImageDraw.Draw(img)
    W, H = w * SS, h * SS
    stripe = H / 13
    for i in range(13):
        col = (178, 34, 52, 255) if i % 2 == 0 else (255, 255, 255, 255)
        d.rectangle([0, i * stripe, W, (i + 1) * stripe], fill=col)
    cw, ch = W * 0.42, stripe * 7
    d.rectangle([0, 0, cw, ch], fill=(60, 59, 110, 255))
    cols, rows = 6, 4
    r = max(1.1 * SS, ch / (rows * 2) * 0.45)
    for row in range(rows):
        for col in range(cols):
            cx = cw * (col + 0.5 + (0.5 if row % 2 else 0.0)) / cols
            cy = ch * (row + 0.5) / rows
            d.polygon(_star_poly(cx, cy, r), fill=(255, 255, 255, 255))
    _save(img, "us.png", (w, h))


# ---------------- theme ----------------
def sun(s):
    img = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    C = s * SS / 2
    R = s * SS * 0.30
    d.ellipse([C - R, C - R, C + R, C + R], fill=(242, 193, 78, 255))
    for k in range(8):
        a = math.radians(k * 45)
        x1 = C + (R + s * SS * 0.10) * math.cos(a)
        y1 = C + (R + s * SS * 0.10) * math.sin(a)
        x2 = C + (R + s * SS * 0.30) * math.cos(a)
        y2 = C + (R + s * SS * 0.30) * math.sin(a)
        d.line([x1, y1, x2, y2], fill=(242, 193, 78, 255), width=max(1, int(s * SS * 0.10)))
    _save(img, "sun.png", (s, s))


def moon(s):
    img = Image.new("RGBA", (s * SS, s * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    C = s * SS / 2
    R = s * SS * 0.38
    d.ellipse([C - R, C - R, C + R, C + R], fill=(219, 228, 240, 255))
    mask = Image.new("L", (s * SS, s * SS), 255)
    md = ImageDraw.Draw(mask)
    off = R * 0.62
    md.ellipse([C - R + off, C - R - off * 0.30, C + R + off, C + R - off * 0.30], fill=0)
    img.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    _save(img, "moon.png", (s, s))


venezuela(64, 30)
usa(64, 30)
sun(30)
moon(30)
print("done")
