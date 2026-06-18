# -*- coding: utf-8 -*-
"""PayRails / fednowrtppayrails brand mark generator (Pillow only)."""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))

# ---- palette ----
BG_TOP = (12, 60, 45)      # #0C3C2D
BG_BOT = (5, 26, 19)       # #051A13
CYAN = (77, 182, 196)      # #4DB6C4
MINT = (95, 224, 192)      # #5FE0C0
WHITE = (240, 248, 247)

SS = 4  # supersample factor


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def vgradient(size, c_top, c_bot):
    """Vertical gradient RGBA image."""
    w, h = size
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        col = lerp(c_top, c_bot, t)
        for x in range(w):
            px[x, y] = col
    return img.convert("RGBA")


def diag_gradient(size, c1, c2):
    """Top-left -> bottom-right gradient."""
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
    """Return RGBA image (transparent) of the chevron-on-rails mark, centered.
    size: master square size in px (already supersampled).
    scale: fraction of the canvas the mark occupies.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # build an alpha mask for the mark, then fill with gradient
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)

    cx = size / 2
    cy = size * 0.42                     # chevrons sit a bit above center
    span = size * 0.40 * scale          # half-width footprint of the chevrons
    w = int(size * 0.085 * scale)       # stroke width
    h = size * 0.24 * scale             # chevron half-height

    def chevron(x_tip):
        # points: top-back, tip, bottom-back  (pointing right)
        x_back = x_tip - span * 0.55
        pts = [(x_back, cy - h), (x_tip, cy), (x_back, cy + h)]
        d.line(pts, fill=255, width=w, joint="curve")
        # rounded caps
        r = w / 2
        for (px_, py_) in pts:
            d.ellipse([px_ - r, py_ - r, px_ + r, py_ + r], fill=255)

    # two chevrons (fast-forward), offset horizontally
    off = span * 0.62
    chevron(cx - off * 0.15)
    chevron(cx + off * 0.85)

    # rail line beneath (the "rails")
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
    # subtle top sheen
    sheen = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sheen)
    sd.ellipse([-s * 0.3, -s * 0.75, s * 1.3, s * 0.35],
               fill=(255, 255, 255, 16))
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


def make_wordmark(height=520, on_dark=True):
    """Auto-width horizontal lockup at supersampled scale, then downscaled."""
    s = SS
    H = height * s
    pad = int(H * 0.16)
    mk = int(H * 0.70)

    fbold = load_font(["segoeuib.ttf", "arialbd.ttf", "Arialbd.ttf"], int(H * 0.36))
    fsmall = load_font(["segoeui.ttf", "arial.ttf"], int(H * 0.118))

    # measure text on a scratch drawing
    scratch = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    pay_w = scratch.textbbox((0, 0), "Pay", font=fbold)[2]
    rails_w = scratch.textbbox((0, 0), "Rails", font=fbold)[2]
    tag = "INSTANT PAYMENTS  ·  FEDNOW  ·  RTP"
    tag_w = scratch.textbbox((0, 0), tag, font=fsmall)[2]

    text_w = max(pay_w + rails_w, tag_w)
    tx = pad + mk + int(H * 0.16)
    W = tx + text_w + pad

    if on_dark:
        bg = vgradient((W, H), BG_TOP, BG_BOT)
        m = rounded_mask((W, H), radius=int(H * 0.18))
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        img.paste(bg, (0, 0), m)
    else:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    mark_tile = make_tile(mk // s, rounded=True).resize((mk, mk), Image.LANCZOS)
    img.alpha_composite(mark_tile, (pad, (H - mk) // 2))

    d = ImageDraw.Draw(img)
    ty = int(H * 0.22)
    d.text((tx, ty), "Pay", font=fbold, fill=WHITE)
    d.text((tx + pay_w, ty), "Rails", font=fbold, fill=CYAN)
    ty2 = ty + int(H * 0.42)
    d.text((tx + 2 * s, ty2), tag, font=fsmall, fill=(170, 200, 195))

    return img.resize((W // s, H // s), Image.LANCZOS)


def save(img, name):
    p = os.path.join(OUT, name)
    img.save(p)
    print("wrote", name, img.size)


# ---- app icons ----
save(make_tile(512, rounded=True), "icon_512.png")
save(make_tile(192, rounded=True), "icon_192.png")
# maskable: full-bleed square, smaller mark inside safe zone
save(make_tile(512, rounded=False, mark_scale=0.78), "icon_maskable_512.png")
save(make_tile(192, rounded=False, mark_scale=0.78), "icon_maskable_192.png")
save(make_tile(180, rounded=True), "apple_touch_icon_180.png")
save(make_tile(64, rounded=True), "favicon_64.png")
save(make_tile(32, rounded=True), "favicon_32.png")
# wordmark lockups
save(make_wordmark(520, on_dark=True), "logo_horizontal_dark.png")
save(make_wordmark(520, on_dark=False), "logo_horizontal_transparent.png")
print("done")
