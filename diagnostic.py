"""
diagnostic.py — À lancer depuis TON Mac (pas besoin de comprendre le code).
But : voir ce qu'Allrugby renvoie réellement chez toi, pour qu'on corrige le
scraper avec certitude.

Lance simplement :   python3 diagnostic.py

Ça crée un fichier 'diagnostic_resultat.txt' dans le dossier.
Ouvre-le, copie son contenu et colle-le moi.
"""
from __future__ import annotations
import sys

URL = "https://www.allrugby.com/dossiers/transferts.html"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

report = []
def log(*a):
    line = " ".join(str(x) for x in a)
    print(line)
    report.append(line)

# ---------- Méthode 1 : requests ----------
log("=" * 60)
log("MÉTHODE 1 — requests")
log("=" * 60)
try:
    import requests
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=20)
    r.encoding = r.apparent_encoding
    log("Statut HTTP :", r.status_code)
    log("Taille reçue :", len(r.text), "caractères")
    for kw in ["quitte", "prolonge", "ans", "ème ligne", "·"]:
        log(f"  occurrences de {kw!r} :", r.text.count(kw))
    log("\n--- 1ères lignes contenant ' ans' ---")
    n = 0
    for line in r.text.replace("·", "\n").split("\n"):
        line = " ".join(line.split())
        if " ans" in line and "," in line and n < 8:
            log("  >", line[:170])
            n += 1
    if n == 0:
        log("  (aucune ligne de transfert trouvée par cette méthode)")
except Exception as e:
    log("Erreur requests :", repr(e))

# ---------- Méthode 2 : playwright ----------
log("\n" + "=" * 60)
log("MÉTHODE 2 — playwright (navigateur)")
log("=" * 60)
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA)
        pg.goto(URL, wait_until="domcontentloaded", timeout=30000)
        pg.wait_for_timeout(2500)
        title = pg.title()
        body = pg.inner_text("body")
        b.close()
    log("Titre de la page :", repr(title))
    log("Taille du texte :", len(body), "caractères")
    for kw in ["quitte", "prolonge", "ans"]:
        log(f"  occurrences de {kw!r} :", body.count(kw))
    log("\n--- 1ères lignes contenant ' ans' ---")
    n = 0
    for line in body.replace("·", "\n").split("\n"):
        line = " ".join(line.split())
        if " ans" in line and "," in line and n < 10:
            log("  >", line[:170])
            n += 1
    if n == 0:
        log("  (aucune ligne de transfert trouvée par cette méthode)")
except Exception as e:
    log("Erreur playwright :", repr(e))

with open("diagnostic_resultat.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(report))

log("\n" + "=" * 60)
log("✅ Fini. Ouvre 'diagnostic_resultat.txt', copie tout, colle-le à Claude.")
