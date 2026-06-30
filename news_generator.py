"""
news_generator.py — Transforme une actu en habillage PNG TRANSPARENT.

Le PNG genere a :
  - en haut : voile sombre + logo + categorie + club
  - au centre : ZONE TRANSPARENTE (tu glisses ta photo derriere dans Canva)
  - en bas : bandeau degrade + titre de l'info + sous-texte

Cle technique : screenshot avec omit_background=True pour garder l'alpha.
"""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
TEMPLATE = (HERE / "template_news.html").read_text(encoding="utf-8")

EYEBROWS = {
    "Staff": "Mouvement de staff",
    "Blessure": "Infirmerie",
    "Discipline": "Discipline",
    "Incertitude": "Incertitude",
}

def _clean_title(title: str):
    """Separe un titre 'Club : phrase' en (club_part, phrase)."""
    if " : " in title:
        left, right = title.split(" : ", 1)
        return left.strip(), right.strip()
    return None, title.strip()

def _shorten(txt: str, maxlen: int = 90) -> str:
    if len(txt) <= maxlen:
        return txt
    cut = txt[:maxlen].rsplit(" ", 1)[0]
    return cut + "…"

def fill(news) -> str:
    _, phrase = _clean_title(news.title)
    # headline = la phrase principale, raccourcie ; subline = titre complet si long
    headline = _shorten(phrase, 80)
    subline = news.title if len(news.title) > 80 else ""

    repl = {
        "{{CATEGORY}}": news.category,
        "{{CLUB}}": news.club or "Top 14",
        "{{EYEBROW}}": EYEBROWS.get(news.category, "Actu"),
        "{{HEADLINE}}": headline,
        "{{SUBLINE}}": subline,
        "{{DATE}}": "Actu du jour",
        "{{SOURCE}}": news.source or "Rugby Addict",
    }
    html = TEMPLATE
    for k, v in repl.items():
        html = html.replace(k, v)
    return html

def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9]+","-", s.lower()).strip("-")[:50]

def render_news(news, outdir: Path) -> Path:
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    html = fill(news)
    tmp = outdir / "_news_render.html"
    tmp.write_text(html, encoding="utf-8")
    slug = slugify(news.title) or "actu"
    out = outdir / f"actu_{slug}.png"
    with sync_playwright() as p:
        b = p.chromium.launch()
        # viewport transparent
        page = b.new_page(viewport={"width":1080,"height":1920})
        page.goto(tmp.as_uri())
        page.wait_for_timeout(400)
        el = page.query_selector('[data-slide="news"]')
        # CLE : omit_background garde la transparence
        el.screenshot(path=str(out), omit_background=True)
        b.close()
    tmp.unlink(missing_ok=True)
    return out

if __name__ == "__main__":
    from news_scraper import NewsItem
    demo = NewsItem(date="2026-06-30",
        title="Toulouse : grosse blessure pour Antoine Dupont, forfait plusieurs semaines",
        category="Blessure", club="Toulouse", source="Rugby Addict",
        link="", raw="")
    print("->", render_news(demo, HERE / "out_news"))
