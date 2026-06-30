"""
article_extract.py — Recupere et resume le contenu d'un article rugby.

Suit le lien (issu du flux RSS), extrait les paragraphes principaux, et en tire
un resume court (2-4 phrases) pour la slide 2.

Robuste : si l'extraction echoue (paywall, blocage, format), retombe sur une
synthese minimale a partir du titre. Ne plante jamais.
"""
from __future__ import annotations
import re
from typing import Optional, List

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

def _fetch_page_text(url: str) -> str:
    """Charge l'article via navigateur et renvoie le texte des paragraphes."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(user_agent=UA)
        try:
            pg.goto(url, wait_until="domcontentloaded", timeout=25000)
            pg.wait_for_timeout(1500)
            # on cible le corps de l'article en priorite (selecteurs precis d'abord)
            paras = pg.eval_on_selector_all(
                "article p, [class*='article-body'] p, [class*='content-body'] p, "
                "[itemprop='articleBody'] p, .article-content p, .post-content p, "
                "main article p, .content p, main p",
                "els => els.map(e => e.innerText)"
            )
            # fallback : tous les <p> si rien trouve
            if not paras or len([p for p in paras if p and len(p) > 50]) < 2:
                paras = pg.eval_on_selector_all("p", "els => els.map(e => e.innerText)")
        except Exception:
            paras = []
        finally:
            b.close()
    # nettoyage : on garde les paragraphes substantiels
    PARASITES = [
        "cookie","abonn","newsletter","publicite","publicité","s'inscrire",
        "connectez-vous","lire aussi","© ","tous droits","donnees personnelles",
        "données personnelles","politique de","mentions legales","mentions légales",
        "vie privee","vie privée","rgpd","consentement","parametrer","paramétrer",
        "accepter les cookies","gerer mes choix","gérer mes choix","conditions generales",
        "conditions générales","cgu","cgv","inscrivez-vous","creez un compte",
        "créez un compte","deja inscrit","déjà inscrit","mot de passe","connexion",
        "votre adresse e-mail","votre email","s'identifier","identifiez-vous",
        "recevoir nos","suivez-nous","partager","commentaires","reagir","réagir",
        "a lire egalement","à lire également","sur le meme sujet","sur le même sujet",
        "ne ratez aucune","telechargez l'application","téléchargez l'application",
        "activer les notifications","contenu reserve","contenu réservé","premium",
        "déjà abonné","deja abonne",
    ]
    clean = []
    for t in paras:
        t = " ".join((t or "").split())
        if len(t) < 50:           # on relève le seuil : vrais paragraphes uniquement
            continue
        low = t.lower()
        if any(x in low for x in PARASITES):
            continue
        # un vrai paragraphe d'article finit generalement par une ponctuation
        if not re.search(r"[.!?»\"]\s*$", t):
            # tolere si assez long (phrase coupee en fin d'extrait)
            if len(t) < 90:
                continue
        clean.append(t)
    return "\n".join(clean[:8])  # max 8 paragraphes utiles


def summarize(title: str, link: Optional[str], max_chars: int = 360) -> str:
    """Renvoie un resume court de l'article. Fallback sur le titre si besoin."""
    body = ""
    if link:
        try:
            body = _fetch_page_text(link)
        except Exception:
            body = ""

    if not body:
        # fallback : reformulation simple a partir du titre
        _, phrase = (title.split(" : ", 1) + [title])[:2] if " : " in title else (None, title)
        return phrase.strip()

    # on prend les 1eres phrases jusqu'a ~max_chars
    sentences = re.split(r"(?<=[.!?])\s+", body.replace("\n", " "))
    out, total = [], 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if total + len(s) > max_chars and out:
            break
        out.append(s)
        total += len(s)
    summary = " ".join(out).strip()
    return summary or title


if __name__ == "__main__":
    # test fallback (sans lien)
    print(summarize("Toulouse : Dupont incertain pour la reprise", None))
