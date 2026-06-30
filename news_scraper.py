"""
news_scraper.py — Veille ACTUS rugby importantes (staff, blessures, forfaits...).

Source : flux RSS de Rugby Addict (agregateur Top 14 / Pro D2).
Tri STRICT par mots-cles : on ne garde que les sujets "majeurs" (staff, blessure
grave, forfait, suspension, incertitude) concernant des clubs de l'elite.

Le but n'est PAS de tout prendre, mais de filtrer le bruit.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

RSS_URL = "https://www.rugby-addict.com/fr/55d3bd647880b1a27a8b457d/rss"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# --- Mots-cles de TRI : l'actu doit en contenir au moins un (categorie) ---
KW_STAFF = ["entraineur","entraîneur","manager","staff","coach","directeur sportif",
            "limoge","demission","démission","nomme","nommé","arrivee staff","president",
            "président","remplace","succede","succède","intronise"]
KW_BLESSURE = ["blessure","blesse","blessé","forfait","indisponible","operation",
               "opération","ligaments","croises","croisés","ischio","commotion",
               "rechute","infirmerie","absence","out ","saison terminee","saison terminée"]
KW_DISCIPLINE = ["suspendu","suspension","cite","cité","commission","sanction",
                 "carton rouge","exclu","banni"]
KW_INCERTITUDE = ["incertain","doute","menace","pourrait manquer","en balance",
                  "compromis","inquietude","inquiétude","statut"]

ALL_KW = KW_STAFF + KW_BLESSURE + KW_DISCIPLINE + KW_INCERTITUDE

# --- Clubs elite : l'actu doit concerner l'un d'eux ---
ELITE = ["toulouse","bordeaux","begles","ubb","rochelle","rochelais","racing",
         "stade francais","stade français","clermont","asm","toulon","lyon","lou",
         "castres","montpellier","mhr","pau","paloise","bayonne","aviron","perpignan",
         "usap","vannes","montauban","oyonnax","grenoble","biarritz","brive","nevers",
         "agen","beziers","béziers","dax","xv de france","equipe de france","bleus"]

CATEGORIES = {
    "Staff": KW_STAFF, "Blessure": KW_BLESSURE,
    "Discipline": KW_DISCIPLINE, "Incertitude": KW_INCERTITUDE,
}

@dataclass
class NewsItem:
    date: str
    title: str
    category: str        # Staff / Blessure / Discipline / Incertitude
    club: Optional[str]
    source: str
    link: str
    raw: str

    def score(self) -> int:
        s = 0
        low = self.raw.lower()
        if any(c in low for c in ELITE): s += 3
        if "xv de france" in low or "equipe de france" in low or "bleus" in low: s += 2
        # priorite par categorie
        s += {"Blessure":3,"Staff":3,"Discipline":2,"Incertitude":1}.get(self.category,0)
        return s


def fetch_rss(url: str = RSS_URL) -> str:
    """Charge le flux RSS via navigateur (evite les blocages)."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA)
        resp = pg.goto(url, wait_until="domcontentloaded", timeout=30000)
        pg.wait_for_timeout(1200)
        # 1) on tente le corps brut de la reponse (vrai XML)
        content = ""
        try:
            if resp:
                content = resp.text()
        except Exception:
            content = ""
        # 2) si vide ou pas d'<item>, on prend le rendu navigateur
        if "<item" not in content.lower():
            try:
                content = pg.content()
            except Exception:
                pass
        # 3) si le navigateur a affiche le XML en texte, inner_text le recupere
        if "<item" not in content.lower():
            try:
                content = pg.inner_text("body")
            except Exception:
                pass
        b.close()
    return content


def detect_club(text: str) -> Optional[str]:
    low = text.lower()
    mapping = {
        "toulouse":"Toulouse","stade toulousain":"Toulouse",
        "bordeaux":"Bordeaux","begles":"Bordeaux","ubb":"Bordeaux",
        "rochelle":"La Rochelle","rochelais":"La Rochelle",
        "racing":"Racing 92","stade francais":"Stade Français","stade français":"Stade Français",
        "clermont":"Clermont","asm":"Clermont","toulon":"Toulon",
        "lyon":"Lyon","lou":"Lyon","castres":"Castres","montpellier":"Montpellier",
        "pau":"Pau","paloise":"Pau","bayonne":"Bayonne","aviron":"Bayonne",
        "perpignan":"Perpignan","usap":"Perpignan","vannes":"Vannes",
        "xv de france":"XV de France","equipe de france":"XV de France","bleus":"XV de France",
    }
    for k, v in mapping.items():
        if k in low:
            return v
    return None


def categorize(text: str) -> Optional[str]:
    low = text.lower()
    for cat, kws in CATEGORIES.items():
        if any(k in low for k in kws):
            return cat
    return None


def parse_rss(xml: str) -> List[NewsItem]:
    items = []
    # extraction simple des <item>...</item>
    blocks = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL | re.IGNORECASE)
    for blk in blocks:
        def tag(name):
            m = re.search(rf"<{name}>(.*?)</{name}>", blk, re.DOTALL | re.IGNORECASE)
            if not m: return ""
            v = m.group(1)
            v = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", v, flags=re.DOTALL)
            return re.sub(r"<.*?>", "", v).strip()
        title = tag("title")
        link = tag("link")
        if not title:
            continue
        cat = categorize(title)
        if cat is None:
            continue  # tri strict : pas de mot-cle = on jette
        if not any(c in title.lower() for c in ELITE):
            continue  # doit concerner un club elite
        items.append(NewsItem(
            date=datetime.now().strftime("%Y-%m-%d"),
            title=title, category=cat, club=detect_club(title),
            source="Rugby Addict", link=link, raw=title,
        ))
    return items


def get_news(xml: Optional[str] = None) -> List[NewsItem]:
    xml = xml if xml is not None else fetch_rss()
    seen, out = set(), []
    for it in parse_rss(xml):
        key = it.title[:60]
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def select_top_news(items: List[NewsItem], n: int = 3) -> List[NewsItem]:
    return sorted(items, key=lambda i: i.score(), reverse=True)[:n]


if __name__ == "__main__":
    # test sur echantillon XML
    sample = '''<rss><channel>
    <item><title>Toulouse : grosse blessure pour Antoine Dupont, forfait plusieurs semaines</title><link>http://x.fr/1</link></item>
    <item><title>Le Stade Toulousain prolonge son sponsor maillot</title><link>http://x.fr/2</link></item>
    <item><title>Clermont : un nouvel entraineur des avants nomme pour 2026</title><link>http://x.fr/3</link></item>
    <item><title>Recette de la mi-temps : les chips preferees des supporters</title><link>http://x.fr/4</link></item>
    <item><title>Toulon : Charles Ollivon suspendu trois matchs apres son carton rouge</title><link>http://x.fr/5</link></item>
    </channel></rss>'''
    for it in select_top_news(get_news(sample), 5):
        print(f"  [{it.score()}] {it.category:11} | {it.club or '-':12} | {it.title[:60]}")
