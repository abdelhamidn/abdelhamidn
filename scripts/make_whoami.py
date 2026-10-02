"""Build assets/whoami-v1.svg: two mini terminals, a colour ASCII portrait and a rotating 3D ASCII wordmark.

Run by hand when the photo or word changes (it is static, so it is not part of the daily workflow):
    python scripts/make_whoami.py
Needs Pillow and numpy.
"""
import math
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

PHOTO = "scripts/portrait-source.jpg"
OUT = "assets/whoami-v1.svg"
WORD = "ANO"
HANDLE = "abdelhamidn"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
W, H = 860, 424
WIN_Y, WIN_H, WIN_W = 16, 392, 398
WIN_X = (16, 446)
TITLE_H = 26
BODY_TOP = WIN_Y + TITLE_H + 6
FOOT_H = 24


# ---- portrait -------------------------------------------------------------
def cut_out(im):
    """Flood the plain studio backdrop from the borders; returns (rgb array, foreground mask)."""
    a = np.asarray(im).astype(int)
    h, w, _ = a.shape
    lum = a.mean(2)
    sat = a.max(2) - a.min(2)
    cand = (lum < 237) & (sat < 14) & (lum > 180)
    bg = np.zeros((h, w), bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if cand[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if cand[y, x] and not bg[y, x]:
                bg[y, x] = True
                dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not bg[ny, nx] and cand[ny, nx] and abs(lum[ny, nx] - lum[y, x]) < 4:
                bg[ny, nx] = True
                dq.append((ny, nx))
    # shirt shadows leak into the flood as thin tendrils: below the chin, open the backdrop mask to cut them off
    m = Image.fromarray((bg * 255).astype(np.uint8))
    opened = m.filter(ImageFilter.MinFilter(31)).filter(ImageFilter.MaxFilter(31))
    o = np.asarray(opened) > 127
    cut = int(h * 0.50)
    bg[cut:] = o[cut:]
    return a, ~bg


def lift(rgb):
    """Brighten dark pixels (hair) so they stay readable on the dark terminal."""
    lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
    t = max(0.0, (0.42 - lum) / 0.42) * 0.75
    tgt = (140, 160, 185)
    return tuple(int(rgb[i] * (1 - t) + tgt[i] * t) for i in range(3)), lum


def portrait_block(cols, area_w, area_h):
    im = Image.open(PHOTO).convert("RGB")
    a, fg = cut_out(im)
    box = (60, 185, 1100, 900)  # hair to collar
    a, fg = a[box[1]:box[3]], fg[box[1]:box[3]]
    ys, xs = np.nonzero(fg)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    a, fg = a[y0:y1, x0:x1], fg[y0:y1, x0:x1]
    h, w = fg.shape
    gray = ImageOps.autocontrast(Image.fromarray(a.astype(np.uint8)).convert("L"), cutoff=1)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=18, percent=320, threshold=0))  # local contrast: eyes, brows, beard
    rows = max(1, round(cols * h / w / 2))
    rgb = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((cols, rows), Image.BOX)).astype(int)
    cov = np.asarray(Image.fromarray((fg * 255).astype(np.uint8)).resize((cols, rows), Image.BOX)) / 255
    ramp = " .:-=+*#%@"
    cw = area_w / cols
    lh = min(area_h / rows, cw * 2.05)
    lum = np.asarray(gray.resize((cols, rows), Image.BOX)).astype(float) / 255
    solid = cov >= 0.45
    lo, hi = np.percentile(lum[solid], [4, 96])
    lines = []  # rows of (char, rgb tuple or None)
    for r in range(rows):
        line = []
        for c in range(cols):
            if not solid[r, c]:
                line.append((" ", None))
                continue
            norm = float(np.clip((lum[r, c] - lo) / (hi - lo), 0, 1))
            k = 0.75 + 0.5 * norm  # exaggerate light/dark so eyes, brows and beard read
            base = tuple(min(255, int(v * k)) for v in rgb[r, c])
            col, _ = lift(base)
            d = 0.22 + 0.78 * norm ** 0.8
            line.append((ramp[max(2, min(9, int(d * 10)))], col))
        lines.append(line)
    return lines, cw, lh


