"""Analyse des phrases de rendez-vous saisies dans Lumyn."""

import re
from datetime import date, timedelta

from lumyn.modules.rendez_vous.modele import creer_modele_rendez_vous


JOURS = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}

NOMS_JOURS = [
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche",
]

MOIS = {
    "janvier": 1,
    "février": 2,
    "fevrier": 2,
    "mars": 3,
    "avril": 4,
    "mai": 5,
    "juin": 6,
    "juillet": 7,
    "août": 8,
    "aout": 8,
    "septembre": 9,
    "octobre": 10,
    "novembre": 11,
    "décembre": 12,
    "decembre": 12,
}


def calculer_annee(jour, mois, annee=None):
    """Choisit l'année indiquée ou la prochaine date future."""

    aujourd_hui = date.today()

    if annee is not None:
        return annee

    date_possible = date(aujourd_hui.year, mois, jour)

    if date_possible < aujourd_hui:
        return aujourd_hui.year + 1

    return aujourd_hui.year


def extraire_heure(texte, rendez_vous):
    """Extrait une heure comme 14h30, 14 h 30 ou 14:30."""

    motif = r"\b([01]?\d|2[0-3])\s*(?:h|:)\s*([0-5]\d)?\b"
    resultat = re.search(motif, texte, flags=re.IGNORECASE)

    if not resultat:
        return texte

    heures = int(resultat.group(1))
    minutes = int(resultat.group(2) or 0)

    if minutes:
        rendez_vous["heure"] = f"{heures:02d}h{minutes:02d}"
    else:
        rendez_vous["heure"] = f"{heures:02d}h"

    return texte[: resultat.start()] + " " + texte[resultat.end() :]


def extraire_jour_ecrit(texte):
    """Recherche un jour explicitement écrit dans la phrase."""

    for nom_jour, numero in JOURS.items():
        if re.search(rf"\b{nom_jour}\b", texte, flags=re.IGNORECASE):
            return nom_jour, numero

    return None, None


def extraire_date_relative(texte, rendez_vous):
    """Reconnaît aujourd'hui, demain et après-demain."""

    aujourd_hui = date.today()

    expressions = [
        (r"\baujourd['’]hui\b", 0),
        (r"\baprès[- ]demain\b", 2),
        (r"\bapres[- ]demain\b", 2),
        (r"\bdemain\b", 1),
    ]

    for motif, decalage in expressions:
        resultat = re.search(motif, texte, flags=re.IGNORECASE)

        if resultat:
            rendez_vous["date"] = aujourd_hui + timedelta(days=decalage)

            return texte[: resultat.start()] + " " + texte[resultat.end() :]

    return texte


def extraire_date_numerique(texte, rendez_vous):
    """Reconnaît 18/08, 18-08, 18.08 ou 18/08/2026."""

    motif = r"\b(0?[1-9]|[12]\d|3[01])[/.-](0?[1-9]|1[0-2])(?:[/.-](\d{4}))?\b"
    resultat = re.search(motif, texte)

    if not resultat:
        return texte

    jour = int(resultat.group(1))
    mois = int(resultat.group(2))
    annee_ecrite = int(resultat.group(3)) if resultat.group(3) else None

    try:
        annee = calculer_annee(jour, mois, annee_ecrite)
        rendez_vous["date"] = date(annee, mois, jour)
    except ValueError:
        rendez_vous["erreurs"].append(
            f"La date {resultat.group(0)} n'existe pas."
        )

    return texte[: resultat.start()] + " " + texte[resultat.end() :]


