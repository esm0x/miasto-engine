#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Grafiki do karty miasta w Google Play, z kolorów w city.json i podpisów w play/captions.json.

    python tools/store_assets.py lubomia

Wejście:  cities/<slug>/city.json                     kolory (theme.primary, theme.primaryDark)
          cities/<slug>/play/captions.json            podpisy zrzutów i teksty grafiki promocyjnej
          cities/<slug>/play/screenshots-916/raw-*/   surowe zrzuty z emulatorów 9:16
          (telefon 1080×1920, tablet 7" 1080×1920 @280 dpi, tablet 10" 1440×2560 @320 dpi)
Wyjście:  cities/<slug>/play/screenshots-916/phone/, tablet-7/, tablet-10/
          cities/<slug>/play/graphics/icon-512.png, feature-graphic-1024x500.png

Ikona to ten sam neutralny glif co w aplikacji (app/src/main/res/drawable/ic_city_glyph.xml),
na kolorze miasta. Miasto z własną ikoną kładzie ją jako play/graphics/icon-512.png
i ustawia "keepIcon": true w captions.json.

Zasady Google Play, których pilnuje skrypt:
  - zrzuty dokładnie 9:16, boki 320–3840 px (telefon) i 1080–7680 px (tablety), do 8 MB
  - podpis zajmuje najwyżej 20% wysokości; bez ramek urządzeń, bez „Pobierz teraz”, „#1”, cen
  - ikona 512×512, grafika 1024×500, PNG bez przezroczystości
