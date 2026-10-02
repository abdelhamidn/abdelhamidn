"""Generate the animated terminal-style SVGs used by the profile README."""
import re
import sys
import urllib.request
from datetime import date

USER = "abdelhamidn"
HANDLE = "ano"
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
    tips = dict(re.findall(r'for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)', html))
    total = 0
    for cid, text in tips.items():
        m = re.match(r"(\d+) contributions?", text.strip())
        if m:
            total += int(m.group(1))
    return cells, total


def svg_wrap(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}"><defs>{defs}</defs>{body}</svg>')


def prompt_svg(command, width=860, chars_per_sec=12):
    """`ano@github ~ $ command` typed out with a blinking cursor."""
    text = f"{HANDLE}@github ~ $ {command}"
    cw = 11.4
    n = len(text)
    tw = n * cw
    dur = max(n / chars_per_sec, 1)
    x0 = (width - tw) / 2
    css = (f"@keyframes type{{from{{width:0}}to{{width:{tw + 4:.1f}px}}}}"
           f"@keyframes cur{{from{{transform:translateX(0)}}to{{transform:translateX({tw:.1f}px)}}}}"
           "@keyframes blink{50%{opacity:0}}"
           f".t{{animation:type {dur:.1f}s steps({n}) forwards;width:0}}"
           f".c{{animation:cur {dur:.1f}s steps({n}) forwards,blink 1s step-end infinite}}")
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
    css = ("@keyframes in{from{opacity:0}to{opacity:1}}"
           "@keyframes wave{0%,100%{opacity:1}50%{opacity:.4}}"
           "rect.d{opacity:0;animation:in .5s forwards}"
           "rect.a{animation:in .5s forwards,wave 3s ease-in-out infinite}")
    out.insert(0, f"<style>{css}</style>")
    for d, row, col, lvl in cells:
        x, y = left + col * (size + gap), top + row * (size + gap)
        fill = EMPTY if lvl == 0 else LEVELS[lvl - 1]
        delay = f"{col * 0.04:.2f}s"
        style = f"animation-delay:{delay}" if lvl == 0 else f"animation-delay:{delay},{2.5 + col * 0.06:.2f}s"
        out.append(f'<rect class="{"d" if lvl == 0 else "a"}" x="{x}" y="{y}" width="{size}" height="{size}" rx="2" fill="{fill}" style="{style}"><title>{d}</title></rect>')
    out.append(f'<text x="{left}" y="{h - 14}" font-size="13" font-weight="700" fill="#e6edf3">{total:,} contributions in the last year</text>')
    return svg_wrap(w, h, "".join(out))


def wordmark_svg(word="ANO"):
    font = {
        "A": ["  ██  ", " ████ ", "██  ██", "██████", "██  ██", "██  ██"],
        "N": ["██   ██", "███  ██", "████ ██", "██ ████", "██  ███", "██   ██"],
        "O": [" ████ ", "██  ██", "██  ██", "██  ██", "██  ██", " ████ "],
    }
    rows = ["  ".join(font[ch][r] for ch in word) for r in range(6)]
    w, h, fs, lh = 860, 190, 26, 27
    def layer(dx, dy, fill):
        return "".join(
            f'<text x="{430 + dx}" y="{40 + dy + i * lh}" text-anchor="middle" font-size="{fs}" '
            f'font-weight="700" xml:space="preserve" fill="{fill}">{row}</text>' for i, row in enumerate(rows))
    defs = ('<linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#39d353"/>'
            '<stop offset="1" stop-color="#6cb6ff"/></linearGradient>')
    body = (f'<rect width="{w}" height="{h}" fill="{BG}"/>'
            '<g><animateTransform attributeName="transform" type="rotate" values="-1.5 430 95;1.5 430 95;-1.5 430 95" dur="5s" repeatCount="indefinite"/>'
            f'{layer(5, 5, "#0d4429")}{layer(0, 0, "url(#g)")}</g>')
    return svg_wrap(w, h, body, defs)


def main():
    cells, total = fetch_contributions()
    if not cells:
        sys.exit("no contribution data fetched")
    files = {
        "assets/contrib-heatmap.svg": heatmap_svg(cells, total),
        "assets/wordmark.svg": wordmark_svg(),
        "assets/prompt-contributions.svg": prompt_svg("./contributions.sh"),
        "assets/prompt-links.svg": prompt_svg("./links.sh"),
        "assets/prompt-skills.svg": prompt_svg("./skills.sh"),
    }
    for path, content in files.items():
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    print(f"wrote {len(files)} files, {total} contributions")


if __name__ == "__main__":
    main()
