"""
generator.py — Transforme un transfert en 3 images PNG (cover / move / info).
Utilise Playwright (Chromium headless) pour un rendu pixel-perfect du template.
"""
from __future__ import annotations
import re
import unicodedata
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
TEMPLATE = (HERE / "template.html").read_text(encoding="utf-8")

# Abréviations club pour les pastilles "crest" (texte, en attendant les vrais logos)
CREST_MAP = {
    "bordeaux":"UBB","bordeaux-bègles":"UBB","ubb":"UBB",
    "toulouse":"ST","stade toulousain":"ST",
    "la rochelle":"SR","stade rochelais":"SR",
    "racing":"R92","racing 92":"R92",
    "stade français":"SF","clermont":"ASM","asm":"ASM",
    "toulon":"RCT","rct":"RCT","lyon":"LOU","lou":"LOU",
    "castres":"CO","montpellier":"MHR","mhr":"MHR",
    "pau":"SP","section paloise":"SP","bayonne":"AB","aviron":"AB",
    "perpignan":"USAP","usap":"USAP","vannes":"RCV","montauban":"USM",
}

def crest_for(club: str | None) -> str:
    if not club: return "?"
    key = club.lower().strip()
    for k, v in CREST_MAP.items():
        if k in key: return v
    # fallback : initiales
    words = [w for w in re.split(r"[\s\-]+", club) if w]
    return ("".join(w[0] for w in words[:3])).upper() or "?"

def split_name(full: str) -> tuple[str, str]:
    parts = full.split()
    if len(parts) == 1: return "", parts[0].upper()
    return parts[0], " ".join(parts[1:]).upper()

def fill(transfer) -> str:
    first, last = split_name(transfer.player)
    from_crest = crest_for(transfer.from_club)
    to_crest = crest_for(transfer.to_club)
    has_dest = bool(transfer.to_club)

    repl = {
        "{{COMPET}}": "Top 14",
        "{{COVER_TAG}}": "Transfert " + ("acté" if transfer.status=="Officiel" else transfer.status.lower()),
        "{{FROM_SHORT}}": (transfer.from_club or "son club").split()[0],
        "{{FIRST}}": first or "",
        "{{LAST}}": last,
        "{{POSTE}}": transfer.poste or "—",
        "{{AGE}}": str(transfer.age) if transfer.age else "—",
        "{{PHOTO_CLASS}}": "",
        "{{PHOTO_STYLE}}": "",
        "{{FROM_CREST}}": from_crest,
        "{{FROM_NAME}}": transfer.from_club or "—",
        "{{ARROW_SUM}}": "vers son nouveau défi" if has_dest else "destination à venir",
        "{{TO_CREST}}": to_crest,
        "{{TO_NAME}}": transfer.to_club or "Nouvelle destination",
        "{{TO_ROLE}}": "Saison 2026/27" if has_dest else "À confirmer",
        "{{SEASON}}": "Mercato 2026/27",
        "{{SOURCE}}": transfer.source or "Allrugby",
        "{{STATUS}}": transfer.status,
        "{{STATUS_SHORT}}": {"Officiel":"Acté","Rumeur":"Rumeur","Prêt":"Prêt","Prolongation":"Prolongé"}.get(transfer.status, transfer.status),
    }
    html = TEMPLATE
    for k, v in repl.items():
        html = html.replace(k, v)
    return html

def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9]+","-", s.lower()).strip("-")

def render(transfer, outdir: Path) -> list[Path]:
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    html = fill(transfer)
    tmp = outdir / "_render.html"
    tmp.write_text(html, encoding="utf-8")
    slug = slugify(transfer.player)
    paths = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(viewport={"width":1080,"height":1920}, device_scale_factor=1)
        page.goto(tmp.as_uri())
        page.wait_for_timeout(400)
        for i, name in enumerate(["cover","move","info"], 1):
            el = page.query_selector(f'[data-slide="{name}"]')
            out = outdir / f"{slug}_{i}_{name}.png"
            el.screenshot(path=str(out))
            paths.append(out)
        b.close()
    tmp.unlink(missing_ok=True)
    return paths

if __name__ == "__main__":
    from scraper import Transfer
    demo = Transfer(date="2026-06-12", player="Madosh Tambwe", poste="Ailier",
                    age=29, from_club="Bordeaux", to_club=None,
                    status="Officiel", source="Allrugby", raw="")
    for p in render(demo, HERE / "out"):
        print("→", p)
