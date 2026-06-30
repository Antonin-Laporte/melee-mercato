"""
generator.py — Transforme un transfert en 3 images PNG (cover / move / info).
Utilise Playwright (Chromium headless) pour un rendu pixel-perfect du template.

Gere 3 types de mouvement :
  - transfert classique : club A -> club B
  - prolongation : reste dans son club (un seul logo, pas de fleche)
  - pret : club proprietaire -> club d'accueil (mention "en pret")

Logos : si un fichier logo existe dans logos/ (ex: logos/toulouse.png), il est
affiche a la place de l'abreviation texte. Sinon, fallback texte.
"""
from __future__ import annotations
import re
import base64
import unicodedata
from pathlib import Path
from playwright.sync_api import sync_playwright
from club_colors import gradients_for

HERE = Path(__file__).parent
TEMPLATE = (HERE / "template.html").read_text(encoding="utf-8")
LOGO_DIR = HERE / "logos"

# Abreviations club (fallback quand pas de logo image)
CREST_MAP = {
    "bordeaux":"UBB","bordeaux-begles":"UBB","ubb":"UBB",
    "toulouse":"ST","stade toulousain":"ST",
    "la rochelle":"SR","stade rochelais":"SR",
    "racing":"R92","racing 92":"R92",
    "stade francais":"SF","clermont":"ASM","asm":"ASM",
    "toulon":"RCT","rct":"RCT","lyon":"LOU","lou":"LOU",
    "castres":"CO","montpellier":"MHR","mhr":"MHR",
    "pau":"SP","section paloise":"SP","bayonne":"AB","aviron":"AB",
    "perpignan":"USAP","usap":"USAP","vannes":"RCV","montauban":"USM",
    "oyonnax":"OYO","nevers":"USON","agen":"SUA","nice":"RCN",
    "grenoble":"FCG","brive":"CABCL","dax":"USD","mont-de-marsan":"SMR",
}

# Cles normalisees -> nom de fichier logo (sans extension)
# Permet "Bordeaux-Begles" et "UBB" de pointer vers logos/bordeaux.png
LOGO_KEYS = {
    "bordeaux":"bordeaux","bordeaux-begles":"bordeaux","ubb":"bordeaux",
    "toulouse":"toulouse","stade toulousain":"toulouse",
    "la rochelle":"larochelle","stade rochelais":"larochelle",
    "racing":"racing92","racing 92":"racing92",
    "stade francais":"stadefrancais","clermont":"clermont","asm":"clermont",
    "toulon":"toulon","lyon":"lyon","lou":"lyon",
    "castres":"castres","montpellier":"montpellier",
    "pau":"pau","section paloise":"pau","bayonne":"bayonne","aviron":"bayonne",
    "perpignan":"perpignan","usap":"perpignan","vannes":"vannes",
    "montauban":"montauban","oyonnax":"oyonnax","nevers":"nevers",
    "agen":"agen","nice":"nice","grenoble":"grenoble","brive":"brive",
}

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return s.lower().strip()

def _find_logo(club: str | None) -> Path | None:
    """Cherche un fichier logo pour ce club dans logos/. None si absent."""
    if not club or not LOGO_DIR.exists():
        return None
    key = _norm(club)
    base = None
    for k, fname in LOGO_KEYS.items():
        if k in key:
            base = fname
            break
    if base is None:
        base = re.sub(r"[^a-z0-9]+", "", key)  # tente nom direct
    for ext in (".png", ".svg", ".jpg", ".jpeg", ".webp"):
        p = LOGO_DIR / f"{base}{ext}"
        if p.exists():
            return p
    return None

def crest_html(club: str | None) -> str:
    """Renvoie soit un <img> du logo, soit l'abreviation texte."""
    logo = _find_logo(club)
    if logo:
        data = base64.b64encode(logo.read_bytes()).decode()
        mime = "image/svg+xml" if logo.suffix==".svg" else f"image/{logo.suffix.lstrip('.')}"
        return f'<img src="data:{mime};base64,{data}" alt="">'
    # fallback texte
    if not club:
        return "?"
    key = _norm(club)
    for k, v in CREST_MAP.items():
        if k in key:
            return v
    words = [w for w in re.split(r"[\s\-]+", club) if w]
    return ("".join(w[0] for w in words[:3])).upper() or "?"

def crest_text(club: str | None) -> str:
    """Version texte seule (pour la slide info)."""
    if not club:
        return "—"
    key = _norm(club)
    for k, v in CREST_MAP.items():
        if k in key:
            return v
    words = [w for w in re.split(r"[\s\-]+", club) if w]
    return ("".join(w[0] for w in words[:3])).upper() or "—"

def split_name(full: str):
    parts = full.split()
    if len(parts) == 1:
        return "", parts[0].upper()
    return parts[0], " ".join(parts[1:]).upper()

ARROW_SVG = '<svg viewBox="0 0 24 40" fill="none" stroke="#c0392f" stroke-width="1.5"><path d="M12 2 L12 34 M5 27 L12 34 L19 27"/></svg>'

