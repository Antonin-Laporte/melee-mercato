"""
build_manifest.py — Genere un manifest.json listant les contenus du jour,
pour que le dashboard sache quoi afficher. Lance apres run.py et run_news.py.

Copie aussi les fichiers du jour dans docs/ (servi par GitHub Pages).
"""
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
DOCS = HERE / "docs"           # GitHub Pages sert ce dossier
DATA = DOCS / "data"

def collect():
    stamp = datetime.now().strftime("%Y-%m-%d")
    DATA.mkdir(parents=True, exist_ok=True)

    entry = {"date": stamp, "transferts": [], "actus": []}

    # --- transferts du jour ---
    tdir = HERE / "carrousels" / stamp
    if tdir.exists():
        # regroupe par joueur (slug avant le _1/_2/_3)
        players = {}
        for f in sorted(tdir.glob("*.png")):
            slug = f.stem.rsplit("_", 2)[0] if "_" in f.stem else f.stem
            players.setdefault(slug, {"slug": slug, "slides": [], "video": None})
            players[slug]["slides"].append(f.name)
        for f in tdir.glob("*.mp4"):
            slug = f.stem
            players.setdefault(slug, {"slug": slug, "slides": [], "video": None})
            players[slug]["video"] = f.name
        # copie les fichiers dans docs/data/transferts/<date>/
        dest = DATA / "transferts" / stamp
        dest.mkdir(parents=True, exist_ok=True)
        for f in tdir.iterdir():
            if f.suffix in (".png", ".mp4"):
                shutil.copy(f, dest / f.name)
        cap = tdir / "captions.txt"
        if cap.exists():
            shutil.copy(cap, dest / "captions.txt")
        entry["transferts"] = list(players.values())

    # --- actus du jour ---
    adir = HERE / "actus" / stamp
    if adir.exists():
        items = {}
        for f in sorted(adir.glob("*.png")):
            slug = f.stem.rsplit("_", 1)[0]
            items.setdefault(slug, {"slug": slug, "slides": []})
            items[slug]["slides"].append(f.name)
        dest = DATA / "actus" / stamp
        dest.mkdir(parents=True, exist_ok=True)
        for f in adir.iterdir():
            if f.suffix == ".png":
                shutil.copy(f, dest / f.name)
        cap = adir / "captions_actus.txt"
        if cap.exists():
            shutil.copy(cap, dest / "captions_actus.txt")
        entry["actus"] = list(items.values())

    (DATA / "manifest.json").write_text(
        json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"manifest.json genere : {len(entry['transferts'])} transferts, {len(entry['actus'])} actus")

if __name__ == "__main__":
    collect()
