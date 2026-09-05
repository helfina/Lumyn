"""Logique métier du carnet de lieux de Lumyn."""

import re
import unicodedata

from lumyn.modules.lieux.stockage import charger_lieux


ALIAS_MAISON = {
    "maison",
    "domicile",
    "chez moi",
}


def normaliser_recherche(texte):
    """Normalise un texte pour faciliter les recherches dans le carnet."""

    if not texte:
        return ""

    texte = unicodedata.normalize("NFKD", str(texte))
    texte = "".join(
        caractere
        for caractere in texte
        if not unicodedata.combining(caractere)
    )

    texte = texte.casefold()
    texte = re.sub(r"\s+", " ", texte)

    return texte.strip()


def termes_lieu(lieu):
    """Retourne le nom et les alias normalisés d'une fiche."""

    termes = []

    nom = normaliser_recherche(lieu.get("nom"))

    if nom:
        termes.append(nom)

    for alias in lieu.get("alias") or []:
        alias_normalise = normaliser_recherche(alias)

        if alias_normalise and alias_normalise not in termes:
            termes.append(alias_normalise)

    return termes


def rechercher_lieux(texte, lieux=None):
    """Recherche des fiches par nom ou alias.

    Les correspondances exactes sont proposées avant les correspondances
    partielles.
    """

    recherche = normaliser_recherche(texte)

    if not recherche:
        return []

    if lieux is None:
        lieux = charger_lieux()

    correspondances_exactes = []
    correspondances_partielles = []

    for lieu in lieux:
        termes = termes_lieu(lieu)

        if recherche in termes:
            correspondances_exactes.append(lieu)
            continue

        if any(recherche in terme for terme in termes):
            correspondances_partielles.append(lieu)

    return correspondances_exactes + correspondances_partielles


def obtenir_adresse_favorite(lieu):
    """Retourne l'adresse favorite d'une fiche.

    Si une fiche ne contient qu'une seule adresse exploitable, cette adresse
    est utilisée même si elle n'est pas explicitement marquée favorite.

    Retourne None lorsqu'aucune adresse ne peut être choisie sans ambiguïté.
    """

    adresses = [
        adresse
        for adresse in (lieu.get("adresses") or [])
        if isinstance(adresse, dict) and adresse.get("adresse")
    ]

    favorites = [
        adresse
        for adresse in adresses
        if adresse.get("favorite") is True
    ]

    if len(favorites) == 1:
        return favorites[0]

    if len(favorites) > 1:
        return None

    if len(adresses) == 1:
        return adresses[0]

    return None


def est_fiche_maison(lieu):
    """Indique si une fiche représente le domicile de l'utilisateur."""

    termes = set(termes_lieu(lieu))

    return bool(termes & ALIAS_MAISON)


def trouver_maison(lieux=None):
    """Recherche l'unique fiche représentant Maison/Domicile/Chez moi."""

    if lieux is None:
        lieux = charger_lieux()

    maisons = [
        lieu
        for lieu in lieux
        if est_fiche_maison(lieu)
    ]

    if len(maisons) == 1:
        return maisons[0]

    return None