def extraire_date_ecrite(texte, rendez_vous):
    """Reconnaît une date comme 18 août ou 18 août 2027."""

    noms_mois = "|".join(MOIS.keys())

    motif = (
        rf"\b(0?[1-9]|[12]\d|3[01])\s+"
        rf"({noms_mois})"
        rf"(?:\s+(\d{{4}}))?\b"
    )

    resultat = re.search(motif, texte, flags=re.IGNORECASE)

    if not resultat:
        return texte

    jour = int(resultat.group(1))
    mois = MOIS[resultat.group(2).lower()]
    annee_ecrite = int(resultat.group(3)) if resultat.group(3) else None

    try:
        annee = calculer_annee(jour, mois, annee_ecrite)
        rendez_vous["date"] = date(annee, mois, jour)
    except ValueError:
        rendez_vous["erreurs"].append(
            f"La date {resultat.group(0)} n'existe pas."
        )

    return texte[: resultat.start()] + " " + texte[resultat.end() :]


def calculer_date_depuis_jour(numero_jour):
    """Calcule la prochaine date correspondant au jour demandé."""

    aujourd_hui = date.today()

    jours_a_ajouter = (numero_jour - aujourd_hui.weekday()) % 7

    # « mardi » signifie le prochain mardi, pas aujourd'hui.
    if jours_a_ajouter == 0:
        jours_a_ajouter = 7

    return aujourd_hui + timedelta(days=jours_a_ajouter)


def extraire_date(texte, rendez_vous):
    """Détermine une date réelle à partir de la phrase."""

    jour_ecrit, numero_jour_ecrit = extraire_jour_ecrit(texte)

    if jour_ecrit:
        rendez_vous["jour_saisi"] = jour_ecrit.capitalize()

    # Priorité à une date précise.
    texte = extraire_date_numerique(texte, rendez_vous)

    if rendez_vous["date"] is None:
        texte = extraire_date_ecrite(texte, rendez_vous)

    if rendez_vous["date"] is None:
        texte = extraire_date_relative(texte, rendez_vous)

    # S'il n'existe aucune autre date, utiliser le jour écrit.
    if rendez_vous["date"] is None and numero_jour_ecrit is not None:
        rendez_vous["date"] = calculer_date_depuis_jour(numero_jour_ecrit)

    if rendez_vous["date"] is not None:
        jour_calcule = NOMS_JOURS[rendez_vous["date"].weekday()]
        rendez_vous["jour_calcule"] = jour_calcule

        # Vérifier une éventuelle contradiction.
        if (
            jour_ecrit is not None
            and JOURS[jour_ecrit] != rendez_vous["date"].weekday()
        ):
            rendez_vous["erreurs"].append(
                f"Tu as écrit {jour_ecrit.capitalize()}, "
                f"mais le {rendez_vous['date'].strftime('%d/%m/%Y')} "
                f"tombe un {jour_calcule}."
            )

    # Retirer le jour écrit du futur titre.
    if jour_ecrit:
        texte = re.sub(
            rf"\b{jour_ecrit}\b(?:\s+prochain)?",
            " ",
            texte,
            flags=re.IGNORECASE,
        )

    return texte


def extraire_titre(texte, rendez_vous):
    """Construit le titre avec le texte restant."""

    # Retirer les petits mots liés à la date et à l'heure.
    texte = re.sub(r"\b(le|à|a)\b", " ", texte, flags=re.IGNORECASE)
    texte = re.sub(r"\s+", " ", texte).strip(" ,.-")

    if texte:
        rendez_vous["titre"] = texte.capitalize()


def analyser_rendez_vous(texte):
    """Analyse une phrase et retourne un rendez-vous structuré."""

    rendez_vous = creer_modele_rendez_vous()
    texte_restant = texte.strip()

    texte_restant = extraire_heure(texte_restant, rendez_vous)
    texte_restant = extraire_date(texte_restant, rendez_vous)
    extraire_titre(texte_restant, rendez_vous)

    if not rendez_vous["titre"]:
        rendez_vous["manquants"].append("le titre")

    if not rendez_vous["date"]:
        rendez_vous["manquants"].append("la date")

    if not rendez_vous["heure"]:
        rendez_vous["manquants"].append("l'heure")

    return rendez_vous