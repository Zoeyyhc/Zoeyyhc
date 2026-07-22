#!/usr/bin/env python3
"""Generate the animated SVG assets for the profile README.

Two assets, each in a light and a dark variant:

  assets/banner-{light,dark}.svg  a terminal window whose `date` line reflects
                                  the real time and season in Melbourne
  assets/tech-{light,dark}.svg    the stack, rendered as terminal output

Everything is drawn from primitives here -- no external art, no logo paths.
Animation is SMIL so it runs when the SVG is loaded through an <img>, which is
how GitHub serves README images.

Run: python3 scripts/gen_assets.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo

MELBOURNE = ZoneInfo("Australia/Melbourne")
ASSETS = Path(__file__).resolve().parent.parent / "assets"

MONO = "ui-monospace,SFMono-Regular,SF Mono,Menlo,Consolas,Liberation Mono,monospace"
# Monospace advance width as a fraction of font size. Menlo/Consolas sit at .60;
# we lay out against that and pad, so a slightly wider fallback still fits.
CHAR_W = 0.60


# --------------------------------------------------------------------------
# theme
# --------------------------------------------------------------------------

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "chrome": "#161b22",
        "border": "#30363d",
        "text": "#c9d1d9",
        "dim": "#7d8590",
        "faint": "#484f58",
    },
    "light": {
        "bg": "#ffffff",
        "chrome": "#f6f8fa",
        "border": "#d0d7de",
        "text": "#1f2328",
        "dim": "#59636e",
        "faint": "#8c959f",
    },
}

# Time of day drives the accent. Melbourne local.
TIME_ACCENT = {
    "dawn": {"dark": "#f0a868", "light": "#b45309"},
    "day": {"dark": "#58a6ff", "light": "#0969da"},
    "dusk": {"dark": "#e8896b", "light": "#c2410c"},
    "night": {"dark": "#7ee0d0", "light": "#0f766e"},
}

# Season tints the streaming code lines. Southern hemisphere.
SEASON_TINT = {
    "summer": {"dark": "#8bd17c", "light": "#3f7a34"},
    "autumn": {"dark": "#d9a441", "light": "#8a5a10"},
    "winter": {"dark": "#7aa2d6", "light": "#3b5f96"},
    "spring": {"dark": "#c58bd1", "light": "#7a3d86"},
}


def phase_of_day(hour: int) -> str:
    if 5 <= hour < 8:
        return "dawn"
    if 8 <= hour < 17:
        return "day"
    if 17 <= hour < 20:
        return "dusk"
    return "night"


def season_of(month: int) -> str:
    if month in (12, 1, 2):
        return "summer"
    if month in (3, 4, 5):
        return "autumn"
    if month in (6, 7, 8):
        return "winter"
    return "spring"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_w(s: str, size: float) -> float:
    return len(s) * size * CHAR_W


def fade_in(begin: float, dur: float = 0.45) -> str:
    """A staggered one-shot fade that holds its end state.

    The delay is encoded as a flat leading segment of the value list rather than
    a `begin` offset, so the animation starts at 0s and there is no frame where
    the element is briefly visible before its turn. Pair with a static
    opacity="1" on the parent: if SMIL never runs, the content stays visible
    instead of degrading to a blank frame.
    """
    total = begin + dur
    hold = begin / total
    return (
        f'<animate attributeName="opacity" values="0;0;1" '
        f'keyTimes="0;{hold:.4f};1" begin="0s" dur="{total:.2f}s" fill="freeze"/>'
    )


def window_chrome(w: float, h: float, title: str, t: dict, accent: str) -> str:
    """Rounded terminal frame with a title bar and three dots."""
    bar = 34
    # the leftmost dot carries the accent, so the frame picks up the time of day
    colours = (accent, t["faint"], t["faint"])
    dots = "".join(
        f'<circle cx="{18 + i * 17}" cy="{bar / 2}" r="5" fill="{c}"/>'
        for i, c in enumerate(colours)
    )
    return f"""  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="11"
        fill="{t['bg']}" stroke="{t['border']}"/>
  <path d="M0.5 11.5a11 11 0 0 1 11-11h{w - 23}a11 11 0 0 1 11 11V{bar}H0.5Z"
        fill="{t['chrome']}"/>
  <line x1="0.5" y1="{bar}" x2="{w - 0.5}" y2="{bar}" stroke="{t['border']}"/>
  {dots}
  <text x="{w / 2}" y="{bar / 2 + 4}" font-family="{MONO}" font-size="11.5"
        fill="{t['dim']}" text-anchor="middle">{esc(title)}</text>"""


# --------------------------------------------------------------------------
# banner
# --------------------------------------------------------------------------

BANNER_W = 840


def build_banner(theme: str, now: dt.datetime) -> str:
    t = THEMES[theme]
    phase = phase_of_day(now.hour)
    season = season_of(now.month)
    accent = TIME_ACCENT[phase][theme]
    tint = SEASON_TINT[season][theme]

    bar = 34
    x = 26
    y = bar + 34
    lh = 27
    fs = 14.5

    # Deliberately no clock. The cron regenerates this every few hours, so a
    # printed time would be visibly stale to anyone loading the page in between.
    # Date and season only change on a scale the cron can keep up with; the time
    # of day shows up as the accent colour instead, which makes no literal claim.
    stamp = now.strftime("%A %-d %B %Y")

    body: list[str] = []
    delay = 0.15

    # Runs of text that change colour mid-line use tspan rather than a second
    # absolutely-positioned <text>: the browser advances the pen itself, so the
    # result does not depend on CHAR_W matching whatever mono font is installed.
    def prompt(cmd: str, at: float) -> str:
        p = "zoey@melbourne ~ %"
        return (
            f'<g opacity="1">{fade_in(at)}'
            f'<text x="{x}" y="{y}" xml:space="preserve" font-family="{MONO}" '
            f'font-size="{fs}" fill="{t["faint"]}">{esc(p)}'
            f'<tspan fill="{t["dim"]}"> {esc(cmd)}</tspan></text></g>'
        )

    body.append(prompt("whoami", delay))
    y += lh
    delay += 0.4
    name = "Zoey Cao"
    role = " · Full Stack Developer · Melbourne, Australia"
    body.append(
        f'<g opacity="1">{fade_in(delay)}'
        f'<text x="{x}" y="{y}" xml:space="preserve" font-family="{MONO}" '
        f'font-size="17" font-weight="600" fill="{accent}">{esc(name)}'
        f'<tspan font-weight="400" fill="{t["text"]}">{esc(role)}</tspan>'
        f"</text></g>"
    )

    y += lh + 8
    delay += 0.5
    body.append(prompt("date", delay))
    y += lh
    delay += 0.4
    scene = f"{stamp} · {season} in Melbourne"
    body.append(
        f'<g opacity="1">{fade_in(delay)}'
        f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" '
        f'fill="{tint}">{esc(scene)}</text></g>'
    )

    y += lh + 8
    delay += 0.5
    p = "zoey@melbourne ~ %"
    cursor_x = x + text_w(p + " ", fs)
    body.append(
        f'<g opacity="1">{fade_in(delay)}'
        f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{fs}" '
        f'fill="{t["faint"]}">{esc(p)}</text>'
        f'<rect x="{cursor_x}" y="{y - 12}" width="9" height="16" fill="{accent}">'
        f'<animate attributeName="opacity" values="1;1;0;0" dur="1.1s" '
        f'begin="{delay + 0.45:.2f}s" repeatCount="indefinite"/>'
        f"</rect></g>"
    )

    h = y + 26

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{BANNER_W}" height="{h:.0f}"
     viewBox="0 0 {BANNER_W} {h:.0f}" role="img"
     aria-label="Zoey Cao, Full Stack Developer, Melbourne, Australia">
{window_chrome(BANNER_W, h, "zoey@melbourne: ~", t, accent)}
  {"".join(body)}
</svg>
"""


