"""Adresses françaises via les API publiques actuelles de la Géoplateforme."""

import json
import socket
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from lumyn.modules.synapse.recherche_lieux import PropositionLieu


SOURCE_BAN = "Géoplateforme / Base Adresse Nationale — Licence Ouverte 2.0"
URL_RECHERCHE = "https://data.geopf.fr/geocodage/search"
URL_AUTOCOMPLETION = "https://data.geopf.fr/geocodage/completion/"


class FournisseurGeoplateforme:
    """Géocode et complète des adresses BAN, sans compte ni clé API."""

    def __init__(self, *, timeout=6, limite=5, transport=None,
                 intervalle_minimum=0.25, horloge=None, pause=None):
        self.timeout = max(1, min(float(timeout), 15))
        self.limite = max(1, min(int(limite), 5))
        self._transport = transport or _charger_json
        self._intervalle = max(0, float(intervalle_minimum))
        self._horloge = horloge or time.monotonic
        self._pause = pause or time.sleep
        self._dernier_appel = None
        self._verrou = threading.Lock()

    def rechercher(self, texte):
        texte = str(texte or "").strip()
        if len(texte) < 3:
            return []
        url = URL_RECHERCHE + "?" + urlencode({
            "q": texte,
            "index": "address",
            "autocomplete": "0",
            "limit": self.limite,
        })
        charge = self._appeler(url)
        return _convertir_recherche(charge, self.limite)

    def autocompleter(self, texte):
        texte = str(texte or "").strip()
        if len(texte) < 3:
            return []
        url = URL_AUTOCOMPLETION + "?" + urlencode({
            "text": texte,
            "type": "StreetAddress",
            "maximumResponses": self.limite,
        })
        charge = self._appeler(url)
        return _convertir_autocompletion(charge, self.limite)

    def _appeler(self, url):
        with self._verrou:
            maintenant = self._horloge()
            if self._dernier_appel is not None:
                attente = self._intervalle - (maintenant - self._dernier_appel)
                if attente > 0:
                    self._pause(attente)
            self._dernier_appel = self._horloge()
        try:
            return self._transport(url, self.timeout)
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError("La Géoplateforme n'a pas répondu dans le délai prévu.") from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError("La recherche d'adresse publique est indisponible.") from erreur


def _charger_json(url, timeout):
    requete = Request(url, headers={"User-Agent": "Lumyn/0.0.4"})
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse Géoplateforme inattendue")
        return json.loads(reponse.read().decode("utf-8"))


def _proposition(nom, adresse, ville, identifiant=""):
    return PropositionLieu(
        nom=nom,
        adresse=adresse,
        source=SOURCE_BAN,
        ville=ville,
        identifiant=identifiant,
        conservation_autorisee=True,
    )


def _uniques(propositions, limite):
    resultat = []
    vus = set()
    for proposition in propositions:
        cle = proposition.adresse.casefold()
        if cle in vus:
            continue
        vus.add(cle)
        resultat.append(proposition)
        if len(resultat) >= limite:
            break
    return resultat


def _convertir_recherche(charge, limite):
    if not isinstance(charge, dict) or not isinstance(charge.get("features"), list):
        raise ValueError("Réponse Géoplateforme invalide.")
    propositions = []
    for feature in charge["features"]:
        proprietes = feature.get("properties") if isinstance(feature, dict) else None
        if not isinstance(proprietes, dict) or proprietes.get("_type") != "address":
            continue
        adresse = str(proprietes.get("label") or "").strip()
        nom = str(proprietes.get("name") or adresse).strip()
        ville = str(proprietes.get("city") or "").strip()
        if nom and adresse:
            propositions.append(_proposition(
                nom, adresse, ville,
                str(proprietes.get("banId") or proprietes.get("id") or "").strip(),
            ))
    return _uniques(propositions, limite)


def _convertir_autocompletion(charge, limite):
    if (not isinstance(charge, dict) or charge.get("status") != "OK"
            or not isinstance(charge.get("results"), list)):
        raise ValueError("Réponse d'autocomplétion Géoplateforme invalide.")
    propositions = []
    for suggestion in charge["results"]:
        if not isinstance(suggestion, dict) or suggestion.get("country") != "StreetAddress":
            continue
        adresse = str(suggestion.get("fulltext") or "").strip()
        ville = str(suggestion.get("city") or "").strip()
        nom = adresse.split(",", 1)[0].strip()
        if nom and adresse:
            propositions.append(_proposition(nom, adresse, ville))
    return _uniques(propositions, limite)

