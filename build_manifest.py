"""
build_manifest.py — Genere docs/data/manifest.json pour le dashboard.

2 etapes :
  1) copie les fichiers FRAICHEMENT generes (carrousels/<date>, actus/<date>)
     vers docs/data/... (servi par GitHub Pages)
  2) SCANNE tout docs/data pour lister l'INTEGRALITE des contenus disponibles,
     groupes par date (le dashboard affiche ainsi tout, pas juste le dernier run)
"""
from __future__ import annotations
import json, shutil
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
DOCS = HERE / "docs"
DATA = DOCS / "data"

def _copy_fresh(stamp: str):
    """Copie les fichiers du run courant vers docs/data/."""
    # transferts
    tdir = HERE / "carrousels" / stamp
    if tdir.exists():
        dest = DATA / "transferts" / stamp
        dest.mkdir(parents=True, exist_ok=True)
        for f in tdir.iterdir():
            if f.suffix in (".png", ".mp4", ".txt"):
                shutil.copy(f, dest / f.name)
    # actus
    adir = HERE / "actus" / stamp
    if adir.exists():
        dest = DATA / "actus" / stamp
        dest.mkdir(parents=True, exist_ok=True)
        for f in adir.iterdir():
            if f.suffix in (".png", ".txt"):
                shutil.copy(f, dest / f.name)

def _scan_transferts(date_dir: Path):
    players = {}
    for f in sorted(date_dir.glob("*.png")):
        slug = f.stem.rsplit("_", 2)[0] if f.stem.count("_") >= 2 else f.stem
        players.setdefault(slug, {"slug": slug, "slides": [], "video": None})
        players[slug]["slides"].append(f.name)
    for f in sorted(date_dir.glob("*.mp4")):
        slug = f.stem
        players.setdefault(slug, {"slug": slug, "slides": [], "video": None})
        players[slug]["video"] = f.name
    return list(players.values())

def _scan_actus(date_dir: Path):
    items = {}
    for f in sorted(date_dir.glob("*.png")):
        slug = f.stem.rsplit("_", 1)[0]
        items.setdefault(slug, {"slug": slug, "slides": []})
        items[slug]["slides"].append(f.name)
    # tri des slides par numero (_1, _2, ...)
    for it in items.values():
        it["slides"].sort(key=lambda n: int(n.rsplit("_",1)[-1].split(".")[0]) if n.rsplit("_",1)[-1].split(".")[0].isdigit() else 0)
    return list(items.values())

def collect():
    stamp = datetime.now().strftime("%Y-%m-%d")
    DATA.mkdir(parents=True, exist_ok=True)

    # 1) copie les fichiers fraichement generes
    _copy_fresh(stamp)

    # 2) scanne TOUT docs/data, groupe par date
    days = {}
    troot = DATA / "transferts"
    if troot.exists():
        for date_dir in troot.iterdir():
            if date_dir.is_dir():
                lst = _scan_transferts(date_dir)
                if lst:
                    days.setdefault(date_dir.name, {"transferts": [], "actus": []})
                    days[date_dir.name]["transferts"] = lst
    aroot = DATA / "actus"
    if aroot.exists():
        for date_dir in aroot.iterdir():
            if date_dir.is_dir():
                lst = _scan_actus(date_dir)
                if lst:
                    days.setdefault(date_dir.name, {"transferts": [], "actus": []})
                    days[date_dir.name]["actus"] = lst

    # dates triees, plus recente d'abord
    sorted_dates = sorted(days.keys(), reverse=True)
    latest = sorted_dates[0] if sorted_dates else stamp

    manifest = {
        "generated": stamp,
        "latest": latest,
        "dates": sorted_dates,
        "days": days,
        # compat : contenu du jour le plus recent a la racine
        "date": latest,
        "transferts": days.get(latest, {}).get("transferts", []),
        "actus": days.get(latest, {}).get("actus", []),
    }

    (DATA / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    n_act = sum(len(d["actus"]) for d in days.values())
    n_tr = sum(len(d["transferts"]) for d in days.values())
    print(f"manifest.json : {len(sorted_dates)} jours, {n_tr} transferts, {n_act} actus au total")
    print(f"  plus recent ({latest}) : {len(manifest['actus'])} actus, {len(manifest['transferts'])} transferts")

if __name__ == "__main__":
    collect()
