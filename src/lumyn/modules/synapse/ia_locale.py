"""Interprétation locale facultative ; Synapse déterministe reste la source de vérité."""

import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


CHAMPS_AUTORISES = {
    "personne", "etablissement", "profession", "ville", "mode",
    "date", "heure", "indices",
}
MODES_AUTORISES = {"physique", "visio", "domicile", "telephone", "non_defini"}


class ErreurConfigurationIALocale(ValueError):
    """Configuration locale activée mais incomplète ou dangereuse."""


class InterpreteurOllama:
    """Demande un JSON minimal à un Ollama local, sans télécharger de modèle."""

    def __init__(self, modele, *, url="http://127.0.0.1:11434", timeout=8, transport=None):
        self.modele = str(modele or "").strip()
        if not self.modele:
            raise ErreurConfigurationIALocale("LUMYN_OLLAMA_MODEL est requis pour activer Ollama.")
        url = str(url or "").rstrip("/")
        hote = (urlsplit(url).hostname or "").casefold()
        if hote not in {"127.0.0.1", "localhost", "::1"}:
            raise ErreurConfigurationIALocale("Ollama doit rester sur l'ordinateur local.")
        self.url = url + "/api/generate"
        self.timeout = max(1, min(float(timeout), 20))
        self._transport = transport or _poster_json

    def interpreter(self, texte):
        texte = str(texte or "").strip()
        if not texte:
            return {}
        consigne = (
            "Extrais uniquement personne, etablissement, profession, ville, mode, date, heure "
            "et indices. Réponds en JSON. N'invente jamais d'adresse et n'ajoute aucun champ.\n"
            "Demande: " + texte
        )
        corps = {"model": self.modele, "prompt": consigne, "format": "json", "stream": False}
        try:
            charge = self._transport(self.url, corps, self.timeout)
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError("L'IA locale n'a pas répondu dans le délai prévu.") from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError("L'IA locale est indisponible ; Synapse reste utilisable.") from erreur
        if not isinstance(charge, dict) or not isinstance(charge.get("response"), str):
            raise ValueError("Réponse Ollama invalide.")
        try:
            resultat = json.loads(charge["response"])
        except json.JSONDecodeError as erreur:
            raise ValueError("JSON Ollama invalide.") from erreur
        return valider_indices_locaux(resultat)


def valider_indices_locaux(resultat):
    """Rejette tout champ inconnu, notamment une adresse présentée comme vraie."""
    if not isinstance(resultat, dict) or set(resultat) - CHAMPS_AUTORISES:
        raise ValueError("Sortie IA locale non conforme.")
    valide = {}
    for cle, valeur in resultat.items():
        if cle == "indices":
            if not isinstance(valeur, list) or not all(isinstance(v, str) for v in valeur):
                raise ValueError("Sortie IA locale non conforme.")
            valide[cle] = [v.strip() for v in valeur[:5] if v.strip()]
        elif valeur is not None:
            if not isinstance(valeur, str) or len(valeur.strip()) > 160:
                raise ValueError("Sortie IA locale non conforme.")
            valide[cle] = valeur.strip()
    if valide.get("mode") not in MODES_AUTORISES | {None}:
        raise ValueError("Mode produit par l'IA locale invalide.")
    return valide


def interpreteur_local_depuis_environnement(environ=None, *, transport=None):
    environ = os.environ if environ is None else environ
    activation = str(environ.get("LUMYN_IA_LOCALE", "")).strip().casefold()
    if activation in {"", "0", "false", "non", "off"}:
        return None
    if activation != "ollama":
        raise ErreurConfigurationIALocale("LUMYN_IA_LOCALE doit valoir 'ollama' ou rester vide.")
    return InterpreteurOllama(
        environ.get("LUMYN_OLLAMA_MODEL"),
        url=environ.get("LUMYN_OLLAMA_URL", "http://127.0.0.1:11434"),
        transport=transport,
    )


def _poster_json(url, corps, timeout):
    donnees = json.dumps(corps, ensure_ascii=False).encode("utf-8")
    requete = Request(url, data=donnees, method="POST", headers={
        "Content-Type": "application/json", "User-Agent": "Lumyn/0.0.4",
    })
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse Ollama inattendue")
        return json.loads(reponse.read().decode("utf-8"))

