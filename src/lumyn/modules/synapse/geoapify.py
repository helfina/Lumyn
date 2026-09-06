"""Adaptateur Geoapify isolé de Synapse et de l'interface Toga."""

import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lumyn.modules.synapse.recherche_lieux import PropositionLieu

SOURCE_GEOAPIFY = "Geoapify / OpenStreetMap"
URL_RECHERCHE = "https://api.geoapify.com/v1/geocode/search"
URL_AUTOCOMPLETE = "https://api.geoapify.com/v1/geocode/autocomplete"


class ErreurConfigurationGeoapify(ValueError):
    """Configuration volontairement activée mais incomplète."""


class FournisseurGeoapify:
    """Recherche structurée bornée ; une requête HTTP vaut un crédit simple."""

    def __init__(self, cle_api=None, *, timeout=6, limite=5, transport=None):
        self.cle_api = str(cle_api or "").strip()
        self.timeout = max(1, min(float(timeout), 15))
        self.limite = max(1, min(int(limite), 5))
        self._transport = transport or _charger_json

    def _cle(self):
        if not self.cle_api:
            raise ErreurConfigurationGeoapify(
                "Geoapify est activé mais GEOAPIFY_API_KEY est absente."
            )
        return self.cle_api

    def rechercher(self, texte):
        return self._requete(URL_RECHERCHE, texte)

    def autocompleter(self, texte):
        return self._requete(URL_AUTOCOMPLETE, texte)

    def _requete(self, endpoint, texte):
        texte = str(texte or "").strip()
        if len(texte) < 3:
            return []
        parametres = {
            "text": texte,
            "format": "json",
            "lang": "fr",
            "bias": "countrycode:fr",
            "limit": self.limite,
            "apiKey": self._cle(),
        }
        url = endpoint + "?" + urlencode(parametres)
        try:
            charge = self._transport(url, self.timeout)
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError("Geoapify n'a pas répondu dans le délai prévu.") from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError("La recherche Geoapify est indisponible.") from erreur
        return _convertir_reponse(charge, self.limite)


def _charger_json(url, timeout):
    requete = Request(url, headers={"User-Agent": "Lumyn/0.0.4"})
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse Geoapify inattendue")
        return json.loads(reponse.read().decode("utf-8"))


def _convertir_reponse(charge, limite):
    if not isinstance(charge, dict) or not isinstance(charge.get("results"), list):
        raise ValueError("Réponse Geoapify invalide.")
    propositions = []
    vus = set()
    for resultat in charge["results"]:
        if not isinstance(resultat, dict):
            continue
        nom = str(resultat.get("name") or resultat.get("address_line1") or "").strip()
        adresse = str(resultat.get("formatted") or "").strip()
        if not nom or not adresse:
            continue
        ville = str(resultat.get("city") or resultat.get("town") or
                    resultat.get("village") or resultat.get("municipality") or "").strip()
        categorie = resultat.get("category") or resultat.get("result_type") or ""
        if isinstance(categorie, list):
            categorie = ", ".join(str(v) for v in categorie[:2])
        profession = str(categorie).replace(".", " · ").strip()
        identifiant = str(resultat.get("place_id") or "").strip()
        cle = (nom.casefold(), adresse.casefold())
        if cle in vus:
            continue
        vus.add(cle)
        propositions.append(PropositionLieu(
            nom=nom,
            adresse=adresse,
            source=SOURCE_GEOAPIFY,
            profession=profession,
            ville=ville,
            identifiant=identifiant,
            conservation_autorisee=False,
        ))
        if len(propositions) >= limite:
            break
    return propositions


def fournisseur_geoapify_depuis_environnement(environ=None):
    """Active Geoapify avec la clé, ou avec LUMYN_GEOAPIFY=1 pour signaler son absence."""
    environ = os.environ if environ is None else environ
    activation = str(environ.get("LUMYN_GEOAPIFY", "")).strip().casefold()
    if activation in {"0", "false", "non", "off"}:
        return None
    cle = str(environ.get("GEOAPIFY_API_KEY", "")).strip()
    if not cle and activation not in {"1", "true", "oui", "on"}:
        return None
    return FournisseurGeoapify(cle)
