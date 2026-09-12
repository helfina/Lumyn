"""Recherche d'établissements via l'API publique de l'Annuaire des Entreprises."""

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lumyn.modules.synapse.recherche_lieux import PropositionLieu


SOURCE_ENTREPRISES = "API Recherche d’entreprises / données publiques SIRENE"
URL_RECHERCHE = "https://recherche-entreprises.api.gouv.fr/search"


class FournisseurEntreprises:
    """Retourne uniquement des établissements publics diffusibles, sans authentification."""

    def __init__(self, *, timeout=6, limite=5, transport=None):
        self.timeout = max(1, min(float(timeout), 15))
        self.limite = max(1, min(int(limite), 5))
        self._transport = transport or _charger_json

    def rechercher(self, texte):
        texte = str(texte or "").strip()
        if len(texte) < 3:
            return []
        url = URL_RECHERCHE + "?" + urlencode({
            "q": texte,
            "page": 1,
            "per_page": self.limite,
            "limite_matching_etablissements": self.limite,
        })
        try:
            charge = self._transport(url, self.timeout)
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError("L'API Recherche d'entreprises n'a pas répondu à temps.") from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError("La recherche publique d'entreprises est indisponible.") from erreur
        return _convertir_reponse(charge, self.limite)


def _charger_json(url, timeout):
    requete = Request(url, headers={"User-Agent": "Lumyn/0.0.4"})
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse API Recherche d'entreprises inattendue")
        return json.loads(reponse.read().decode("utf-8"))


def _convertir_reponse(charge, limite, *, source=SOURCE_ENTREPRISES):
    if not isinstance(charge, dict) or not isinstance(charge.get("results"), list):
        raise ValueError("Réponse API Recherche d'entreprises invalide.")
    propositions = []
    vus = set()
    for entreprise in charge["results"]:
        if not isinstance(entreprise, dict):
            continue
        nom = str(entreprise.get("nom_complet") or entreprise.get("nom_raison_sociale") or "").strip()
        correspondances = entreprise.get("matching_etablissements")
        etablissements = list(correspondances) if isinstance(correspondances, list) else []
        siege = entreprise.get("siege")
        if isinstance(siege, dict):
            etablissements.append(siege)
        for etablissement in etablissements:
            if not isinstance(etablissement, dict) or etablissement.get("etat_administratif") == "F":
                continue
            adresse = str(etablissement.get("adresse") or etablissement.get("geo_adresse") or "").strip()
            ville = str(etablissement.get("libelle_commune") or "").strip()
            siret = str(etablissement.get("siret") or "").strip()
            cle = (nom.casefold(), adresse.casefold())
            if not nom or not adresse or cle in vus:
                continue
            vus.add(cle)
            propositions.append(PropositionLieu(
                nom=nom,
                adresse=adresse,
                source=source,
                profession=str(etablissement.get("activite_principale") or "").strip(),
                ville=ville,
                identifiant=siret,
                conservation_autorisee=True,
            ))
            if len(propositions) >= limite:
                return propositions
    return propositions
