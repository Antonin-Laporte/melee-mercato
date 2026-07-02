# 📊 Ton dashboard Mêlée Mercato

Un tableau de bord web où, chaque matin, tu retrouves les carrousels et actus du
jour, prêts à télécharger. Gratuit, hébergé sur GitHub Pages.

---

## Mise en place (une seule fois)

### 1. Renseigne ton nom GitHub dans le dashboard
Ouvre `docs/index.html`, cherche cette ligne (vers la fin) :
```js
const GH_USER = "TON-USER";
```
Remplace `TON-USER` par ton identifiant GitHub (celui dans l'URL de ton repo :
`github.com/TON-USER/melee-mercato`). Sauvegarde.

### 2. Active GitHub Pages
Sur ton repo GitHub :
1. Onglet **Settings** → menu **Pages** (à gauche)
2. Section "Build and deployment", **Source** : choisis **Deploy from a branch**
3. **Branch** : `main`, dossier **`/docs`**
4. Clique **Save**

GitHub te donne une adresse du type :
`https://TON-USER.github.io/melee-mercato/`
C'est l'adresse de ton dashboard. Mets-la en favori sur ton téléphone. 📱

### 3. Upload les fichiers
Ré-uploade le projet sur ton repo (dont le dossier `docs/` et `build_manifest.py`).

---

## Utilisation quotidienne

1. Le matin, les robots tournent et publient les contenus du jour.
2. Ouvre ton dashboard (le lien github.io).
3. Onglet **Transferts** ou **Actus** : tu vois les cartes du jour.
4. Clique pour naviguer entre les slides, puis **télécharge** ce qu'il te faut.
5. Poste sur TikTok / YouTube. Voilà.

---

## L'onglet "Article manuel"

Pour une info que le robot n'a pas captée : colle l'URL de l'article, clique.
Ça t'envoie vers GitHub Actions pour lancer la génération (le robot fait le
travail, gratuit). Le résultat apparaît dans l'onglet Actus après quelques minutes.

> Note : la génération "en un clic instantané" nécessiterait un serveur payant.
> En version gratuite, on passe par le robot GitHub — quelques minutes d'attente,
> mais zéro coût.

---

## Si le dashboard est vide
- Vérifie que les robots ont bien tourné (onglet Actions, coche verte).
- Vérifie que GitHub Pages est actif (Settings → Pages).
- Le premier affichage peut prendre 1-2 min après l'activation de Pages.
