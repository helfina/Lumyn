"""Route les recherches vers la source publique adaptée, sans décision automatique."""

import re

from lumyn.modules.synapse.entreprises import FournisseurEntreprises
from lumyn.modules.synapse.geoplateforme import FournisseurGeoplateforme
from lumyn.modules.synapse.sante_publique import FournisseurEtablissementsSante


MOTS_SANTE = {
    "docteur", "dr", "médecin", "medecin", "dentiste", "dermatologue",
    "infirmier", "infirmière", "kine", "kiné", "psychologue", "psy",
    "pharmacie", "hôpital", "hopital", "hospitalier", "hospitalière",
    "hospitaliere", "clinique", "cabinet médical", "centre hospitalier",
    "centre hospitalier universitaire",
}
MOTS_ADRESSE = {
    "rue", "avenue", "boulevard", "route", "impasse", "allée", "allee",
    "place", "chemin", "quai", "cours", "lotissement",
}


class RouteurLieuxPublics:
    """BAN pour les adresses, annuaires dédiés pour les activités."""

    def __init__(self, *, adresses=None, entreprises=None, sante=None):
        self.adresses = adresses or FournisseurGeoplateforme()
        self.entreprises = entreprises or FournisseurEntreprises()
        self.sante = sante if sante is not None else FournisseurEtablissementsSante()

    def autocompleter(self, texte):
        return self.adresses.autocompleter(texte)

    def rechercher(self, texte):
        categorie = classifier_requete(texte)
        if categorie == "sante":
            return self.sante.rechercher(texte) if self.sante is not None else []
        if categorie == "adresse":
            return self.adresses.rechercher(texte)
        return self.entreprises.rechercher(texte)


def classifier_requete(texte):
    normalise = str(texte or "").casefold()
    mots = set(re.findall(r"[\wÀ-ÿ]+", normalise))
    if any(expression in normalise for expression in MOTS_SANTE) or mots & MOTS_SANTE:
        return "sante"
    if re.search(r"\b\d{1,4}\s", normalise) or mots & MOTS_ADRESSE:
        return "adresse"
    return "entreprise"
