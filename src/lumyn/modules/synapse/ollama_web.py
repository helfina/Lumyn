"""Ollama Web Search préparé comme dernier recours, jamais actif par défaut."""

import json
import os
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from lumyn.modules.synapse.recherche_lieux import PropositionLieu


URL_RECHERCHE = "https://ollama.com/api/web_search"
MOTIF_ADRESSE = re.compile(
    r"\b(\d{1,4}(?:\s+(?:bis|ter|quater))?\s+"
    r"(?:rue|avenue|boulevard|route|impasse|all[ée]e|place|chemin|quai|cours)"
    r"\s+[^\n.;]{2,80}?(?:,\s*)?\d{5}\s+[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ '\u2019-]{1,50})\b",
    re.IGNORECASE,
)


class ErreurConfigurationOllamaWeb(ValueError):
    """Configuration Web absente ou incomplète."""


class FournisseurOllamaWeb:
    """Transforme des résultats Web sourcés puis vérifie leur adresse avec BAN."""

    def __init__(self, cle_api, *, ban, timeout=8, limite=3, transport=None):
        self.cle_api = str(cle_api or "").strip()
        if not self.cle_api:
            raise ErreurConfigurationOllamaWeb("OLLAMA_API_KEY est absente.")
        self.ban = ban
        self.timeout = max(1, min(float(timeout), 20))
        self.limite = max(1, min(int(limite), 3))
        self._transport = transport or _poster_json

    def rechercher(self, texte):
        texte = str(texte or "").strip()
        if len(texte) < 3:
            return []
        requete = texte + " adresse professionnelle"
        try:
            charge = self._transport(
                URL_RECHERCHE,
                {"query": requete, "max_results": self.limite},
                self.timeout,
                self.cle_api,
            )
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError("Ollama Web Search n'a pas répondu dans le délai prévu.") from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError("Ollama Web Search est indisponible ou son quota est épuisé.") from erreur
        return self._convertir(charge)

    def _convertir(self, charge):
        if not isinstance(charge, dict) or not isinstance(charge.get("results"), list):
            raise ValueError("Réponse Ollama Web Search invalide.")
        propositions = []
        vus = set()
        for resultat in charge["results"]:
            if not isinstance(resultat, dict):
                continue
            titre = str(resultat.get("title") or "").strip()
            url = str(resultat.get("url") or "").strip()
            contenu = str(resultat.get("content") or "")
            url_analysee = urlsplit(url)
            if (not titre or url_analysee.scheme not in {"https", "http"}
                    or not url_analysee.hostname
                    or url_analysee.username is not None
                    or url_analysee.password is not None):
                continue
            correspondance = MOTIF_ADRESSE.search(contenu)
            if not correspondance:
                continue
            adresse_web = " ".join(correspondance.group(1).split())
            cle = (url.casefold(), adresse_web.casefold())
            if cle in vus:
                continue
            vus.add(cle)
            propositions.append(self._verifier(titre, adresse_web, url))
            if len(propositions) >= self.limite:
                break
        return propositions

    def _verifier(self, titre, adresse_web, url):
        source_web = (
            "Ollama Web Search — " + (urlsplit(url).hostname or "site inconnu")
            + " — " + url
        )
        try:
            candidats = list(self.ban.rechercher(adresse_web))
        except (OSError, TimeoutError, ValueError):
            candidats = []
        candidat = next((c for c in candidats
                          if _adresses_compatibles(adresse_web, c.adresse)), None)
        if candidat is None:
            return PropositionLieu(
                titre, adresse_web, source_web, identifiant=url,
                conservation_autorisee=False, adresse_verifiee=False)
        return PropositionLieu(
            titre, candidat.adresse,
            source_web + " | vérification : " + candidat.source,
            ville=candidat.ville, identifiant=url,
            conservation_autorisee=False, adresse_verifiee=True)


def _adresses_compatibles(adresse_web, adresse_ban):
    def elements(valeur):
        normalise = str(valeur).casefold().replace("’", "'")
        numero = re.search(r"\b\d{1,4}\b", normalise)
        code = re.search(r"\b\d{5}\b", normalise)
        mots_faibles = {
            "rue", "avenue", "boulevard", "route", "impasse", "allee",
            "allée", "place", "chemin", "quai", "cours", "des", "les",
            "une", "sur", "sous",
        }
        mots = {
            mot for mot in re.findall(r"[a-zà-ÿ]{3,}", normalise)
            if mot not in mots_faibles
        }
        return numero.group(0) if numero else "", code.group(0) if code else "", mots

    numero_web, code_web, mots_web = elements(adresse_web)
    numero_ban, code_ban, mots_ban = elements(adresse_ban)
    if not numero_web or numero_web != numero_ban:
        return False
    if code_web and code_web != code_ban:
        return False
    communs = mots_web & mots_ban
    return len(communs) >= 2 and len(communs) / max(1, len(mots_web)) >= 0.5


def fournisseur_ollama_web_depuis_environnement(environ=None, *, ban=None):
    """Active explicitement le Web avec une clé locale ; sinon aucun trafic."""
    environ = os.environ if environ is None else environ
    activation = str(environ.get("LUMYN_OLLAMA_WEB", "")).strip().casefold()
    if activation in {"", "0", "false", "non", "off"}:
        return None
    if activation not in {"1", "true", "oui", "on", "ollama"}:
        raise ErreurConfigurationOllamaWeb(
            "LUMYN_OLLAMA_WEB doit valoir '1' ou rester vide."
        )
    if ban is None:
        raise ErreurConfigurationOllamaWeb(
            "La vérification BAN est requise pour activer Ollama Web Search."
        )
    return FournisseurOllamaWeb(environ.get("OLLAMA_API_KEY"), ban=ban)


def _poster_json(url, corps, timeout, cle_api):
    requete = Request(
        url,
        data=json.dumps(corps, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + cle_api,
            "Content-Type": "application/json",
            "User-Agent": "Lumyn/0.0.4",
        },
    )
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse Ollama Web Search inattendue")
        return json.loads(reponse.read().decode("utf-8"))