def palette(lines, n=28):
    px = [col for line in lines for _, col in line if col]
    img = Image.new("RGB", (len(px), 1))
    img.putdata(px)
    q = img.quantize(n, method=Image.Quantize.MEDIANCUT)
    raw = q.getpalette()[: n * 3]
    pal = ["#%02x%02x%02x" % tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)]
    it = iter(q.getdata())
    out = [[(ch, next(it) if col else None) for ch, col in line] for line in lines]
    return out, pal


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs(line, cls_of):
    """Collapse a row into <tspan> runs of equal class; spaces ride along with the previous run."""
    out, cur, buf = [], None, ""
    for ch, k in line:
        if ch != " " and k != cur:
            if buf:
                out.append((cur, buf))
            cur, buf = k, ""
        buf += ch
    if buf:
        out.append((cur, buf))
    return "".join(f'<tspan class="{cls_of(k)}">{esc(t)}</tspan>' if k is not None else esc(t) for k, t in out)


# ---- 3D wordmark ----------------------------------------------------------
def wordmark_frames(cols, rows, frames=60, depth=14):
    f = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf", 260)
    img = Image.new("L", (900, 420), 0)
    ImageDraw.Draw(img).text((20, 20), WORD, font=f, fill=255)
    img = img.crop(img.getbbox())
    mw = cols - 8
    mh = round(mw * img.height / img.width)
    img = img.resize((mw, mh), Image.LANCZOS)
    m = np.asarray(img) > 128
    blur = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(float) / 255
    gy, gx = np.gradient(blur)
    er = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3))) > 127
    edge = m & ~er
    cx, cy = mw / 2, mh / 2
    pts, nrm, kind = [], [], []
    zs = np.arange(-depth / 2, depth / 2 + 0.01, 0.5)
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if edge[y, x]:
            n = np.array([-gx[y, x], -gy[y, x], 0.0])
            n = n / (np.linalg.norm(n) or 1)
            for z in zs:
                pts.append((x - cx, y - cy, z)); nrm.append(n); kind.append(1)
        for z, nz in ((-depth / 2, -1.0), (depth / 2, 1.0)):
            pts.append((x - cx, y - cy, z)); nrm.append(np.array([0, 0, nz])); kind.append(0)
    P, N, K = np.array(pts), np.array(nrm), np.array(kind)
    light = np.array([-0.45, -0.55, 0.7]); light /= np.linalg.norm(light)
    ramp = " .:-=+*#%@"
    tilt = 0.22
    ct, st = math.cos(tilt), math.sin(tilt)
    out = []
    for fi in range(frames):
        th = 2 * math.pi * fi / frames
        c, s = math.cos(th), math.sin(th)
        x = P[:, 0] * c + P[:, 2] * s
        z = -P[:, 0] * s + P[:, 2] * c
        y = P[:, 1] * ct - z * st
        z2 = P[:, 1] * st + z * ct
        nx = N[:, 0] * c + N[:, 2] * s
        nz = -N[:, 0] * s + N[:, 2] * c
        ny = N[:, 1] * ct - nz * st
        nz2 = N[:, 1] * st + nz * ct
        b = 0.16 + 0.84 * np.clip(nx * light[0] + ny * light[1] + nz2 * light[2], 0, 1)
        u = np.clip((x + cols / 2).astype(int), 0, cols - 1)
        v = np.clip((y / 2 + rows / 2).astype(int), 0, rows - 1)
        bri = np.zeros((rows, cols))
        typ = np.zeros((rows, cols), int)
        for i in np.argsort(z2):  # far to near, so the nearest point writes last
            bri[v[i], u[i]] = b[i]
            typ[v[i], u[i]] = K[i] + 1
        out.append([[(ramp[min(9, max(1, int(bri[r, cc] * 10)))] if typ[r, cc] else " ", (typ[r, cc] - 1) if typ[r, cc] else None)
                     for cc in range(cols)] for r in range(rows)])
    return out


