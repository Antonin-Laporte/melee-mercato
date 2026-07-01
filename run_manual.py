"""
run_manual.py — Genere un habillage actu a partir d'une URL d'article (a la demande).

Usage : python3 run_manual.py "https://www.rugbyrama.fr/..."

Recupere le titre + le contenu de l'article, detecte categorie/club automatiquement,
et genere les 2 slides. Ajoute au dashboard comme une actu normale.
"""
from __future__ import annotations
import sys, re
from datetime import datetime
from pathlib import Path

from news_scraper import NewsItem, categorize, detect_club
from news_generator import render_news
from article_extract import _fetch_page_text

HERE = Path(__file__).parent

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def fetch_title(url: str) -> str:
    """Recupere le <title> ou le <h1> de la page article."""
    from playwright.sync_api import sync_playwright
    title = ""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA)
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=25000)
            pg.wait_for_timeout(1200)
            # priorite au H1 de l'article, sinon le title de la page
            h1 = pg.query_selector("h1")
            title = (h1.inner_text() if h1 else pg.title()) or ""
        except Exception:
            title = ""
        finally:
            b.close()
    return " ".join(title.split())


def main():
    if len(sys.argv) < 2 or not sys.argv[1].startswith("http"):
        print("Usage : python3 run_manual.py \"https://...\"")
        sys.exit(1)
    url = sys.argv[1].strip()
    print(f"-> Article : {url}")

    title = fetch_title(url)
    if not title:
        print("  /!\\ Impossible de lire le titre de l'article.")
        sys.exit(1)
    print(f"  Titre : {title[:80]}")

    # categorie : on tente la detection auto ; sinon 'Actu' generique
    cat = categorize(title) or "Actu"
    club = detect_club(title) or "Rugby"
    # source = nom de domaine
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    source = m.group(1).replace(".fr","").replace(".com","").title() if m else "Web"

    news = NewsItem(datetime.now().strftime("%Y-%m-%d"),
                    title, cat, club, source, url, "")

    stamp = datetime.now().strftime("%Y-%m-%d")
    outdir = HERE / "actus" / stamp
    paths = render_news(news, outdir)
    print(f"  [OK] Genere : {', '.join(p.name for p in paths)}")

    # caption
    cap = outdir / "captions_actus.txt"
    line = f"=== [MANUEL] {title[:60]} ===\nSource : {source}\nFichiers : {', '.join(p.name for p in paths)}\n"
    with open(cap, "a", encoding="utf-8") as f:
        f.write("\n" + line)
    print("  Ajoute au dashboard (onglet Actus).")


if __name__ == "__main__":
    main()
