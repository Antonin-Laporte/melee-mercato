"""
diagnostic_news.py — A lancer depuis TON Mac si le scraping d'actus deconne.
Montre ce que renvoie le flux RSS Rugby Addict et ce que le tri retient.

Lance :  python3 diagnostic_news.py
Puis envoie 'diagnostic_news_resultat.txt' a Claude.
"""
from __future__ import annotations
report = []
def log(*a):
    line = " ".join(str(x) for x in a); print(line); report.append(line)

from news_scraper import fetch_rss, parse_rss, ALL_KW, ELITE
import re

log("="*60); log("DIAGNOSTIC ACTUS — flux RSS Rugby Addict"); log("="*60)
try:
    xml = fetch_rss()
    log("Taille recue :", len(xml), "caracteres")
    nb_items = len(re.findall(r"<item>", xml, re.IGNORECASE))
    log("Nombre de <item> trouves :", nb_items)
    log("\n--- 10 premiers titres BRUTS (avant tri) ---")
    titles = re.findall(r"<title>(.*?)</title>", xml, re.DOTALL|re.IGNORECASE)
    for t in titles[1:11]:
        t = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", t, flags=re.DOTALL)
        t = re.sub(r"<.*?>","",t).strip()
        log("  •", t[:90])
    retenus = parse_rss(xml)
    log(f"\n--- {len(retenus)} actus RETENUES apres tri strict ---")
    for n in retenus[:10]:
        log(f"  [{n.category}] {n.club or '-'} | {n.title[:70]}")
except Exception as e:
    log("Erreur :", repr(e))

open("diagnostic_news_resultat.txt","w",encoding="utf-8").write("\n".join(report))
log("\n[OK] Fichier 'diagnostic_news_resultat.txt' cree. Envoie-le a Claude.")
