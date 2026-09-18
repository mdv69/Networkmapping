#!/usr/bin/env python3
"""Genere un fichier texte avec un email pret a copier-coller par contact.

Usage:
    python generate_ready_to_send.py --csv data/contacts.csv --template templates/message.txt \
        --subject "Objet - $entreprise" --out emails_pret_a_envoyer.txt
"""

import argparse

from send_emails import build_message, load_contacts


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    contacts = load_contacts(args.csv)
    with open(args.template, encoding="utf-8") as f:
        template_text = f.read()

    lines = [f"{len(contacts)} emails prets a envoyer manuellement - n'oublie pas de joindre ton CV a chaque envoi.\n"]

    for i, contact in enumerate(contacts, start=1):
        if not contact.get("civilite"):
            contact["civilite"] = "[VERIFIER Monsieur/Madame]"
        subject, body = build_message(template_text, args.subject, contact)
        lines.append("=" * 70)
        lines.append(f"[{i}/{len(contacts)}] {contact.get('entreprise', '')} - {contact.get('nom', '')}")
        email_line = f"A : {contact['email']}"
        if contact.get("email_devine", "").startswith("OUI"):
            email_line += "   >>> EMAIL DEVINE, A VERIFIER AVANT ENVOI <<<"
        lines.append(email_line)
        lines.append(f"Objet : {subject}")
        lines.append("-" * 70)
        lines.append(body)
        lines.append("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"{len(contacts)} email(s) generes -> {args.out}")


if __name__ == "__main__":
    main()
