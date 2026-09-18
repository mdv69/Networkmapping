#!/usr/bin/env python3
"""Extrait les contacts avec email d'un fichier Excel de prospection
et produit un CSV pret pour send_emails.py.

Format attendu dans les colonnes 'Contact public' / 'Contact public2' :
    "Prenom Nom - Poste - email@domaine.com"
Les lignes sans email (contact public sans adresse connue) sont ignorees.

Usage:
    python parse_contacts.py --xlsx "fichier.xlsx" --out data/contacts.csv
"""

import argparse
import csv
import re

import pandas as pd

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-']+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

CONTACT_COLUMNS = ["Contact public", "Contact public2"]


def parse_contact_field(raw):
    """Renvoie (nom, poste, email) ou None si pas d'email trouve."""
    if not isinstance(raw, str):
        return None
    match = EMAIL_RE.search(raw)
    if not match:
        return None
    email = match.group(0)
    prefix = raw[: match.start()]
    parts = [p.strip(" -") for p in prefix.split(" - ") if p.strip(" -")]
    nom = parts[0] if len(parts) >= 1 else ""
    poste = parts[1] if len(parts) >= 2 else ""
    return nom, poste, email


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xlsx", required=True, help="Fichier Excel source")
    parser.add_argument("--out", required=True, help="CSV de sortie")
    args = parser.parse_args()

    xls = pd.ExcelFile(args.xlsx)
    rows = []
    seen_emails = set()

    for sheet in xls.sheet_names:
        if sheet.startswith("00"):
            continue
        df = pd.read_excel(args.xlsx, sheet_name=sheet)
        for _, row in df.iterrows():
            for col in CONTACT_COLUMNS:
                if col not in df.columns:
                    continue
                parsed = parse_contact_field(row.get(col))
                if not parsed:
                    continue
                nom, poste, email = parsed
                email_key = email.lower()
                if email_key in seen_emails:
                    continue
                seen_emails.add(email_key)
                rows.append({
                    "email": email,
                    "entreprise": row.get("Organisation", ""),
                    "nom": nom,
                    "prenom": nom.split()[0] if nom else "",
                    "poste": poste or row.get("Fonction", ""),
                    "secteur": row.get("Sous-secteur / équipe cible", ""),
                    "pourquoi_pertinent": row.get("Pourquoi pertinent", ""),
                    "priorite": row.get("Priorité", ""),
                    "feuille": sheet,
                })

    fieldnames = ["email", "entreprise", "nom", "prenom", "poste", "secteur", "pourquoi_pertinent", "priorite", "feuille"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{len(rows)} contact(s) avec email extrait(s) -> {args.out}")


if __name__ == "__main__":
    main()
