"""
run_news.py — Point d'entree ACTUS (staff, blessures, discipline, incertitudes).
Genere des habillages PNG transparents pour les infos importantes du jour.

Usage :
    python3 run_news.py            # actus du jour (tri strict)
    python3 run_news.py --top 2
    python3 run_news.py --demo     # demo hors-ligne
    python3 run_news.py --force    # ignorer l'historique
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime
from pathlib import Path

from news_scraper import get_news, select_top_news, NewsItem
from news_generator import render_news, slugify

HERE = Path(__file__).parent
OUT_ROOT = HERE / "actus"
HISTORY = HERE / "posted_news.json"

def load_history() -> set:
    if HISTORY.exists():
        try: return set(json.loads(HISTORY.read_text(encoding="utf-8")))
        except Exception: return set()
    return set()

def save_history(keys: set) -> None:
    HISTORY.write_text(json.dumps(sorted(keys), ensure_ascii=False, indent=2), encoding="utf-8")

def build_caption(n: NewsItem) -> str:
    emoji = {"Blessure":"🚑","Staff":"🔁","Discipline":"⚖️","Incertitude":"❓"}.get(n.category,"📰")
    return (f"{emoji} {n.category.upper()} — {n.title}\n"
            f"#rugby #top14 #{(n.club or 'rugby').lower().replace(' ','')} #acturugby\n"
            f"Source : {n.source}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    stamp = datetime.now().strftime("%Y-%m-%d")
    outdir = OUT_ROOT / stamp
    outdir.mkdir(parents=True, exist_ok=True)

    if args.demo:
        news = [NewsItem(stamp, "Toulouse : grosse blessure pour Antoine Dupont, forfait plusieurs semaines",
                         "Blessure","Toulouse","Rugby Addict","","")]
        history = set()
    else:
        print("-> Veille actus Rugby Addict...")
        try:
            alln = get_news()
        except Exception as e:
            print(f"  /!\\ Scraping impossible ({e}). On reessaiera.")
            return
        print(f"  {len(alln)} actus importantes detectees (apres tri strict).")
        history = set() if args.force else load_history()
        fresh = [n for n in alln if n.title[:60] not in history]
        if not fresh:
            print("  Aucune NOUVELLE actu importante. Jour creux cote infos.")
            return
        news = select_top_news(fresh, args.top)

    captions, posted = [], set(history)
    for n in news:
        print(f"-> Habillage : [{n.category}] {n.title[:55]}")
        p = render_news(n, outdir)
        captions.append(f"=== {n.title[:60]} ===\n{build_caption(n)}\nFichier : {p.name}\n")
        posted.add(n.title[:60])

    (outdir / "captions_actus.txt").write_text("\n".join(captions), encoding="utf-8")
    if not args.demo:
        save_history(posted)

    print(f"\n[OK] Habillages PNG transparents dans : {outdir}")
    print("     -> Glisse ta photo DERRIERE chaque PNG dans Canva, puis poste.")

if __name__ == "__main__":
    main()
