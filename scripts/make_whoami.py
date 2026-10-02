"""Build assets/whoami-v2.svg: one full-width terminal window with a rotating 3D ASCII wordmark.

Run by hand when the word changes (it is static, so it is not part of the daily workflow):
    python scripts/make_whoami.py
Needs Pillow and numpy.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = "assets/whoami-v2.svg"
WORD = "ANO"
HANDLE = "abdelhamidn"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"
W, H = 860, 418
WIN_X, WIN_Y, WIN_W, WIN_H = 1, 1, W - 2, H - 2
TITLE_H = 28
COLS, ROWS = 120, 26
FRAMES, DT = 48, 0.1


def wordmark_frames(cols, rows, frames, depth=16):
    f = ImageFont.truetype("C:/Windows/Fonts/ariblk.ttf", 260)
    img = Image.new("L", (900, 420), 0)
    ImageDraw.Draw(img).text((20, 20), WORD, font=f, fill=255)
    img = img.crop(img.getbbox())
    mw = cols - 12
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


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs(line):
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
    return "".join(f'<tspan class="w{k}">{esc(t)}</tspan>' if k is not None else esc(t) for k, t in out)


def build():
    x, y = WIN_X, WIN_Y
    body = [
        f'<rect x="{x}" y="{y}" width="{WIN_W}" height="{WIN_H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
        f'<path d="M{x} {y + TITLE_H}V{y + 10}a10 10 0 0 1 10 -10H{x + WIN_W - 10}a10 10 0 0 1 10 10V{y + TITLE_H}z" fill="#161b22"/>',
        f'<line x1="{x}" y1="{y + TITLE_H}" x2="{x + WIN_W}" y2="{y + TITLE_H}" stroke="#30363d"/>',
        f'<circle cx="{x + 18}" cy="{y + 14}" r="5.5" fill="#ff5f56"/><circle cx="{x + 36}" cy="{y + 14}" r="5.5" fill="#ffbd2e"/>'
        f'<circle cx="{x + 54}" cy="{y + 14}" r="5.5" fill="#27c93f"/>',
        f'<text x="{x + WIN_W / 2}" y="{y + 18}" text-anchor="middle" font-size="12" fill="#8b949e">{HANDLE}@github: ~$ ./wordmark.sh --3d</text>',
    ]
    area_w = WIN_W - 24
    cw = area_w / COLS
    lh = cw * 2.05
    fs = cw / 0.6
    x0 = x + 12
    y0 = y + TITLE_H + (WIN_H - TITLE_H - lh * ROWS) / 2
    total = FRAMES * DT
    css = ("text{font-family:" + FONT + ";white-space:pre}.w0{fill:#39d353}.w1{fill:#58a6ff}"
           f"@keyframes sw{{0%{{opacity:1}}{100 / FRAMES:.3f}%{{opacity:1}}{100 / FRAMES + 0.001:.3f}%{{opacity:0}}100%{{opacity:0}}}}"
           f".f{{opacity:0;animation:sw {total:.2f}s linear infinite}}"
           "@media (prefers-reduced-motion:reduce){.f{animation:none}.f0{opacity:1}}")
    for fi, fr in enumerate(wordmark_frames(COLS, ROWS, FRAMES)):
        delay = 0 if fi == 0 else fi * DT - total
        g = [f'<g class="f f{fi}" style="animation-delay:{delay:.2f}s">']
        for r, line in enumerate(fr):
            if all(ch == " " for ch, _ in line):
                continue
            g.append(f'<text x="{x0}" y="{y0 + (r + 1) * lh:.1f}" font-size="{fs:.2f}" textLength="{cw * COLS:.1f}" '
                     f'lengthAdjust="spacing" xml:space="preserve">{runs(line)}</text>')
        g.append("</g>")
        body.append("".join(g))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
            f'<style>{css}</style>{"".join(body)}</svg>')


if __name__ == "__main__":
    svg = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg) // 1024} KB)")
