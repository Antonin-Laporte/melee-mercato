"""
diagnostic_news.py — A lancer depuis TON Mac pour tester TOUS les flux RSS actus.
Dit lesquels marchent, combien d'actus chacun renvoie, et ce que le tri retient.

Lance :  python3 diagnostic_news.py
Puis envoie 'diagnostic_news_resultat.txt' a Claude.
"""
from __future__ import annotations
import re
report = []
def log(*a):
    line = " ".join(str(x) for x in a); print(line); report.append(line)

from news_scraper import fetch_rss, parse_rss, RSS_FEEDS, select_top_news

log("="*64); log("DIAGNOSTIC ACTUS — test de chaque flux RSS"); log("="*64)

all_items = []
for name, url in RSS_FEEDS:
    log(f"\n--- {name} ---"); log(f"    {url}")
    try:
        xml = fetch_rss(url)
        if "<item" not in xml.lower():
            log(f"    /!\\ Pas d'<item> trouve (flux mort, bloque, ou mauvaise URL). Taille recue: {len(xml)}")
            continue
        nb = len(re.findall(r"<item", xml, re.IGNORECASE))
        log(f"    OK — {nb} entrees brutes dans le flux")
        items = parse_rss(xml, source_name=name)
        log(f"    -> {len(items)} actus IMPORTANTES apres tri strict")
        for it in items[:4]:
            log(f"       [{it.category}] {it.title[:62]}")
        all_items += items
    except Exception as e:
        log(f"    ERREUR: {repr(e)[:100]}")

# fusion + dedup
seen, uniq = set(), []
for it in all_items:
    k = it.title[:60].lower()
    if k not in seen:
        seen.add(k); uniq.append(it)

log("\n" + "="*64)
log(f"TOTAL : {len(uniq)} actus importantes uniques (toutes sources fusionnees)")
log("--- Top 5 retenues ---")
for it in select_top_news(uniq, 5):
    log(f"  [{it.score()}] {it.category:11} | {it.club or '-':13} | src:{it.source}")
    log(f"      {it.title[:70]}")

open("diagnostic_news_resultat.txt","w",encoding="utf-8").write("\n".join(report))
log("\n[OK] Fichier 'diagnostic_news_resultat.txt' cree. Envoie-le a Claude.")
