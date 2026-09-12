"""Administrations via l'annuaire officiel Service-Public.gouv.fr / DILA."""

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lumyn.modules.synapse.recherche_lieux import PropositionLieu


SOURCE_ADMINISTRATION = (
    "Service-Public.gouv.fr / DILA — Annuaire de l'administration"
)
URL_RECHERCHE = (
    "https://api-lannuaire.service-public.fr/api/explore/v2.1/catalog/"
    "datasets/api-lannuaire-administration/records"
)


class FournisseurAdministration:
    """Recherche des guichets publics sans compte ni authentification."""

    def __init__(self, *, timeout=6, limite=5, transport=None):
        self.timeout = max(1, min(float(timeout), 15))
        self.limite = max(1, min(int(limite), 5))
        self._transport = transport or _charger_json

    def rechercher(self, texte):
        texte = str(texte or "").strip()
        if len(texte) < 3:
            return []
        recherche = f"search(*, {json.dumps(texte, ensure_ascii=False)})"
        url = URL_RECHERCHE + "?" + urlencode({
            "where": recherche,
            "limit": self.limite,
        })
        try:
            charge = self._transport(url, self.timeout)
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError(
                "L'annuaire de l'administration n'a pas répondu à temps."
            ) from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError(
                "L'annuaire public de l'administration est indisponible."
            ) from erreur
        return _convertir_reponse(charge, self.limite)


def _charger_json(url, timeout):
    requete = Request(url, headers={"User-Agent": "Lumyn/0.0.4"})
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse de l'annuaire de l'administration inattendue")
        return json.loads(reponse.read().decode("utf-8"))


def _adresses_en_liste(valeur):
    if isinstance(valeur, str):
        try:
            valeur = json.loads(valeur)
        except (TypeError, ValueError):
            return []
    return valeur if isinstance(valeur, list) else []


def _formater_adresse(adresse):
    if not isinstance(adresse, dict):
        return "", ""
    if str(adresse.get("type_adresse") or "").casefold() != "adresse":
        return "", ""
    voie = " ".join(str(adresse.get(cle) or "").strip() for cle in (
        "complement1", "complement2", "numero_voie", "service_distribution"
    )).strip()
    code_postal = str(adresse.get("code_postal") or "").strip()
    ville = str(adresse.get("nom_commune") or "").strip()
    localite = " ".join(partie for partie in (code_postal, ville) if partie)
    texte = ", ".join(partie for partie in (voie, localite) if partie)
    return texte, ville


def _convertir_reponse(charge, limite):
    if not isinstance(charge, dict) or not isinstance(charge.get("results"), list):
        raise ValueError("Réponse de l'annuaire de l'administration invalide.")
    propositions = []
    vus = set()
    for organisme in charge["results"]:
        if not isinstance(organisme, dict):
            continue
        nom = str(organisme.get("nom") or "").strip()
        identifiant = str(organisme.get("id") or "").strip()
        for adresse_brute in _adresses_en_liste(organisme.get("adresse")):
            adresse, ville = _formater_adresse(adresse_brute)
            cle = (nom.casefold(), adresse.casefold())
            if not nom or not adresse or cle in vus:
                continue
            vus.add(cle)
            propositions.append(PropositionLieu(
                nom=nom,
                adresse=adresse,
                source=SOURCE_ADMINISTRATION,
                ville=ville,
                identifiant=identifiant,
                conservation_autorisee=True,
                adresse_verifiee=False,
            ))
            if len(propositions) >= limite:
                return propositions
    return propositions
