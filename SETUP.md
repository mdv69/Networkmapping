# NetMap — mise en route

App en un seul fichier (`index.html`) : contacts, clusters, priorité, carte D3, import Excel/CSV, synchro cloud via Supabase.

## 1. Créer le projet Supabase (gratuit)

1. Va sur https://supabase.com → *New project*.
2. Une fois le projet créé, ouvre **SQL Editor** et exécute :

```sql
create table netmap_state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null,
  updated_at timestamptz not null default now()
);

alter table netmap_state enable row level security;

create policy "own row only"
  on netmap_state
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
```

Cette table stocke tout ton réseau (contacts, clusters, liens) dans une seule ligne JSON, protégée pour que toi seul puisses la lire/écrire.

3. Crée ton compte de connexion : **Authentication → Users → Add user**, renseigne ton email et un mot de passe. (Pas besoin d'un vrai email fonctionnel — c'est juste un identifiant, pas un envoi de mail.) Décoche/valide "Auto Confirm User" pour qu'il soit actif immédiatement.

4. Récupère tes clés : **Project Settings → API** → copie `Project URL` et la clé `anon public`.

## 2. Configurer index.html

Ouvre `index.html`, cherche ce bloc (juste après les fonctions IndexedDB) :

```js
const SUPABASE_URL = "";
const SUPABASE_ANON_KEY = "";
```

Colle tes valeurs entre les guillemets. Sans ça, l'app tourne quand même mais reste 100% locale (pas de synchro entre appareils).

## 3. Déployer sur Netlify

Le plus simple, sans ligne de commande :

1. Va sur https://app.netlify.com/drop
2. Glisse le fichier `index.html` (et `SETUP.md` si tu veux) dans la zone de dépôt.
3. Netlify te donne une URL du type `https://un-nom-aleatoire.netlify.app`. Accessible depuis n'importe quel appareil, protégée par ton login Supabase.

Pour un nom d'URL plus propre, ou une mise à jour automatique à chaque modif du fichier, tu peux aussi connecter Netlify directement à ce repo GitHub (Site settings → Build & deploy → lier le repo, aucune commande de build nécessaire, "Publish directory" = `.`).

## 4. Importer ton réseau LinkedIn

1. Sur LinkedIn : **Paramètres → Confidentialité des données → Obtenir une copie de vos données** → coche "Connexions" → demande l'archive (arrive par email sous quelques minutes, parfois plus).
2. Tu récupères un fichier `Connections.csv`.
3. Dans NetMap, onglet **Excel**, dépose ce fichier.
4. Vérifie le mapping de colonnes proposé (First Name / Last Name sont détectés et fusionnés automatiquement en un nom complet) puis clique **Importer**.
5. Les liens entre tes contacts LinkedIn ne sont pas dans cet export — utilise les règles automatiques "Même entreprise" / "Même cluster" (onglet Liens), ou ajoute des liens manuels un par un.

## Notes

- Sans Supabase configuré, tes données restent dans le navigateur (IndexedDB) — un backup JSON régulier (bouton en bas de page) reste recommandé.
- Avec Supabase configuré, chaque appareil connecté avec le même compte voit les mêmes données (sync automatique ~3s après chaque modif, ou bouton "Sauvegarder").
- Le champ **Sous-catégorie** est libre : mets "UCL" ou "EmLyon" pour un contact du cluster École, ou un secteur ("Finance", "Tech"...) pour un contact Pro.
- Les **notes** (textarea) sont faites pour se souvenir de détails perso : prénom des enfants, anniversaire, comment vous vous êtes rencontrés, etc.
