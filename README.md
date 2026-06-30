# Melee Mercato — moteur de carrousels transferts rugby

Genere des carrousels (cover / mouvement / fiche) au format 9:16 (1080x1920)
prets a poster sur **YouTube Shorts** et **TikTok**, a partir de la veille
transferts d'Allrugby.

Semi-auto : le script prepare visuels + legendes, tu verifies, tu postes.

---

## Installation (une seule fois)

Dans le Terminal, place-toi dans le dossier puis :

```bash
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

Pour generer aussi les **videos** (Shorts monetisables), installe FFmpeg :

```bash
brew install ffmpeg
```

(Si tu n'as pas Homebrew : https://brew.sh — ou lance le script sans video avec `--no-video`.)

---

## Utilisation quotidienne

```bash
python3 run.py            # carrousels (PNG) + videos (MP4) du jour
python3 run.py --no-video # carrousels seulement (pas de MP4)
python3 run.py --top 2    # limiter le nombre
python3 run.py --demo     # test hors-ligne (Tambwe)
python3 run.py --force    # ignorer l'historique, re-sortir les tops recents
```

Resultat : un dossier `carrousels/AAAA-MM-JJ/` contenant, pour chaque transfert :
- **3 PNG** (le carrousel) -> a poster sur TikTok + en post image YouTube
- **1 MP4** (~7 s, fondus + zoom) -> a poster en Short video YouTube (monetisable)
- un `captions.txt` avec legendes & hashtags prets a copier.

Tu ouvres, tu verifies les NOMS, tu postes.

### Pourquoi 2 formats ?
Les carrousels d'images YouTube comptent les vues mais ne sont PAS monetisables.
La version video (Short classique) l'est. On poste donc : carrousel pour
l'engagement/les abonnes, video pour les revenus. Sur TikTok, le carrousel suffit.

### Le son
Les videos sortent **sans audio** (pas de musique sous copyright). Ajoute un son
tendance directement dans l'editeur YouTube/TikTok au moment de poster : c'est ce
qui marche le mieux pour l'algo. Demande a Claude des recommandations de sons.

---

## Le systeme anti-jour-creux

Le rugby a des jours sans transfert. Le script gere ca :

1. **Nouveaux transferts du jour** -> il les sort (cas normal)
2. **Rien de neuf** -> il te le dit clairement et te suggere un format
   "moment fort" / "recap de la semaine" a poster a la main
3. `--force` -> re-sort les meilleurs transferts recents meme deja postes

Un fichier `posted.json` retient les joueurs deja sortis pour ne jamais repeter
deux fois le meme transfert.

---

## Structure

| Fichier | Role |
|---|---|
| `run.py` | point d'entree — lance toute la chaine |
| `scraper.py` | veille Allrugby (via navigateur) + scoring |
| `generator.py` | injecte les donnees + exporte les PNG |
| `video.py` | assemble les slides en MP4 (fondus + zoom) |
| `template.html` | design des slides |
| `diagnostic.py` | outil de debug si le scraping casse un jour |
| `posted.json` | historique auto des transferts deja postes |

---

## Reglages utiles

- **Nom du compte affiche** : dans `template.html`, cherche `@melee.mercato`
  et `MELEE.MERCATO`.
- **Clubs prioritaires** (scoring) : liste `ELITE_CLUBS` dans `scraper.py`.
- **Abreviations de club** (pastilles) : dico `CREST_MAP` dans `generator.py`.

---

## Si le scraping casse un jour

Allrugby peut changer la structure de sa page. Si `run.py` ne trouve plus rien :

```bash
python3 diagnostic.py
```

Ca cree `diagnostic_resultat.txt`. Envoie-le moi, je reajuste le parser.

---

## Points d'attention

1. **Verifie toujours les noms** avant de poster (parsing auto, pas infaillible
   sur noms composes / accents).
2. **Photos** : on est en option 2 (design sans photo copyright). Le filtre est
   deja pret dans `template.html` (bloc `.photo`) si un jour tu prends une
   licence photo.
3. **Citation source** : Allrugby est cite sur chaque visuel + legende, comme
   demande sur leur site.

---

---

## Logos de clubs

Le moteur affiche le **logo du club** s'il est disponible, sinon une
**abreviation texte** stylisee (UBB, ST, RCT...).

Pour ajouter des logos : depose les fichiers PNG (fond transparent) dans le
dossier `logos/`, nommes en minuscules sans accents (ex: `toulouse.png`,
`bordeaux.png`, `clermont.png`). Voir `logos/README.txt` pour la liste complete
des noms attendus. Tu peux en ajouter au fur et a mesure.

En cloud : pense a uploader le dossier `logos/` (avec tes PNG) dans le repo.

## Photos de joueurs en fond (optionnel)

Le bloc `.photo` du template est deja cable pour recevoir une image de fond
avec le filtre desature/contraste. Pour l'activer, il faudra brancher une
source d'images **libres de droits** (tu les fournis). Dis-le a Claude quand tu
veux franchir cette etape.

## Types de mouvement geres

Le moteur adapte automatiquement le visuel selon le type :
- **Transfert** : club A -> fleche -> club B
- **Prolongation** : un seul logo, "Il prolonge l'aventure" (pas de fleche)
- **Pret** : club preteur -> "en pret" -> club d'accueil
- **Rumeur** : tag "Rumeur mercato"

---

## Contenu ACTUS (staff, blessures, discipline, incertitudes)

En plus des transferts, le moteur genere des **habillages d'actu** : staff,
blessures importantes, suspensions, incertitudes — uniquement le gros (clubs
elite). Tri STRICT par mots-cles : le bruit (sponsors, calendrier, recettes...)
est ecarte.

### Format special : PNG transparent
L'habillage actu est un **PNG a fond transparent** :
- en haut : logo + categorie + club
- au centre : ZONE TRANSPARENTE -> tu glisses ta photo d'illustration derriere
  (dans Canva, Photoshop, etc.)
- en bas : bandeau degrade + titre de l'info

### Utilisation
```bash
python3 run_news.py            # actus du jour (tri strict)
python3 run_news.py --top 2
python3 run_news.py --demo     # test hors-ligne
python3 run_news.py --force    # ignorer l'historique
```
Resultat : dossier `actus/AAAA-MM-JJ/` avec les PNG transparents + captions.
Tu glisses ta photo derriere chaque PNG, puis tu postes.

### Source
Flux RSS de Rugby Addict (agregateur Top 14 / Pro D2). Si ca casse un jour :
`python3 diagnostic_news.py` puis envoie le resultat a Claude.

### En cloud
Un 2e workflow (`.github/workflows/actus.yml`) tourne chaque matin ~08h30.
Recupere l'artifact **actus-du-jour** dans l'onglet Actions.

### Reglages du tri
Les mots-cles sont dans `news_scraper.py` (listes KW_STAFF, KW_BLESSURE, etc.).
Ajoute/retire des termes pour affiner ce qui est considere "important".

## Prochaines etapes (Phase 2)

- Lancement automatique chaque matin (tache planifiee macOS).
- Notification Slack quand les carrousels du jour sont prets.
- Vrais logos de clubs (usage editorial).
- Format dedie "moment fort de la saison" pour les jours creux.
