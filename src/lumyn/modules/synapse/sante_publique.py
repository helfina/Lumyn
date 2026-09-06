"""Établissements FINESS accessibles sans compte via l'API Recherche d'entreprises."""

import json
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lumyn.modules.synapse.entreprises import _convertir_reponse


URL_RECHERCHE = "https://recherche-entreprises.api.gouv.fr/search"


class FournisseurEtablissementsSante:
    """Recherche le sous-ensemble FINESS ; ce n'est pas un annuaire RPPS."""

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
            "est_finess": "true",
            "etat_administratif": "A",
            "page": 1,
            "per_page": self.limite,
            "limite_matching_etablissements": self.limite,
        })
        try:
            charge = self._transport(url, self.timeout)
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError("La recherche FINESS publique n'a pas répondu à temps.") from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError("La recherche publique d'établissements de santé est indisponible.") from erreur
        return _convertir_reponse(charge, self.limite)


def _charger_json(url, timeout):
    requete = Request(url, headers={"User-Agent": "Lumyn/0.0.4"})
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse FINESS inattendue")
        return json.loads(reponse.read().decode("utf-8"))

