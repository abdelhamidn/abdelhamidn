"""Generate the animated terminal-style SVGs used by the profile README."""
import re
import sys
import urllib.request
from datetime import date

USER = "abdelhamidn"
HANDLE = "abdelhamidn"
BG, FG, MUTED = "#22272e", "#adbac7", "#768390"
LEVELS = ["#0d4429", "#006d32", "#26a641", "#39d353"]  # level 1..4
EMPTY = "#16402b"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono',monospace"


def fetch_contributions():
    url = f"https://github.com/users/{USER}/contributions"
    html = urllib.request.urlopen(url, timeout=30).read().decode()
    cells = []
    for m in re.finditer(r'<td[^>]*data-date="([^"]+)" id="contribution-day-component-(\d+)-(\d+)" data-level="(\d)"', html):
        d, row, col, lvl = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        cells.append((d, row, col, lvl))
    m = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", html)
    total = int(m.group(1).replace(",", "")) if m else 0
    return cells, total


def svg_wrap(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}"><defs>{defs}</defs>{body}</svg>')


def prompt_svg(command, width=860, chars_per_sec=12):
    """`ano@github ~ $ command` typed out with a blinking cursor."""
    text = f"{HANDLE}@github ~ $ {command}"
    cw = 10.5
    n = len(text)
    tw = n * cw
    dur = max(n / chars_per_sec, 1)
    x0 = (width - tw) / 2
    css = (f"@keyframes type{{from{{width:0}}to{{width:{tw + 4:.1f}px}}}}"
           f"@keyframes cur{{from{{transform:translateX(0)}}to{{transform:translateX({tw:.1f}px)}}}}"
           "@keyframes blink{50%{opacity:0}}"
           f".t{{animation:type {dur:.1f}s steps({n}) forwards;width:0}}"
           f".c{{animation:cur {dur:.1f}s steps({n}) forwards,blink 1s step-end 8}}")
    body = f'''<style>{css}</style>
<rect width="{width}" height="56" fill="{BG}"/>
<clipPath id="c"><rect class="t" x="{x0:.1f}" y="10" height="36"/></clipPath>
<text x="{x0:.1f}" y="35" font-size="19" font-weight="700" fill="{FG}" clip-path="url(#c)" xml:space="preserve"><tspan fill="#39d353">{HANDLE}@github</tspan> <tspan fill="#6cb6ff">~</tspan> <tspan fill="{MUTED}">$</tspan> {command}</text>
<rect class="c" x="{x0:.1f}" y="16" width="10" height="24" fill="#39d353"/>'''
    return svg_wrap(width, 56, body)


def heatmap_svg(cells, total):
    size, gap = 11, 3
    left, top = 44, 34
    weeks = max(c[2] for c in cells) + 1
    w = left + weeks * (size + gap) + 20
    h = top + 7 * (size + gap) + 44
    out = [f'<rect width="{w}" height="{h}" rx="6" fill="{BG}"/>']
    # month labels
    last = None
    for d, row, col, _ in cells:
        if row == 0:
            mo = int(d[5:7])
            if mo != last:
                last = mo
                if col < 2:
                    continue
                name = date(2000, mo, 1).strftime("%b")
                out.append(f'<text x="{left + col * (size + gap)}" y="22" font-size="11" fill="{MUTED}">{name}</text>')
    for label, r in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        out.append(f'<text x="8" y="{top + r * (size + gap) + 10}" font-size="11" fill="{MUTED}">{label}</text>')
    css = "@keyframes in{from{opacity:0}to{opacity:1}}g.k{opacity:0;animation:in .5s forwards}@media (prefers-reduced-motion:reduce){g.k{animation:none;opacity:1}}"
    out.insert(0, f"<style>{css}</style>")
    columns = {}
    for d, row, col, lvl in cells:
        x, y = left + col * (size + gap), top + row * (size + gap)
        fill = EMPTY if lvl == 0 else LEVELS[lvl - 1]
        columns.setdefault(col, []).append(
            f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="2" fill="{fill}"><title>{d}</title></rect>')
    for col in sorted(columns):
        out.append(f'<g class="k" style="animation-delay:{col * 0.04:.2f}s">{"".join(columns[col])}</g>')
    out.append(f'<text x="{left}" y="{h - 14}" font-size="13" font-weight="700" fill="#e6edf3">{total:,} contributions in the last year</text>')
    return svg_wrap(w, h, "".join(out))


def wordmark_svg(word="ABDELHAMIDN"):
    font = {
        "A": [" ███ ", "█   █", "█   █", "█████", "█   █", "█   █"],
        "B": ["████ ", "█   █", "████ ", "█   █", "█   █", "████ "],
        "D": ["████ ", "█   █", "█   █", "█   █", "█   █", "████ "],
        "E": ["█████", "█    ", "████ ", "█    ", "█    ", "█████"],
        "L": ["█    ", "█    ", "█    ", "█    ", "█    ", "█████"],
        "H": ["█   █", "█   █", "█████", "█   █", "█   █", "█   █"],
        "M": ["█   █", "██ ██", "█ █ █", "█   █", "█   █", "█   █"],
        "I": ["█████", "  █  ", "  █  ", "  █  ", "  █  ", "█████"],
        "N": ["█   █", "██  █", "█ █ █", "█  ██", "█   █", "█   █"],
    }
    rows = [" ".join(font[ch][r] for ch in word) for r in range(6)]
    w, h, fs, lh = 860, 140, 18, 19
    cx, top = w // 2, 32

    def layer(dx, dy, fill):
        return "".join(
            f'<text x="{cx + dx}" y="{top + dy + i * lh}" text-anchor="middle" font-size="{fs}" '
            f'font-weight="700" xml:space="preserve" fill="{fill}">{row}</text>' for i, row in enumerate(rows))
    defs = ('<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#39d353"/>'
            '<stop offset="1" stop-color="#6cb6ff"/></linearGradient>')
    mid = f"{cx} {h // 2}"
    body = (f'<rect width="{w}" height="{h}" fill="{BG}"/>'
            f'<g><animateTransform attributeName="transform" type="rotate" values="0 {mid};-1.2 {mid};1.2 {mid};0 {mid}" dur="4s" repeatCount="3"/>'
            f'{layer(3, 3, "#0d4429")}{layer(0, 0, "url(#g)")}</g>')
    return svg_wrap(w, h, body, defs)


def main():
    cells, total = fetch_contributions()
    if not cells:
        sys.exit("no contribution data fetched")
    files = {
        "assets/contrib-heatmap.svg": heatmap_svg(cells, total),
        "assets/wordmark-v2.svg": wordmark_svg(),
        "assets/prompt-contributions-v2.svg": prompt_svg("./contributions.sh"),
        "assets/prompt-links-v2.svg": prompt_svg("./links.sh"),
        "assets/prompt-skills-v2.svg": prompt_svg("./skills.sh"),
    }
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"wrote {len(files)} files, {total} contributions")


if __name__ == "__main__":
    main()
