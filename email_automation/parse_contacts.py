#!/usr/bin/env python3
"""Extrait les contacts d'un fichier Excel de prospection et produit un CSV
pret pour send_emails.py.

Format attendu dans les colonnes 'Contact public' / 'Contact public2' :
    "Prenom Nom - Poste - email@domaine.com"
ou, sans email connu :
    "Prenom Nom"

Pour les contacts nommes sans email, le script deduit une adresse probable
a partir du format utilise par d'autres personnes de la meme entreprise
dans le fichier (ex: prenom.nom@domaine.com). Ces emails devines sont
marques email_devine=OUI et DOIVENT etre verifies avant tout envoi.

Usage:
    python parse_contacts.py --xlsx "fichier.xlsx" --out data/contacts.csv
"""

import argparse
import csv
import re
import unicodedata
from collections import Counter

import gender_guesser.detector as gender
import pandas as pd

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-']+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

CONTACT_COLUMNS = ["Contact public", "Contact public2"]

_gender_detector = gender.Detector()


def guess_civilite(prenom):
    """Renvoie 'Monsieur', 'Madame' ou '' (incertain, a completer manuellement)."""
    if not prenom:
        return ""
    ascii_prenom = unicodedata.normalize("NFKD", prenom).encode("ascii", "ignore").decode()
    result = _gender_detector.get_gender(ascii_prenom)
    if result in ("male", "mostly_male"):
        return "Monsieur"
    if result in ("female", "mostly_female"):
        return "Madame"
    return ""


def strip_accents(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


def parse_contact_field(raw):
    """Renvoie (nom, poste, email_ou_None)."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    match = EMAIL_RE.search(raw)
    if match:
        email = match.group(0)
        prefix = raw[: match.start()]
    else:
        email = None
        prefix = raw
    parts = [p.strip(" -") for p in prefix.split(" - ") if p.strip(" -")]
    nom = parts[0] if len(parts) >= 1 else ""
    poste = parts[1] if len(parts) >= 2 else ""
    return nom, poste, email


def guess_email(prenom, nom_famille, domain_pattern):
    """Construit une adresse probable a partir du gabarit ('{p}.{n}' ou similaire)."""
    p = strip_accents(prenom).lower().replace(" ", "").replace("-", "")
    n = strip_accents(nom_famille).lower().replace(" ", "-")
    local_part, domain = domain_pattern
    local = local_part.format(p=p, n=n)
    return f"{local}@{domain}"


def detect_domain_pattern(emails_for_org):
    """A partir d'emails connus d'une meme entreprise, deduit (gabarit, domaine)."""
    domains = Counter(e.split("@")[1] for e in emails_for_org)
    domain = domains.most_common(1)[0][0]
    patterns = Counter()
    for e in emails_for_org:
        local, d = e.split("@")
        if d != domain:
            continue
        if "." in local:
            patterns["{p}.{n}"] += 1
        else:
            patterns["other"] += 1
    if not patterns or patterns.most_common(1)[0][0] == "other":
        return None
    return "{p}.{n}", domain


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xlsx", required=True, help="Fichier Excel source")
    parser.add_argument("--out", required=True, help="CSV de sortie")
    args = parser.parse_args()

    xls = pd.ExcelFile(args.xlsx)
    raw_rows = []

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
                raw_rows.append({
                    "nom": nom,
                    "poste": poste or row.get("Fonction", ""),
                    "email": email,
                    "entreprise": row.get("Organisation", ""),
                    "secteur": row.get("Sous-secteur / équipe cible", ""),
                    "pourquoi_pertinent": row.get("Pourquoi pertinent", ""),
                    "priorite": row.get("Priorité", ""),
                    "feuille": sheet,
                })

    # Domaine/gabarit d'email connu par entreprise, a partir des emails reels trouves
    emails_by_org = {}
    for r in raw_rows:
        if r["email"]:
            emails_by_org.setdefault(r["entreprise"], []).append(r["email"])
    pattern_by_org = {org: detect_domain_pattern(emails) for org, emails in emails_by_org.items()}

    def find_pattern_for(entreprise):
        if entreprise in pattern_by_org:
            return pattern_by_org[entreprise]
        # Match par marque commune (ex: "BNP Paribas CIB" et "BNP Paribas Wealth
        # Management" partagent le meme domaine) : deux premiers mots communs.
        target_words = entreprise.split()[:2]
        for org, pattern in pattern_by_org.items():
            if pattern and org.split()[:2] == target_words:
                return pattern
        return None

    rows = []
    seen_emails = set()
    guessed_count = 0
    unresolved = []

    for r in raw_rows:
        nom = r["nom"]
        name_parts = nom.split()
        prenom = name_parts[0] if name_parts else ""
        nom_famille = " ".join(name_parts[1:]) if len(name_parts) >= 2 else ""

        email = r["email"]
        email_devine = "NON"
        if not email:
            pattern = find_pattern_for(r["entreprise"])
            if pattern and prenom and nom_famille:
                email = guess_email(prenom, nom_famille, pattern)
                email_devine = "OUI - A VERIFIER AVANT ENVOI"
                guessed_count += 1
            else:
                unresolved.append(f"{nom} ({r['entreprise']})")
                continue

        email_key = email.lower()
        if email_key in seen_emails:
            continue
        seen_emails.add(email_key)

        rows.append({
            "email": email,
            "email_devine": email_devine,
            "entreprise": r["entreprise"],
            "nom": nom,
            "prenom": prenom,
            "nom_famille": nom_famille,
            "civilite": guess_civilite(prenom),
            "poste": r["poste"],
            "secteur": r["secteur"],
            "pourquoi_pertinent": r["pourquoi_pertinent"],
            "priorite": r["priorite"],
            "feuille": r["feuille"],
        })

    fieldnames = ["email", "email_devine", "entreprise", "nom", "prenom", "nom_famille", "civilite", "poste", "secteur", "pourquoi_pertinent", "priorite", "feuille"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    uncertain_civilite = [r["nom"] for r in rows if not r["civilite"]]
    print(f"{len(rows)} contact(s) au total -> {args.out}")
    print(f"  dont {guessed_count} email(s) DEVINE(S) a partir du format de l'entreprise (a verifier avant envoi)")
    if uncertain_civilite:
        print(f"\nCivilite incertaine pour {len(uncertain_civilite)} contact(s), a completer manuellement :")
        for n in uncertain_civilite:
            print(f"  - {n}")
    if unresolved:
        print(f"\n{len(unresolved)} contact(s) nomme(s) sans email et sans format d'entreprise connu (aucune autre adresse @cette-entreprise dans le fichier) :")
        for n in unresolved:
            print(f"  - {n}")


if __name__ == "__main__":
    main()
