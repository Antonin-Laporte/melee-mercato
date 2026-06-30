"""
club_colors.py — Couleurs officielles des clubs pour teinter les fonds.
Chaque club : (couleur principale, couleur secondaire) en hex.
Le fond degrade utilise la principale (visible) en s'assombrissant vers le bas
pour garder le texte clair lisible.
"""
from __future__ import annotations
import unicodedata
import re

# (primaire, secondaire)
CLUB_COLORS = {
    # --- TOP 14 ---
    "bordeaux":   ("#7a1f3d", "#1b2a4a"),   # bordeaux / marine
    "toulouse":   ("#9b1b863", "#1a1a1a"),  # (corrige plus bas)
    "larochelle": ("#f2c200", "#0a0a0a"),   # jaune / noir
    "racing92":   ("#0a1a4f", "#7fd0f0"),   # marine / ciel
    "stadefrancais": ("#e6447f", "#1a1a2e"),# rose / marine
    "clermont":   ("#0b2a5b", "#f2d600"),   # marine / jaune
    "toulon":     ("#c0151c", "#0a0a0a"),   # rouge / noir
    "lyon":       ("#1a2240", "#b71f2f"),   # marine / rouge
    "castres":    ("#1c2c6b", "#7fa8d8"),   # bleu / ciel
    "montpellier":("#0e2a55", "#2aa0e0"),   # marine / bleu
    "pau":        ("#0c4a36", "#0a8a4a"),   # vert
    "bayonne":    ("#7fb2e0", "#15224a"),   # ciel / marine
    "perpignan":  ("#b71515", "#f2c200"),   # rouge / or
    "vannes":     ("#10203f", "#5a7fb0"),   # marine
    # --- PRO D2 / gros ---
    "oyonnax":    ("#b71f2f", "#1a1a1a"),
    "grenoble":   ("#1a4a8a", "#b71f2f"),
    "nevers":     ("#1a3a7a", "#c0151c"),
    "agen":       ("#1a3a8a", "#ffffff"),
    "nice":       ("#c0151c", "#0a0a0a"),
    "brive":      ("#1a1a1a", "#ffffff"),
    "mont-de-marsan": ("#f2c200", "#1a1a1a"),
}
# corrections lisibles
CLUB_COLORS["toulouse"] = ("#9b1b1b", "#1a1a1a")  # rouge / noir

DEFAULT = ("#26262c", "#0a0a0c")  # gris sombre neutre (clubs inconnus)

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()
    return s.lower().strip()

# memes cles que les logos
KEY_MAP = {
    "bordeaux":"bordeaux","bordeaux-begles":"bordeaux","ubb":"bordeaux",
    "toulouse":"toulouse","stade toulousain":"toulouse",
    "la rochelle":"larochelle","stade rochelais":"larochelle",
    "racing":"racing92","racing 92":"racing92",
    "stade francais":"stadefrancais","clermont":"clermont","asm":"clermont",
    "toulon":"toulon","lyon":"lyon","lou":"lyon",
    "castres":"castres","montpellier":"montpellier",
    "pau":"pau","section paloise":"pau","bayonne":"bayonne","aviron":"bayonne",
    "perpignan":"perpignan","usap":"perpignan","vannes":"vannes",
    "oyonnax":"oyonnax","grenoble":"grenoble","nevers":"nevers","agen":"agen",
    "nice":"nice","brive":"brive","mont-de-marsan":"mont-de-marsan",
}

def colors_for(club: str | None):
    """Renvoie (primaire, secondaire) pour un club, ou DEFAULT."""
    if not club:
        return DEFAULT
    key = _norm(club)
    for k, base in KEY_MAP.items():
        if k in key:
            return CLUB_COLORS.get(base, DEFAULT)
    return DEFAULT

def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0,2,4))

def _mix(hex1, hex2, t):
    """Melange lineaire t entre 2 couleurs (t=0 -> hex1, t=1 -> hex2)."""
    r1,g1,b1 = _hex_to_rgb(hex1); r2,g2,b2 = _hex_to_rgb(hex2)
    r = round(r1+(r2-r1)*t); g = round(g1+(g2-g1)*t); b = round(b1+(b2-b1)*t)
    return f"#{r:02x}{g:02x}{b:02x}"

def darken(hex_c, t=0.6):
    """Assombrit une couleur vers le noir (t=0.6 = 60% plus sombre)."""
    return _mix(hex_c, "#08080a", t)

def gradients_for(club: str | None) -> dict:
    """Renvoie les 3 fonds CSS (cover/move/info) teintes pour le club."""
    prim, sec = colors_for(club)
    # versions assombries pour garder le texte clair lisible en bas
    prim_dark = darken(prim, 0.45)
    prim_deep = darken(prim, 0.78)
    sec_deep = darken(sec, 0.7)

    # COVER : la couleur monte du bas, sombre en haut (la photo/silhouette respire)
    cover = (f"radial-gradient(75% 55% at 62% 32%, {prim_dark} 0%, "
             f"{prim_deep} 48%, #0a0a0c 100%)")
    # MOVE : couleur affirmee en haut, vire au sombre au centre
    move = (f"radial-gradient(130% 95% at 50% -8%, {prim} 0%, "
            f"{prim_deep} 52%, #0a0a0c 100%)")
    # INFO : diagonale couleur -> noir
    info = (f"linear-gradient(160deg, {prim_dark} 0%, {prim_deep} 45%, #0a0a0c 100%)")
    return {"cover": cover, "move": move, "info": info,
            "primary": prim, "secondary": sec}

if __name__ == "__main__":
    for c in ["Bayonne","Toulon","Clermont","Bordeaux","Inconnu FC"]:
        g = gradients_for(c)
        print(f"{c:14} prim={g['primary']}  move={g['move'][:50]}...")
