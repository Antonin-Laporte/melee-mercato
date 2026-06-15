# 🤖 Faire tourner Mêlée Mercato dans le cloud (GitHub Actions)

Objectif : le moteur tourne **tout seul chaque matin** sur les serveurs de
GitHub, sans ton ordi. Tu récupères les carrousels + vidéos du jour directement
depuis la page GitHub.

Tu as déjà un compte GitHub : parfait. Tout se fait depuis le **navigateur**,
zéro installation.

---

## Étape 1 — Créer le repository

1. Va sur https://github.com/new
2. **Repository name** : `melee-mercato` (ou ce que tu veux)
3. Coche **Private** (ton projet reste privé, recommandé)
4. Ne coche rien d'autre. Clique **Create repository**.

Tu arrives sur une page vide avec des instructions. Ignore-les, on passe par
l'upload direct (plus simple).

---

## Étape 2 — Uploader les fichiers du projet

1. Sur la page de ton repo vide, clique sur le lien
   **"uploading an existing file"** (ou : bouton **Add file → Upload files**).
2. **Glisse-dépose TOUT le contenu** du dossier `melee_mercato` dans la zone :
   - `run.py`, `scraper.py`, `generator.py`, `video.py`, `template.html`,
     `requirements.txt`, `README.md`, `diagnostic.py`
   - **ET le dossier `.github`** (très important : il contient le robot !)

   ⚠️ Si tu ne vois pas le dossier `.github` dans ton Finder, c'est qu'il est
   masqué (les dossiers commençant par un point sont cachés sur Mac).
   Dans le Finder, fais **Cmd + Shift + .** (point) pour afficher les fichiers
   cachés, et tu le verras apparaître.

3. En bas, clique **Commit changes**.

Vérifie : tu dois voir tous tes fichiers listés dans le repo, et un dossier
`.github/workflows/` contenant `mercato.yml`.

---

## Étape 3 — Activer le robot

1. Dans ton repo, clique sur l'onglet **Actions** (en haut).
2. GitHub détecte le workflow. S'il demande d'activer les workflows, clique
   **"I understand my workflows, go ahead and enable them"**.
3. Tu verras le workflow **"Melee Mercato - carrousels du jour"** dans la liste.

---

## Étape 4 — Premier test manuel

Pas besoin d'attendre demain matin pour tester :

1. Onglet **Actions** → clique sur **"Melee Mercato - carrousels du jour"**.
2. À droite, bouton **"Run workflow"** → confirme **Run workflow**.
3. Attends ~3-5 min (ça installe tout et génère). La ligne passe au vert ✅
   quand c'est fini.

---

## Étape 5 — Récupérer les carrousels + vidéos

1. Clique sur l'exécution terminée (la ligne verte).
2. Tout en bas, section **"Artifacts"** → **"mercato-du-jour"**.
3. Clique dessus : ça télécharge un `.zip` avec les carrousels (PNG) + vidéos
   (MP4) + le `captions.txt` du jour.
4. Décompresse, vérifie les noms, poste sur YouTube + TikTok. 🏉

---

## Et ensuite ? (automatique)

Le robot est programmé pour se lancer **tout seul chaque matin vers 8h**
(heure de Paris). Chaque jour, tu n'as qu'à :
1. Aller dans l'onglet **Actions**
2. Ouvrir l'exécution du jour
3. Télécharger l'artifact **mercato-du-jour**
4. Poster.

L'historique (`posted.json`) est sauvegardé automatiquement dans le repo, donc
**jamais deux fois le même transfert**, même en cloud.

---

## Réglages

- **Changer l'heure** : dans `.github/workflows/mercato.yml`, ligne `cron`.
  `'0 6 * * *'` = 6h UTC = 8h Paris (été) / 7h (hiver). Pour 9h Paris été : `'0 7 * * *'`.
- **Jour creux** : si aucun nouveau transfert, l'artifact peut être vide — c'est
  normal, poste un format "moment fort" à la main ce jour-là.

---

## Si un jour ça casse

Si l'exécution devient rouge ❌ (souvent : Allrugby a changé sa page) :
1. Clique sur l'exécution rouge → regarde l'étape en erreur.
2. Copie le message et envoie-le à Claude.
3. On corrige `scraper.py`, tu ré-uploades le fichier, et c'est reparti.
