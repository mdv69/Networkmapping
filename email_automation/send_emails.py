#!/usr/bin/env python3
"""Mail merge: envoie un email personnalise par entreprise via SMTP Office365.

Usage:
    python send_emails.py --csv data/contacts.csv --template templates/message.txt --subject "Objet" [--send]

Sans --send, le script fonctionne en mode "dry-run" : il affiche les emails
qui seraient envoyes sans rien envoyer reellement.

Variables d'environnement requises pour l'envoi reel :
    OUTLOOK_EMAIL      adresse d'envoi (ex: toi@outlook.com)
    OUTLOOK_PASSWORD   mot de passe (ou mot de passe d'application)

Format du CSV attendu (en-tetes obligatoires : email, entreprise) :
    email,entreprise,nom,poste
    contact@acme.com,Acme,Jean Dupont,Responsable RH
"""

import argparse
import csv
import os
import smtplib
import sys
from email.message import EmailMessage
from string import Template

SMTP_HOST = "smtp.office365.com"
SMTP_PORT = 587


def load_contacts(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "email" not in reader.fieldnames or "entreprise" not in reader.fieldnames:
            raise ValueError("Le CSV doit contenir au minimum les colonnes 'email' et 'entreprise'")
        return list(reader)


def build_message(template_text, subject_template, contact):
    body = Template(template_text).safe_substitute(contact)
    subject = Template(subject_template).safe_substitute(contact)
    return subject, body


def send_email(smtp, from_addr, to_addr, subject, body):
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body)
    smtp.send_message(msg)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", required=True, help="Chemin du fichier CSV des contacts")
    parser.add_argument("--template", required=True, help="Chemin du fichier texte modele (placeholders $entreprise, $nom, ...)")
    parser.add_argument("--subject", required=True, help="Objet de l'email (peut contenir des placeholders, ex: 'Proposition pour $entreprise')")
    parser.add_argument("--send", action="store_true", help="Envoie reellement les emails (sinon dry-run)")
    args = parser.parse_args()

    contacts = load_contacts(args.csv)
    with open(args.template, encoding="utf-8") as f:
        template_text = f.read()

    if not args.send:
        print(f"[DRY RUN] {len(contacts)} email(s) seraient envoyes :\n")
        for contact in contacts:
            subject, body = build_message(template_text, args.subject, contact)
            print("=" * 60)
            print(f"A: {contact['email']}")
            print(f"Objet: {subject}")
            print("-" * 60)
            print(body)
        print("\nAucun email envoye (mode dry-run). Relance avec --send pour envoyer reellement.")
        return

    from_addr = os.environ.get("OUTLOOK_EMAIL")
    password = os.environ.get("OUTLOOK_PASSWORD")
    if not from_addr or not password:
        sys.exit("Erreur : definis les variables d'environnement OUTLOOK_EMAIL et OUTLOOK_PASSWORD avant d'utiliser --send")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(from_addr, password)
        for contact in contacts:
            subject, body = build_message(template_text, args.subject, contact)
            send_email(smtp, from_addr, contact["email"], subject, body)
            print(f"Envoye a {contact['email']} ({contact.get('entreprise', '')})")

    print(f"\n{len(contacts)} email(s) envoye(s) avec succes.")


if __name__ == "__main__":
    main()