# --------------------------------------------------------------------------
# tech stack
# --------------------------------------------------------------------------

# Brand colours are used only as a 6px dot next to each name -- no logo shapes.
# `None` falls back to the theme's dim colour (marks that are effectively
# monochrome, or concepts rather than products).
STACK: list[tuple[str, list[tuple[str, str | None]]]] = [
    (
        "languages",
        [
            ("C#", "#953dac"),
            ("TypeScript", "#3178c6"),
            ("Python", "#3776ab"),
            ("JavaScript", "#e8c020"),
        ],
    ),
    (
        "frontend",
        [
            ("React", "#61dafb"),
            ("Next.js", None),
            ("Vue", "#42b883"),
            ("Tailwind CSS", "#38bdf8"),
            ("Zustand", "#bf7c3f"),
        ],
    ),
    (
        "backend",
        [
            ("ASP.NET Core", "#7b5cf0"),
            ("FastAPI", "#009688"),
            ("Django / DRF", "#44b78b"),
            ("Flask", None),
            ("Express", None),
        ],
    ),
    (
        "data",
        [
            ("PostgreSQL", "#4169e1"),
            ("MS SQL", "#cc2927"),
            ("Cosmos DB", "#0078d4"),
            ("MongoDB", "#47a248"),
            ("Redis", "#dc382d"),
            ("pgvector", "#5b7fd4"),
        ],
    ),
    (
        "ai",
        [
            ("Anthropic Claude", "#d97757"),
            ("Claude Code", "#d97757"),
            ("OpenAI", "#10a37f"),
            ("CrewAI", "#ff5a50"),
            ("LangGraph", "#2f6f6f"),
            ("RAG", None),
        ],
    ),
    (
        "cloud",
        [
            ("Azure", "#0078d4"),
            ("AWS", "#ff9900"),
            ("GCP", "#4285f4"),
            ("Firebase", "#ffca28"),
        ],
    ),
    (
        "infra",
        [
            ("Docker", "#2496ed"),
            ("Terraform", "#7b42bc"),
            ("Bicep", "#0078d4"),
            ("GitHub Actions", "#2088ff"),
        ],
    ),
    (
        "testing",
        [
            ("pytest", "#0a9edc"),
            ("Vitest", "#6da544"),
            ("Jest", "#c21325"),
            ("Playwright", "#2ead33"),
            ("React Testing Library", "#e33332"),
        ],
    ),
]


