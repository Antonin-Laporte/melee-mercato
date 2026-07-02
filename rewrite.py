"""
rewrite.py — Reformulation GRATUITE (sans API) du contenu d'un article.

Objectif : produire un texte qui reprend les MEMES informations que l'article
mais avec une structure et des tournures differentes, pour ne pas etre une copie.
La source est toujours citee par ailleurs.

Approche (heuristique, pas d'IA) :
  - decoupe en phrases
  - nettoie les tournures journalistiques ("Selon nos informations", dates de pub...)
  - reorganise : phrase d'accroche reformulee + faits essentiels
  - varie les connecteurs
Ce n'est pas de la vraie IA, mais ca casse le copier-coller et ca structure.
"""
from __future__ import annotations
import re
from typing import List

# tournures a retirer / alleger
STRIP_PATTERNS = [
    r"selon (nos informations|le journal|le quotidien|l'?equipe|rmc|rtl)[^.,]*[.,]?",
    r"comme (l'?a )?(revele|rapporte|croit savoir|indique)[^.,]*[.,]?",
    r"d'?apres[^.,]*[.,]?",
    r"\b(hier|aujourd'?hui|ce (matin|soir|week-?end|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche))\b",
    r"\ba (indique|precise|explique|declare|confie|ajoute|poursuivi)\b",
]

CONNECTORS = ["Par ailleurs, ", "De plus, ", "Dans le detail, ", "A noter que ",
              "Concretement, ", "En parallele, "]

def _sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) > 25]

def _clean_sentence(s: str) -> str:
    low = s
    for pat in STRIP_PATTERNS:
        low = re.sub(pat, "", low, flags=re.IGNORECASE)
    low = re.sub(r"\s{2,}", " ", low).strip()
    low = re.sub(r"\s+([.,;:!?])", r"\1", low)  # espace avant ponctuation
    low = re.sub(r"^[,;:\-\s]+", "", low)
    # majuscule en debut
    if low and low[0].islower():
        low = low[0].upper() + low[1:]
    return low

def rewrite(title: str, body: str, target_sentences: int = 6) -> List[str]:
    """
    Renvoie une LISTE de paragraphes reformules (pour repartir sur plusieurs slides).
    """
    sents = _sentences(body)
    if not sents:
        # fallback : a partir du titre
        base = title.split(" : ", 1)[-1] if " : " in title else title
        return [base.strip()]

    cleaned = []
    seen = set()
    for s in sents:
        c = _clean_sentence(s)
        key = c.lower()[:40]
        if len(c) < 30 or key in seen:
            continue
        seen.add(key)
        cleaned.append(c)
        if len(cleaned) >= target_sentences:
            break

    # varie les connecteurs sur les phrases 2+ (sauf la 1ere = accroche)
    out = []
    ci = 0
    for i, c in enumerate(cleaned):
        if i == 0:
            out.append(c)
        else:
            # 1 phrase sur 2 recoit un connecteur pour fluidifier
            if i % 2 == 0 and ci < len(CONNECTORS):
                c2 = CONNECTORS[ci] + (c[0].lower() + c[1:] if c else c)
                ci += 1
                out.append(c2)
            else:
                out.append(c)
    return out

def chunk_for_slides(paragraphs: List[str], per_slide_chars: int = 320) -> List[str]:
    """Regroupe les phrases en blocs pour chaque slide (max ~320 car/slide)."""
    slides, cur, cur_len = [], [], 0
    for p in paragraphs:
        if cur and cur_len + len(p) > per_slide_chars:
            slides.append(" ".join(cur))
            cur, cur_len = [], 0
        cur.append(p)
        cur_len += len(p)
    if cur:
        slides.append(" ".join(cur))
    return slides[:3]  # max 3 slides de texte

if __name__ == "__main__":
    body = ("Selon nos informations, Antoine Dupont a repris l'entrainement ce lundi. "
            "Le demi de melee toulousain avait ete menage la semaine derniere. "
            "Comme l'a revele le staff, sa presence face aux All Blacks n'est pas encore assuree. "
            "Le joueur ressent encore une legere gene au genou. "
            "D'apres le club, une decision sera prise jeudi. "
            "Fabien Galthie souhaite ne prendre aucun risque avec son cadre.")
    paras = rewrite("XV de France : Dupont incertain", body)
    for s in chunk_for_slides(paras):
        print("SLIDE:", s, "\n")
