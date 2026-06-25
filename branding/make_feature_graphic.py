# -*- coding: utf-8 -*-
"""PayRails Google Play feature graphic (1024x500) generator (Pillow only).

Reuses the brand mark + palette from make_logo.py so the graphic matches the
app icon: cyan->mint double-chevron on a rail line, over a dark-teal gradient.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- palette (matches make_logo.py) ----
BG_TOP = (12, 60, 45)
BG_BOT = (5, 26, 19)
CYAN = (77, 182, 196)
MINT = (95, 224, 192)
WHITE = (240, 248, 247)

SS = 2  # supersample factor


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgradient(size, c_top, c_bot):
    w, h = size
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        col = lerp(c_top, c_bot, y / max(1, h - 1))
        for x in range(w):
            px[x, y] = col
    return img.convert("RGBA")


def diag_gradient(size, c1, c2):
    w, h = size
    base = Image.new("RGB", (w, h))
    px = base.load()
    for y in range(h):
        for x in range(w):
            t = (x / max(1, w - 1) + y / max(1, h - 1)) / 2
            px[x, y] = lerp(c1, c2, t)
    return base.convert("RGBA")


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def draw_mark(size, scale=1.0, stroke_color=(MINT, CYAN)):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)

    cx = size / 2
    cy = size * 0.42
    span = size * 0.40 * scale
    w = int(size * 0.085 * scale)
    h = size * 0.24 * scale

    def chevron(x_tip):
        x_back = x_tip - span * 0.55
        pts = [(x_back, cy - h), (x_tip, cy), (x_back, cy + h)]
        d.line(pts, fill=255, width=w, joint="curve")
        r = w / 2
        for (px_, py_) in pts:
            d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r], fill=255)

    off = span * 0.62
    chevron(cx - off * 0.15)
    chevron(cx + off * 0.85)

    rail_w = int(size * 0.055 * scale)
    rail_y = size * 0.74
    rx1, rx2 = cx - span * 1.0, cx + span * 1.1
    d.line([(rx1, rail_y), (rx2, rail_y)], fill=255, width=rail_w)
    rr = rail_w / 2
    for px_ in (rx1, rx2):
        d.ellipse([px_ - rr, rail_y - rr, px_ + rr, rail_y + rr], fill=255)

    grad = diag_gradient((size, size), stroke_color[0], stroke_color[1])
    img.paste(grad, (0, 0), mask)
    return img


def make_tile(px, rounded=True, mark_scale=1.0):
    s = px * SS
    bg = vgradient((s, s), BG_TOP, BG_BOT)
    sheen = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.ellipse([-s * 0.3, -s * 0.75, s * 1.3, s * 0.35], fill=(255, 255, 255, 16))
    bg = Image.alpha_composite(bg, sheen)
    mark = draw_mark(s, scale=mark_scale)
    bg = Image.alpha_composite(bg, mark)
    if rounded:
        m = rounded_mask((s, s), radius=int(s * 0.22))
        out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        out.paste(bg, (0, 0), m)
    else:
        out = bg
    return out.resize((px, px), Image.LANCZOS)


def load_font(names, size):
    for n in names:
        for p in (n, os.path.join("C:/Windows/Fonts", n)):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def make_feature_graphic(w=1024, h=500):
    s = SS
    W, H = w * s, h * s

    bg = vgradient((W, H), BG_TOP, BG_BOT)
    # diagonal sheen across the top-left
    sheen = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.ellipse([-W * 0.25, -H * 1.1, W * 1.0, H * 0.45], fill=(255, 255, 255, 14))
    bg = Image.alpha_composite(bg, sheen)

    # brand mark tile
    mk = int(H * 0.52)
    mark = make_tile(mk // s, rounded=True).resize((mk, mk), Image.LANCZOS)

    fbold = load_font(["segoeuib.ttf", "arialbd.ttf"], int(H * 0.21))
    ftag = load_font(["segoeui.ttf", "arial.ttf"], int(H * 0.05))

    d = ImageDraw.Draw(bg)
    pay_bb = d.textbbox((0, 0), "Pay", font=fbold)
    rails_bb = d.textbbox((0, 0), "Rails", font=fbold)
    pay_w = pay_bb[2] - pay_bb[0]
    word_h = max(pay_bb[3], rails_bb[3])
    word_w = pay_w + (rails_bb[2] - rails_bb[0])

    tag = "INSTANT PAYMENTS  ·  FEDNOW  ·  RTP"
    tag_bb = d.textbbox((0, 0), tag, font=ftag)
    tag_w = tag_bb[2] - tag_bb[0]
    tag_h = tag_bb[3] - tag_bb[1]

    text_w = max(word_w, tag_w)
    gap = int(H * 0.09)
    group_w = mk + gap + text_w
    gx = (W - group_w) // 2
    gy = (H - mk) // 2

    bg.alpha_composite(mark, (gx, gy))

    tx = gx + mk + gap
    line_gap = int(H * 0.07)
    block_h = word_h + line_gap + tag_h
    ty = (H - block_h) // 2
    d.text((tx, ty), "Pay", font=fbold, fill=WHITE)
    d.text((tx + pay_w, ty), "Rails", font=fbold, fill=CYAN)
    d.text((tx + 2, ty + word_h + line_gap), tag, font=ftag, fill=(170, 200, 195))

    return bg.convert("RGB").resize((w, h), Image.LANCZOS)


img = make_feature_graphic()
p = os.path.join(OUT, "feature_graphic_1024x500.png")
img.save(p)
print("wrote feature_graphic_1024x500.png", img.size)
