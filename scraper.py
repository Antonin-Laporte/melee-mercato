"""
scraper.py — Veille transferts rugby depuis Allrugby (v2).

Charge la page avec Playwright (un vrai navigateur) car Allrugby renvoie du
HTML brut illisible aux simples requetes 'requests'. Le rendu navigateur donne
des lignes propres du type :
    "Louka MAYRE, Centre, 18 ans, quitte Lyon pour s'engager avec Oyonnax ..."

Note legale : page publique de news transferts utilisee comme source de donnees
factuelles. Allrugby demande a etre cite — c'est fait dans les visuels
("Source - Allrugby") et dans les legendes.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

JOURNAL_URL = "https://www.allrugby.com/dossiers/transferts.html"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

ELITE_CLUBS = {
    "toulouse","bordeaux","bordeaux-begles","ubb","la rochelle","rochelais",
    "racing","stade francais","clermont","asm","toulon","lyon","lou",
    "castres","montpellier","pau","section paloise","bayonne","aviron","perpignan",
    "usap","vannes","montauban","nice","provence","grenoble","oyonnax",
    "mont-de-marsan","brive","nevers","agen","beziers","dax","aix","valence romans",
    "leinster","munster","ulster","connacht","saracens","leicester","exeter",
    "bath","northampton","harlequins","gloucester","bristol","sale","glasgow",
}

@dataclass
class Transfer:
    date: str
    player: str
    poste: str
    age: Optional[int]
    from_club: Optional[str]
    to_club: Optional[str]
    status: str
    source: str
    raw: str

    def score(self) -> int:
        s = 0
        fc = (self.from_club or "").lower()
        tc = (self.to_club or "").lower()
        if any(c in fc for c in ELITE_CLUBS): s += 3
        if any(c in tc for c in ELITE_CLUBS): s += 3
        if self.status == "Officiel": s += 4
        elif self.status == "Prolongation": s += 2
        elif self.status == "Rumeur": s += 1
        if self.age and self.age <= 30: s += 1
        if self.to_club: s += 2
        return s


def fetch_text(url: str = JOURNAL_URL) -> str:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA)
        pg.goto(url, wait_until="domcontentloaded", timeout=30000)
        pg.wait_for_timeout(2500)
        txt = pg.inner_text("body")
        b.close()
    return txt


POSTE_HINTS = ["pilier","talonneur","2eme ligne","2\u00e8me ligne","3eme ligne",
               "3\u00e8me ligne","melee","m\u00eal\u00e9e","ouverture",
               "centre","ailier","arriere","arri\u00e8re","polyvalent"]

def parse_line(line: str) -> Optional[Transfer]:
    txt = " ".join(line.split())
    if len(txt) < 15 or " ans" not in txt:
        return None
    if txt.lower().startswith(("si vous","le journal","allrugby","arriv","depart",
                               "d\u00e9part","espoir","pro ","une erreur")):
        return None

    m_name = re.match(r"^([A-Z\u00c0-\u017f][^,]{1,48}?)\s*,", txt)
    player = m_name.group(1).strip() if m_name else None
    if not player or len(player.split()) > 5:
        return None

    poste = next((p for p in POSTE_HINTS if p in txt.lower()), None)
    m_age = re.search(r",\s*(\d{1,2})\s*ans", txt)
    age = int(m_age.group(1)) if m_age else None

    low = txt.lower()
    if "prolonge" in low or "prolongation" in low: status = "Prolongation"
    elif "pr\u00eat\u00e9" in low or "pr\u00eat" in low: status = "Pret"
    elif "rumeur" in low or "serait" in low or "piste" in low: status = "Rumeur"
    else: status = "Officiel"

    from_club = to_club = None
    m_quit = re.search(r"quitte\s+(?:l[ae']\s*)?([A-Z\u00c0-\u017f][\w\u00c0-\u017f'\u2019\-\s]+?)(?:\s+pour\b|,|\s+\d|\s+source|\s+imm\u00e9diatement|$)", txt)
    if m_quit: from_club = m_quit.group(1).strip()
    m_to = re.search(r"(?:s'engager?\s+avec|rejoint|signe\s+\u00e0)\s+(?:l[ae']\s*)?([A-Z\u00c0-\u017f][\w\u00c0-\u017f'\u2019\-\s]+?)(?:\s+\d|\s+imm\u00e9diatement|,|\s+source|\s+\(|$)", txt)
    if m_to: to_club = m_to.group(1).strip()
    if not to_club and status == "Prolongation":
        m_pro = re.search(r"prolonge\s+(?:\u00e0|avec)\s+([A-Z\u00c0-\u017f][\w\u00c0-\u017f'\u2019\-\s]+?)(?:\s+\d|,|$)", txt)
        if m_pro: from_club = to_club = m_pro.group(1).strip()

    m_src = re.search(r"source\s+(.+?)\s*$", txt, re.IGNORECASE)
    source = m_src.group(1).strip() if m_src else "Allrugby"

    if not (from_club or to_club):
        return None

    # casse propre des postes (evite "3Eme Ligne")
    POSTE_LABEL = {
        "pilier":"Pilier","talonneur":"Talonneur","2eme ligne":"2eme ligne",
        "2\u00e8me ligne":"2\u00e8me ligne","3eme ligne":"3eme ligne",
        "3\u00e8me ligne":"3\u00e8me ligne","melee":"M\u00eal\u00e9e",
        "m\u00eal\u00e9e":"M\u00eal\u00e9e","ouverture":"Ouverture","centre":"Centre",
        "ailier":"Ailier","arriere":"Arri\u00e8re","arri\u00e8re":"Arri\u00e8re",
        "polyvalent":"Polyvalent",
    }
    poste_label = POSTE_LABEL.get(poste, poste.title()) if poste else "\u2014"

    return Transfer(
        date=datetime.now().strftime("%Y-%m-%d"),
        player=player, poste=poste_label,
        age=age, from_club=from_club, to_club=to_club,
        status=status, source=source, raw=txt,
    )


def get_transfers(text: Optional[str] = None) -> List[Transfer]:
    text = text if text is not None else fetch_text()
    out, seen = [], set()
    for chunk in re.split(r"\u00b7|\n", text):
        t = parse_line(chunk)
        if t and t.player not in seen:
            seen.add(t.player)
            out.append(t)
    return out


def select_top(transfers: List[Transfer], n: int = 3) -> List[Transfer]:
    return sorted(transfers, key=lambda t: t.score(), reverse=True)[:n]


if __name__ == "__main__":
    ts = get_transfers()
    print(f"{len(ts)} transferts parses")
    for t in select_top(ts, 8):
        print(f"  [{t.score()}] {t.player} - {t.poste} - {t.from_club} -> {t.to_club} ({t.status})")