# ---- svg ------------------------------------------------------------------
def window(x, title):
    return (f'<rect x="{x}" y="{WIN_Y}" width="{WIN_W}" height="{WIN_H}" rx="10" fill="#0d1117" stroke="#30363d"/>'
            f'<path d="M{x} {WIN_Y + TITLE_H}V{WIN_Y + 10}a10 10 0 0 1 10 -10H{x + WIN_W - 10}a10 10 0 0 1 10 10V{WIN_Y + TITLE_H}z" fill="#161b22"/>'
            f'<line x1="{x}" y1="{WIN_Y + TITLE_H}" x2="{x + WIN_W}" y2="{WIN_Y + TITLE_H}" stroke="#30363d"/>'
            f'<circle cx="{x + 16}" cy="{WIN_Y + 13}" r="5" fill="#ff5f56"/><circle cx="{x + 32}" cy="{WIN_Y + 13}" r="5" fill="#ffbd2e"/>'
            f'<circle cx="{x + 48}" cy="{WIN_Y + 13}" r="5" fill="#27c93f"/>'
            f'<text x="{x + WIN_W / 2}" y="{WIN_Y + 17}" text-anchor="middle" font-size="11" fill="#8b949e">{esc(title)}</text>')


def build():
    area_w, area_h = WIN_W - 24, WIN_H - TITLE_H - FOOT_H - 14
    lines, cw, lh = portrait_block(116, area_w, area_h)
    lines, pal = palette(lines)
    fs = cw / 0.6
    px0 = WIN_X[0] + 12
    py0 = BODY_TOP + (area_h - lh * len(lines)) / 2
    css = ["text{font-family:" + FONT + ";white-space:pre}"]
    css += [f".c{i}{{fill:{c}}}" for i, c in enumerate(pal)]
    css += ["@keyframes rv{from{opacity:0}to{opacity:1}}.pr{opacity:0;animation:rv .3s forwards}",
            ".w0{fill:#39d353}.w1{fill:#58a6ff}"]
    body = [window(WIN_X[0], f"{HANDLE}@github: ~$ ./portrait.sh"), window(WIN_X[1], f"{HANDLE}@github: ~$ ./wordmark.sh --3d")]
    for i, line in enumerate(lines):
        y = py0 + (i + 1) * lh
        body.append(f'<text class="pr" style="animation-delay:{i * 0.035:.2f}s" x="{px0}" y="{y:.1f}" font-size="{fs:.2f}" '
                    f'textLength="{cw * len(line):.1f}" lengthAdjust="spacing" xml:space="preserve">{runs(line, lambda k: f"c{k}")}</text>')
    fy = WIN_Y + WIN_H - 10
    body.append(f'<text x="{WIN_X[0] + 14}" y="{fy}" font-size="11" fill="#e6edf3" xml:space="preserve">'
                f'<tspan fill="#39d353">{HANDLE}@github:~$</tspan> whoami: Abdelhamid NOIRA</text>')

    # wordmark: a stack of frames, shown one after another
    cols, rows, frames, dt = 78, 26, 60, 0.08
    wcw = area_w / cols
    wlh = wcw * 2.05
    wfs = wcw / 0.6
    wx0 = WIN_X[1] + 12
    wy0 = BODY_TOP + (area_h - wlh * rows) / 2
    total = frames * dt
    css.append(f"@keyframes sw{{0%{{opacity:1}}{100 / frames:.3f}%{{opacity:1}}{100 / frames + 0.001:.3f}%{{opacity:0}}100%{{opacity:0}}}}"
               f".f{{opacity:0;animation:sw {total:.2f}s linear infinite}}"
               "@media (prefers-reduced-motion:reduce){.f{animation:none}.f0{opacity:1}}")
    for fi, fr in enumerate(wordmark_frames(cols, rows, frames)):
        delay = 0 if fi == 0 else fi * dt - total
        g = [f'<g class="f f{fi}" style="animation-delay:{delay:.2f}s">']
        for r, line in enumerate(fr):
            if all(ch == " " for ch, _ in line):
                continue
            g.append(f'<text x="{wx0}" y="{wy0 + (r + 1) * wlh:.1f}" font-size="{wfs:.2f}" textLength="{wcw * cols:.1f}" '
                     f'lengthAdjust="spacing" xml:space="preserve">{runs(line, lambda k: f"w{k}")}</text>')
        g.append("</g>")
        body.append("".join(g))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<style>{"".join(css)}</style><rect width="{W}" height="{H}" fill="#22272e"/>'
            f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="#30363d"/>'
            f'<line x1="{W / 2}" y1="0" x2="{W / 2}" y2="{H}" stroke="#30363d"/>{"".join(body)}</svg>')


if __name__ == "__main__":
    svg = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg) // 1024} KB)")