def fill(transfer) -> str:
    first, last = split_name(transfer.player)
    status = transfer.status
    from_html = crest_html(transfer.from_club)
    to_html = crest_html(transfer.to_club)
    has_dest = bool(transfer.to_club)

    # couleur = club d'ARRIVEE (ou le club lui-meme en prolongation)
    if status == "Prolongation":
        color_club = transfer.from_club or transfer.to_club
    else:
        color_club = transfer.to_club or transfer.from_club
    grad = gradients_for(color_club)

    # valeurs communes
    repl = {
        "{{COMPET}}": "Top 14",
        "{{FIRST}}": first or "",
        "{{LAST}}": last,
        "{{POSTE}}": transfer.poste or "\u2014",
        "{{AGE}}": str(transfer.age) if transfer.age else "\u2014",
        "{{PHOTO_CLASS}}": "",
        "{{PHOTO_STYLE}}": "",
        "{{BG_COVER}}": grad["cover"],
        "{{BG_MOVE}}": grad["move"],
        "{{BG_INFO}}": grad["info"],
        "{{SEASON}}": "Mercato 2026/27",
        "{{SOURCE}}": transfer.source or "Allrugby",
        "{{STATUS}}": status,
        "{{ARROW_SVG}}": ARROW_SVG,
        "{{FROM_CREST}}": from_html,
        "{{TO_CREST}}": to_html,
    }

    # ---- logique par TYPE ----
    if status == "Prolongation":
        club = transfer.from_club or transfer.to_club or "son club"
        repl.update({
            "{{COVER_TAG}}": "Prolongation",
            "{{COVER_OF}}": "il continue l'aventure \u00e0",
            "{{MOVE_EYEBROW}}": "Fid\u00e8le au club",
            "{{MOVE_TITLE}}": "Il prolonge<br>l'aventure",
            "{{MOVE_LAYOUT}}": "solo",
            "{{TO_HIDE}}": "",
            "{{FROM_NAME}}": club,
            "{{FROM_ROLE}}": "",
            "{{ARROW_SUM}}": "",
            "{{TO_CREST}}": crest_html(club),
            "{{TO_NAME}}": club,
            "{{TO_ROLE}}": "Nouveau contrat",
            "{{STATUS_SHORT}}": "Prolong\u00e9",
        })
        # cover : "il continue l'aventure a CLUB"
        repl["{{COVER_OF}}"] = f"il prolonge \u00e0 {club.split()[0]}"

    elif status == "Pret":
        repl.update({
            "{{COVER_TAG}}": "Pr\u00eat",
            "{{COVER_OF}}": f"pr\u00eat\u00e9 par {(transfer.from_club or 'son club').split()[0]}",
            "{{MOVE_EYEBROW}}": "Le mouvement",
            "{{MOVE_TITLE}}": "Il part<br>en pr\u00eat",
            "{{MOVE_LAYOUT}}": "",
            "{{TO_HIDE}}": "" if has_dest else "hide",
            "{{FROM_NAME}}": transfer.from_club or "\u2014",
            "{{FROM_ROLE}}": "Club pr\u00eateur",
            "{{ARROW_SUM}}": "en pr\u00eat" if has_dest else "destination \u00e0 venir",
            "{{TO_NAME}}": transfer.to_club or "Club d'accueil",
            "{{TO_ROLE}}": "En pr\u00eat 2026/27" if has_dest else "\u00c0 confirmer",
            "{{STATUS_SHORT}}": "Pr\u00eat",
        })

    else:  # Officiel / Rumeur = transfert classique
        tag = "Transfert act\u00e9" if status == "Officiel" else "Rumeur mercato"
        repl.update({
            "{{COVER_TAG}}": tag,
            "{{COVER_OF}}": f"il quitte {(transfer.from_club or 'son club').split()[0]}",
            "{{MOVE_EYEBROW}}": "Le mouvement",
            "{{MOVE_TITLE}}": "Il change<br>de maillot",
            "{{MOVE_LAYOUT}}": "",
            "{{TO_HIDE}}": "" if has_dest else "hide",
            "{{FROM_NAME}}": transfer.from_club or "\u2014",
            "{{FROM_ROLE}}": "Club quitt\u00e9",
            "{{ARROW_SUM}}": "vers son nouveau d\u00e9fi" if has_dest else "destination \u00e0 venir",
            "{{TO_NAME}}": transfer.to_club or "Nouvelle destination",
            "{{TO_ROLE}}": "Saison 2026/27" if has_dest else "\u00c0 confirmer",
            "{{STATUS_SHORT}}": "Act\u00e9" if status == "Officiel" else "Rumeur",
        })

    # slide info : "Quitte" devient "Club" en prolongation
    repl["{{FROM_CREST_TEXT}}"] = crest_text(transfer.from_club)
    if status == "Prolongation":
        repl["{{INFO_K3}}"] = "Club"
        repl["{{INFO_V3}}"] = crest_text(transfer.from_club or transfer.to_club)
    elif status == "Pret":
        repl["{{INFO_K3}}"] = "Pr\u00eat\u00e9 par"
        repl["{{INFO_V3}}"] = crest_text(transfer.from_club)
    else:
        repl["{{INFO_K3}}"] = "Quitte"
        repl["{{INFO_V3}}"] = crest_text(transfer.from_club)

    html = TEMPLATE
    for k, v in repl.items():
        html = html.replace(k, v)
    return html

def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return re.sub(r"[^a-z0-9]+","-", s.lower()).strip("-")

def render(transfer, outdir: Path) -> list:
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
    demo = Transfer(date="2026-06-15", player="Gabin Villiere", poste="Ailier",
                    age=30, from_club="Toulon", to_club="Toulon",
                    status="Prolongation", source="Allrugby", raw="")
    for p in render(demo, HERE / "out"):
        print("->", p)