def build_tech(theme: str, accent: str) -> str:
    t = THEMES[theme]
    bar = 34
    pad = 26
    fs = 13
    lh = 26
    label_w = 108
    dot_gap = 11
    tok_gap = 17

    rows: list[str] = []
    widest = 0.0
    y = bar + 32
    delay = 0.2

    for label, tokens in STACK:
        row = (
            f'<text x="{pad}" y="{y}" font-family="{MONO}" font-size="{fs}" '
            f'fill="{t["faint"]}">{esc(label)}</text>'
        )
        x = pad + label_w
        for name, colour in tokens:
            fill = colour or t["faint"]
            row += (
                f'<g opacity="1">{fade_in(delay, 0.35)}'
                f'<circle cx="{x + 3}" cy="{y - 4.5}" r="3.4" fill="{fill}"/>'
                f'<text x="{x + dot_gap}" y="{y}" font-family="{MONO}" '
                f'font-size="{fs}" fill="{t["text"]}">{esc(name)}</text></g>'
            )
            x += dot_gap + text_w(name, fs) + tok_gap
            delay += 0.055
        widest = max(widest, x - tok_gap)
        rows.append(row)
        y += lh

    w = max(BANNER_W, widest + pad)
    h = y + 14

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}"
     viewBox="0 0 {w:.0f} {h:.0f}" role="img"
     aria-label="Tech stack: languages, frontend, backend, data, AI, cloud, infra, testing">
{window_chrome(w, h, "zoey@melbourne: ~/stack", t, accent)}
  {"".join(rows)}
</svg>
"""


# --------------------------------------------------------------------------

def main() -> None:
    now = dt.datetime.now(MELBOURNE)
    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        accent = TIME_ACCENT[phase_of_day(now.hour)][theme]
        (ASSETS / f"banner-{theme}.svg").write_text(build_banner(theme, now))
        (ASSETS / f"tech-{theme}.svg").write_text(build_tech(theme, accent))
    print(
        f"generated for {now:%Y-%m-%d %H:%M %Z} "
        f"({phase_of_day(now.hour)}, {season_of(now.month)})"
    )


if __name__ == "__main__":
    main()
