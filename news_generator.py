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
from article_extract import summarize

HERE = Path(__file__).parent
TEMPLATE = (HERE / "template_news.html").read_text(encoding="utf-8")

EYEBROWS = {
    "Staff": "Mouvement de staff",
    "Blessure": "Infirmerie",
    "Discipline": "Discipline",
    "Incertitude": "Incertitude",
    "Selection": "Composition / Sélection",
    "Compo": "Composition",
    "Transfert": "Mercato",
    "Match": "Avant-match",
    "Déclaration": "La déclaration",
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

def fill(news, article_text: str = "", slide_num: int = 0, slide_total: int = 0) -> str:
    _, phrase = _clean_title(news.title)
    headline = phrase
    subline = ""
    # pagination "2/3" sur les slides texte (si plusieurs)
    pager = f"{slide_num}/{slide_total}" if slide_total > 1 and slide_num else ""

    repl = {
        "{{CATEGORY}}": news.category,
        "{{CLUB}}": news.club or "Top 14",
        "{{EYEBROW}}": EYEBROWS.get(news.category, "Actu"),
        "{{HEADLINE}}": headline,
        "{{SUBLINE}}": subline,
        "{{HEADLINE2}}": phrase,
        "{{ARTICLE}}": article_text or phrase,
        "{{PAGER}}": pager,
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

def render_news(news, outdir: Path, fetch_article: bool = True) -> list:
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # 1) recupere le corps de l'article et le REFORMULE en blocs
    from article_extract import get_body
    from rewrite import rewrite, chunk_for_slides
    text_slides = []
    if fetch_article:
        try:
            body = get_body(news.title, getattr(news, "link", None))
            if body:
                paras = rewrite(news.title, body, target_sentences=9)
                text_slides = chunk_for_slides(paras, per_slide_chars=300)
        except Exception:
            text_slides = []
    if not text_slides:
        phrase = news.title.split(" : ", 1)[-1] if " : " in news.title else news.title
        text_slides = [phrase.strip()]

    slug = slugify(news.title) or "actu"
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width":1080,"height":1920})

        # SLIDE 1 : habillage photo transparent
        html1 = fill(news, text_slides[0])
        tmp1 = outdir / "_n1.html"; tmp1.write_text(html1, encoding="utf-8")
        page.goto(tmp1.as_uri()); page.wait_for_timeout(700)
        el1 = page.query_selector('[data-slide="news"]')
        out1 = outdir / f"actu_{slug}_1.png"
        el1.screenshot(path=str(out1), omit_background=True)
        paths.append(out1)
        tmp1.unlink(missing_ok=True)

        # SLIDES TEXTE : une par bloc reformule
        total = len(text_slides)
        for idx, chunk in enumerate(text_slides, start=1):
            html2 = fill(news, chunk, slide_num=idx, slide_total=total)
            tmp2 = outdir / f"_n2_{idx}.html"; tmp2.write_text(html2, encoding="utf-8")
            page.goto(tmp2.as_uri()); page.wait_for_timeout(700)
            el2 = page.query_selector('[data-slide="news2"]')
            out2 = outdir / f"actu_{slug}_{idx+1}.png"
            el2.screenshot(path=str(out2))
            paths.append(out2)
            tmp2.unlink(missing_ok=True)

        b.close()
    return paths

if __name__ == "__main__":
    from news_scraper import NewsItem
    demo = NewsItem(date="2026-06-30",
        title="Toulouse : grosse blessure pour Antoine Dupont, forfait plusieurs semaines",
        category="Blessure", club="Toulouse", source="Rugby Addict",
        link="", raw="")
    print("->", render_news(demo, HERE / "out_news"))
