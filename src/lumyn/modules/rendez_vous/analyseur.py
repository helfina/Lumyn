"""Analyse des phrases de rendez-vous saisies dans Lumyn."""


def analyser_rendez_vous(texte):
    """Extrait le titre, le jour et l'heure d'une saisie simple."""

    jours = [
        "lundi",
        "mardi",
        "mercredi",
        "jeudi",
        "vendredi",
        "samedi",
        "dimanche",
    ]

    mots = texte.lower().split()

    jour = None
    heure = None
    mots_du_titre = []

    for mot in mots:
        if mot in jours:
            jour = mot.capitalize()
        elif "h" in mot and mot.replace("h", "").isdigit():
            heure = mot
        else:
            mots_du_titre.append(mot)

    titre = " ".join(mots_du_titre).capitalize()

    return titre, jour, heure