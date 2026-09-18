#!/usr/bin/env python3
"""Genere une page HTML locale avec un bouton par contact.
Chaque bouton ouvre le client mail par defaut avec destinataire, objet et
corps deja remplis (limite du protocole mailto: aucune piece jointe possible,
il faut joindre le CV manuellement dans le client mail).

Usage:
    python generate_mailto_page.py --csv data/contacts.csv --template templates/message.txt \
        --subject "Objet - $entreprise" --out emails.html
"""

import argparse
import html
from urllib.parse import quote

from send_emails import build_message, load_contacts


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Emails a envoyer</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; max-width: 900px; margin: 24px auto; padding: 0 16px; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }}
  .note {{ background: #fff8e1; border: 1px solid #f0d060; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; }}
  .contact {{ border: 1px solid #ddd; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }}
  .contact.guess {{ border-color: #e0a800; background: #fffdf5; }}
  .info {{ flex: 1; }}
  .info .entreprise {{ font-weight: 600; }}
  .info .nom {{ color: #444; }}
  .info .email {{ color: #777; font-size: 0.85rem; }}
  .flag {{ color: #b36b00; font-size: 0.8rem; font-weight: 600; }}
  a.btn {{ background: #0a66c2; color: white; padding: 10px 18px; border-radius: 6px; text-decoration: none; font-weight: 600; white-space: nowrap; }}
  a.btn:hover {{ background: #084e96; }}
</style>
</head>
<body>
<h1>{count} emails prets a envoyer</h1>
<div class="note">
  En cliquant sur "Ouvrir le mail", ton client mail par defaut s'ouvre avec le destinataire,
  l'objet et le texte deja remplis. <strong>Pense a joindre ton CV manuellement</strong> avant
  d'envoyer (impossible de le faire automatiquement via un lien).
</div>
{rows}
</body>
</html>
"""

ROW_TEMPLATE = """<div class="contact{extra_class}">
  <div class="info">
    <div class="entreprise">{entreprise}</div>
    <div class="nom">{nom} — {poste}</div>
    <div class="email">{email}{flag}</div>
  </div>
  <a class="btn" href="{mailto}">Ouvrir le mail</a>
</div>
"""


def build_mailto(to_addr, subject, body):
    return f"mailto:{quote(to_addr)}?subject={quote(subject)}&body={quote(body)}"


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

    rows = []
    for contact in contacts:
        if not contact.get("civilite"):
            contact["civilite"] = "Madame/Monsieur"
        subject, body = build_message(template_text, args.subject, contact)
        is_guess = contact.get("email_devine", "").startswith("OUI")
        rows.append(ROW_TEMPLATE.format(
            extra_class=" guess" if is_guess else "",
            entreprise=html.escape(contact.get("entreprise", "")),
            nom=html.escape(contact.get("nom", "")),
            poste=html.escape(contact.get("poste", "")),
            email=html.escape(contact["email"]),
            flag=" &mdash; <span class=\"flag\">email devine, a verifier</span>" if is_guess else "",
            mailto=build_mailto(contact["email"], subject, body),
        ))

    page = PAGE_TEMPLATE.format(count=len(contacts), rows="\n".join(rows))
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"{len(contacts)} bouton(s) genere(s) -> {args.out}")


if __name__ == "__main__":
    main()
