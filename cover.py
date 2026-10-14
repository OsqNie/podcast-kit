#!/usr/bin/env python3
"""Generate a 3000x3000 podcast cover (cover.jpg) from show.json: title, tagline and cover colours.

Usage: python3 cover.py      (needs Pillow: pip install pillow)
show.json "cover" keys (all optional): bg_top, bg_bottom, accent, text  (hex colours)
"""
import json
import pathlib
import sys

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError:
    sys.exit("Pillow is needed: pip install pillow")

HERE = pathlib.Path(__file__).resolve().parent
S = 3000
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def font(size):
    for path in FONT_CANDIDATES:
        if pathlib.Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def main():
    show = json.loads((HERE / "show.json").read_text(encoding="utf-8"))
    c = show.get("cover", {})
    top, bottom = hexrgb(c.get("bg_top", "#0B1424")), hexrgb(c.get("bg_bottom", "#0E1828"))
    mid = tuple(min(255, int(v * 2)) for v in top)
    accent, text = hexrgb(c.get("accent", "#ECAA48")), hexrgb(c.get("text", "#F4EEE4"))

    img = Image.new("RGB", (S, S))
    d = ImageDraw.Draw(img)
    hy = int(S * 0.62)
    for y in range(S):
        if y < hy:
            k = y / hy
            col = tuple(int(top[i] + (mid[i] - top[i]) * k) for i in range(3))
        else:
            col = bottom
        d.line([(0, y), (S, y)], fill=col)

    cx, r = S // 2, 620
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for i in range(40, 0, -1):
        g.ellipse([cx - r - i * 22, hy - r - i * 22, cx + r + i * 22, hy + r + i * 22], fill=accent + (5,))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img.paste(glow, (0, 0), glow)

    sun = Image.new("L", (S, S), 0)
    ImageDraw.Draw(sun).ellipse([cx - r, hy - r, cx + r, hy + r], fill=255)
    ImageDraw.Draw(sun).rectangle([0, hy, S, S], fill=0)
    img.paste(Image.new("RGB", (S, S), accent), (0, 0), sun)

    d = ImageDraw.Draw(img)
    d.line([(260, hy), (S - 260, hy)], fill=text, width=10)
    for k, rr in enumerate([800, 980, 1160]):
        fade = tuple(int(accent[i] * (1 - 0.3 * k) + bottom[i] * 0.3 * k) for i in range(3))
        d.arc([cx - rr, hy - rr, cx + rr, hy + rr], 180, 360, fill=fade, width=8 - k * 2)

    def centered(s, f, y, fill, track):
        w = sum(d.textlength(ch, font=f) for ch in s) + track * (len(s) - 1)
        x = (S - w) / 2
        for ch in s:
            d.text((x, y), ch, font=f, fill=fill)
            x += d.textlength(ch, font=f) + track

    title = show.get("title", "Podcast").upper()
    size = 400 if len(title) <= 10 else int(400 * 10 / len(title))
    centered(title, font(size), hy + 230, text, 60)
    if show.get("tagline"):
        centered(show["tagline"].upper(), font(110), hy + 760, accent, 30)
    img.save(HERE / "cover.jpg", quality=92)
    print("cover.jpg written")


if __name__ == "__main__":
    main()