"""

import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
GLYPH = ROOT / "app/src/main/res/drawable/ic_city_glyph.xml"
FONTS = Path("C:/Windows/Fonts")
WHITE = (255, 255, 255)

SETS = {  # katalog wejściowy → (wyjściowy, rozmiar płótna, zakres boków wg Google, minimum zrzutów)
    "raw-phone": ("phone", (1080, 1920), (320, 3840), 2),
    "raw-tablet7": ("tablet-7", (1080, 1920), (1080, 7680), 4),
    "raw-tablet10": ("tablet-10", (1440, 2560), (1080, 7680), 4),
}

BAND = 0.1875      # pas z podpisem: 18,75% wysokości (limit Google to 20%)
MAX_BYTES = 8 * 1024 * 1024


def rgb(hex_):
    return tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))


def shade(c, f):
    return tuple(round(v * f) for v in c)


def tint(c, f):
    """Towards white: f=0 leaves the colour, f=1 is white."""
    return tuple(round(v + (255 - v) * f) for v in c)


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def fit_text(d, text, name, size, max_w):
    while size > 20:
        f = font(name, size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 2
    return font(name, size)


def gradient(w, h, top, bottom):
    mask = Image.linear_gradient("L").resize((w, h))
    return Image.composite(Image.new("RGB", (w, h), bottom), Image.new("RGB", (w, h), top), mask)


# --- glif -------------------------------------------------------------------------------

def glyph_polygons():
    """Ścieżka z wektora Androida: same M/L/Z, więc wystarczy lista wielokątów."""
    data = re.search(r'android:pathData="([^"]+)"', GLYPH.read_text(encoding="utf-8")).group(1)
    polys = []
    for sub in re.findall(r"M[^MZ]+Z?", data):
        pts = [tuple(map(float, p)) for p in re.findall(r"(-?[\d.]+),(-?[\d.]+)", sub)]
        polys.append(pts)
    return polys


def draw_glyph(size, bg, scale=1.0):
    """Glif na pełnym kwadracie koloru miasta; evenOdd: kolejne podścieżki to otwory."""
    k = 4                                    # nadpróbkowanie zamiast antyaliasingu
    big = Image.new("RGB", (size * k, size * k), bg)
    d = ImageDraw.Draw(big)
    unit = size * k / 108 * scale
    off = size * k / 2 - 54 * unit
    for i, poly in enumerate(glyph_polygons()):
        d.polygon([(off + x * unit, off + y * unit) for x, y in poly], fill=WHITE if i == 0 else bg)
    return big.resize((size, size), Image.LANCZOS)


# --- zrzuty -----------------------------------------------------------------------------

def compose(raw: Path, size, caption, colors):
    top_c, bottom_c, sub_c, shadow_c = colors
    W, H = size
    s = W / 1080
    im = gradient(W, H, top_c, bottom_c)
    d = ImageDraw.Draw(im)
    title, sub = caption
    band = int(H * BAND)

    ft = fit_text(d, title, "segoeuib.ttf", int(66 * s), W - int(100 * s))
    fs = fit_text(d, sub, "segoeui.ttf", int(42 * s), W - int(100 * s))
    th = ft.getbbox(title)[3]
    sh = fs.getbbox(sub)[3]
    gap = int(18 * s)
    y0 = (band - (th + gap + sh)) // 2 + int(10 * s)
    d.text((W / 2, y0), title, font=ft, fill=WHITE, anchor="mt")
    d.text((W / 2, y0 + th + gap), sub, font=fs, fill=sub_c, anchor="mt")

    shot = Image.open(raw).convert("RGB")
    top, bottom = band + int(24 * s), H - int(44 * s)
    sh_h = bottom - top
    sh_w = round(sh_h * shot.width / shot.height)
    shot = shot.resize((sh_w, sh_h), Image.LANCZOS)
    x = (W - sh_w) // 2
    r = int(34 * s)

    mask = Image.new("L", (sh_w, sh_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sh_w - 1, sh_h - 1], radius=r, fill=255)
    shadow = Image.new("L", (W, H), 0)
    shadow.paste(mask, (x, top + int(16 * s)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(28 * s))).point(lambda v: int(v * .55))
    im.paste(Image.new("RGB", (W, H), shadow_c), (0, 0), shadow)
    im.paste(shot, (x, top), mask)
    return im


# --- grafika promocyjna -----------------------------------------------------------------

def feature_graphic(app_name, feature, primary, colors):
    top_c, bottom_c, sub_c, shadow_c = colors
    W, H = 1024, 500
    im = gradient(W, H, top_c, bottom_c)
    d = ImageDraw.Draw(im)

    # Ikona jak w launcherze: zaokrąglony kwadrat z cieniem po lewej.
    icon_size, ix, iy = 300, 70, 100
    icon = draw_glyph(icon_size, primary, scale=1.25)
    mask = Image.new("L", (icon_size, icon_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, icon_size - 1, icon_size - 1], radius=72, fill=255)
    shadow = Image.new("L", (W, H), 0)
    shadow.paste(mask, (ix, iy + 10))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * .5))
    im.paste(Image.new("RGB", (W, H), shadow_c), (0, 0), shadow)
    im.paste(icon, (ix, iy), mask)
    ImageDraw.Draw(im).rounded_rectangle([ix, iy, ix + icon_size - 1, iy + icon_size - 1], radius=72,
                                         outline=tint(primary, 0.3), width=2)

    tx, max_w = 430, W - 430 - 40
    ft = fit_text(d, app_name, "segoeuib.ttf", 84, max_w)
    d.text((tx, 140), app_name, font=ft, fill=WHITE, anchor="ls")
    y = 140 + 62
    fl = font("segoeui.ttf", 34)
    for line in feature["lines"]:
        f = fit_text(d, line, "segoeui.ttf", 34, max_w) if d.textlength(line, font=fl) > max_w else fl
        d.text((tx, y), line, font=f, fill=sub_c, anchor="ls")
        y += 46
    if feature.get("footer"):
        d.text((tx, y + 30), feature["footer"], font=fit_text(d, feature["footer"], "segoeui.ttf", 26, max_w),
               fill=sub_c, anchor="ls")
    return im


# --- main -------------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"[a-z0-9-]+", sys.argv[1]):
        sys.exit("Użycie: python tools/store_assets.py <slug>")
    city_dir = ROOT / "cities" / sys.argv[1]
    city = json.loads((city_dir / "city.json").read_text(encoding="utf-8"))
    play = city_dir / "play"
    spec = json.loads((play / "captions.json").read_text(encoding="utf-8"))
    shots, graphics = play / "screenshots-916", play / "graphics"
    graphics.mkdir(parents=True, exist_ok=True)

    primary = rgb(city["theme"]["primary"])
    # Podtytuł: jasny wariant motywu, rozbielony, żeby był czytelny na kolorze miasta.
    colors = (primary, shade(primary, 0.62), tint(rgb(city["theme"]["primaryDark"]), 0.55), shade(primary, 0.2))

    problems = []
    for src_dir, (dst_dir, size, (lo, hi), minimum) in SETS.items():
        src, dst = shots / src_dir, shots / dst_dir
        raws = sorted(src.glob("*.png"))
        if not raws:
            problems.append(f"{dst_dir}: brak zrzutów w {src_dir}/")
            continue
        dst.mkdir(exist_ok=True)
        for raw in raws:
            if raw.stem not in spec["captions"]:
                problems.append(f"{src_dir}/{raw.name}: brak podpisu w captions.json")
                continue
            out = dst / raw.name
            compose(raw, size, spec["captions"][raw.stem], colors).save(out, optimize=True)
            w, h = Image.open(out).size
            ok = w * 16 == h * 9 and lo <= min(w, h) and max(w, h) <= hi and out.stat().st_size <= MAX_BYTES
            if not ok:
                problems.append(str(out))
            print(f"  {dst_dir}/{out.name:<26} {w}×{h} {out.stat().st_size // 1024:>5} KB {'OK' if ok else 'BŁĄD'}")
        if len(raws) < minimum:
            problems.append(f"{dst_dir}: za mało zrzutów ({len(raws)}, Google wymaga {minimum})")

    if not spec.get("keepIcon"):
        draw_glyph(512, primary, scale=1.25).save(graphics / "icon-512.png", optimize=True)
    fg = feature_graphic(city["appName"], spec["feature"], primary, colors)
    fg.save(graphics / "feature-graphic-1024x500.png", optimize=True)
    for name, want in (("icon-512.png", (512, 512)), ("feature-graphic-1024x500.png", (1024, 500))):
        im = Image.open(graphics / name)
        ok = im.size == want and im.mode == "RGB"
        if not ok:
            problems.append(name)
        print(f"  graphics/{name:<30} {im.size[0]}×{im.size[1]} {im.mode} {'OK' if ok else 'BŁĄD'}")

    if problems:
        sys.exit("Problemy:\n  " + "\n  ".join(problems))
    print("Wszystko w limitach Google Play.")


if __name__ == "__main__":
    main()
