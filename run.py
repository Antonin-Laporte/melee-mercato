"""
run.py — Point d'entree Melee Mercato.
Chaine complete : veille -> selection -> generation des carrousels du jour.

Systeme anti-jour-creux :
  1. Transferts du jour non encore postes (cas ideal)
  2. Sinon : recap des meilleurs transferts recents non postes
  3. Sinon : message clair (rien de neuf) -> a toi de poster un format "moment fort"

Un historique 'posted.json' retient les joueurs deja sortis pour ne pas repeter.

Usage :
    python3 run.py              # live Allrugby
    python3 run.py --top 2      # limiter le nombre
    python3 run.py --demo       # demo hors-ligne (Tambwe)
    python3 run.py --force      # ignorer l'historique (re-generer meme deja postes)
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from scraper import get_transfers, select_top, Transfer
from generator import render
from video import make_video, ffmpeg_available

HERE = Path(__file__).parent
OUT_ROOT = HERE / "carrousels"
HISTORY = HERE / "posted.json"


def load_history() -> set:
    if HISTORY.exists():
        try:
            return set(json.loads(HISTORY.read_text(encoding="utf-8")))
        except Exception:
            return set()
    return set()


def save_history(players: set) -> None:
    HISTORY.write_text(json.dumps(sorted(players), ensure_ascii=False, indent=2),
                       encoding="utf-8")


def build_caption(t: Transfer) -> str:
    dest = f"-> {t.to_club}" if t.to_club else "-> destination a venir"
    hook = {
        "Officiel": "C'est officiel !",
        "Rumeur": "Rumeur mercato",
        "Pret": "En pret cette saison",
        "Prolongation": "Il prolonge !",
    }.get(t.status, "Mercato")
    age = f", {t.age} ans" if t.age else ""
    return (
        f"{hook} {t.player} ({t.poste}{age}) quitte {t.from_club or '?'} {dest}\n"
        f"#rugby #top14 #mercato #transfert #ProD2 #rugbyfrance\n"
        f"Source : {t.source}"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--force", action="store_true", help="ignorer l'historique")
    ap.add_argument("--no-video", action="store_true",
                    help="ne generer que les carrousels (pas les MP4)")
    args = ap.parse_args()

    want_video = not args.no_video
    if want_video and not ffmpeg_available():
        print("  /!\\ FFmpeg introuvable : seuls les carrousels seront generes.")
        print("      Pour les videos : brew install ffmpeg  (puis relance)")
        want_video = False

    stamp = datetime.now().strftime("%Y-%m-%d")
    outdir = OUT_ROOT / stamp
    outdir.mkdir(parents=True, exist_ok=True)

    # --- DEMO ---
    if args.demo:
        transfers = [Transfer(date=stamp, player="Madosh Tambwe", poste="Ailier",
                              age=29, from_club="Bordeaux", to_club=None,
                              status="Officiel", source="Allrugby", raw="")]
        history = set()
    else:
        print("-> Veille Allrugby en cours...")
        try:
            all_t = get_transfers()
        except Exception as e:
            print(f"  /!\\ Scraping impossible ({e}).")
            print("     (Allrugby inaccessible aujourd'hui ; on reessaiera demain.)")
            return
        print(f"  {len(all_t)} transferts lus sur Allrugby.")

        history = set() if args.force else load_history()
        fresh = [t for t in all_t if t.player not in history]

        # cascade anti-jour-creux
        if fresh:
            transfers = select_top(fresh, args.top)
            print(f"  {len(fresh)} nouveaux (non postes) -> {len(transfers)} retenus.")
        else:
            print("  Aucun NOUVEAU transfert depuis le dernier passage.")
            print("  -> Jour creux : pense a un format 'moment fort' / 'recap semaine'.")
            print("     (ou relance avec --force pour re-sortir les tops recents)")
            return

    if not transfers:
        print("Rien a generer aujourd'hui.")
        return

    captions, posted = [], set(history)
    for t in transfers:
        print(f"-> Generation : {t.player} ({t.from_club} -> {t.to_club or '?'})")
        paths = render(t, outdir)
        line = (f"=== {t.player} ===\n{build_caption(t)}\n"
                f"Carrousel : {', '.join(p.name for p in paths)}")
        if want_video:
            from generator import slugify
            vpath = make_video(paths, outdir / f"{slugify(t.player)}.mp4")
            print(f"   + video : {vpath.name}")
            line += f"\nVideo : {vpath.name}"
        captions.append(line + "\n")
        posted.add(t.player)

    (outdir / "captions.txt").write_text("\n".join(captions), encoding="utf-8")
    if not args.demo:
        save_history(posted)

    print(f"\n[OK] Termine. Carrousels + legendes dans : {outdir}")
    print("     -> Ouvre le dossier, verifie les noms, poste sur YouTube Shorts + TikTok.")


if __name__ == "__main__":
    main()
