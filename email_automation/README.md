# Envoi d'emails personnalises (mail merge)

Script pour envoyer un email personnalise par entreprise a partir d'un fichier CSV.

## 1. Preparer le CSV

Colonnes obligatoires : `email`, `entreprise`. Ajoutez les colonnes que vous voulez
utiliser dans le message (`nom`, `poste`, etc.). Voir `data/contacts.example.csv`.

## 2. Ecrire le modele de message

Editez `templates/message.txt`. Utilisez `$nom_colonne` pour inserer une valeur du CSV
(ex: `$entreprise`, `$nom`). L'objet de l'email peut aussi contenir des placeholders.

## 3. Tester en dry-run (aucun envoi)

```bash
python send_emails.py --csv data/contacts.csv --template templates/message.txt \
  --subject "A propos de \$entreprise"
```

Verifiez l'apercu affiche pour chaque contact.

## 4. Configurer les identifiants Outlook/Office365

```bash
export OUTLOOK_EMAIL="votre.adresse@outlook.com"
export OUTLOOK_PASSWORD="votre_mot_de_passe_ou_mdp_application"
```

Si l'authentification a deux facteurs est activee, utilisez un
"mot de passe d'application" genere dans les parametres de securite du compte.

## 5. Envoyer reellement

```bash
python send_emails.py --csv data/contacts.csv --template templates/message.txt \
  --subject "A propos de \$entreprise" --send
```
