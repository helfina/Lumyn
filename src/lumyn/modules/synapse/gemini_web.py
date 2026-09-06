"""Adaptateur Gemini Web préparé mais non activable tant que Search exige le niveau payant."""

import json
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from lumyn.modules.synapse.recherche_lieux import PropositionLieu


URL_INTERACTIONS = "https://generativelanguage.googleapis.com/v1beta/interactions"


class ErreurConfigurationGemini(ValueError):
    """Gemini Web reste explicitement hors du parcours normal."""


class FournisseurGeminiWeb:
    """Repli Web minimal ; les résultats sans URL citée sont refusés."""

    def __init__(self, cle_api, *, modele="gemini-3.8-flash", timeout=8,
                 limite=3, transport=None):
        self.cle_api = str(cle_api or "").strip()
        if not self.cle_api:
            raise ErreurConfigurationGemini("GEMINI_API_KEY est absente.")
        self.modele = str(modele or "").strip()
        self.timeout = max(1, min(float(timeout), 20))
        self.limite = max(1, min(int(limite), 3))
        self._transport = transport or _poster_json

    def rechercher(self, texte):
        texte = str(texte or "").strip()
        if len(texte) < 3:
            return []
        consigne = (
            "Trouve au plus trois lieux professionnels correspondant à cette requête minimale. "
            "Réponds uniquement par un tableau JSON avec nom, adresse, profession, ville, source_url. "
            "N'invente rien et cite la page publique qui prouve chaque adresse. Requête: " + texte
        )
        corps = {"model": self.modele, "input": consigne,
                 "tools": [{"type": "google_search"}]}
        try:
            charge = self._transport(URL_INTERACTIONS, corps, self.timeout, self.cle_api)
        except (TimeoutError, socket.timeout) as erreur:
            raise TimeoutError("Gemini Web n'a pas répondu dans le délai prévu.") from erreur
        except (HTTPError, URLError, OSError) as erreur:
            raise OSError("Gemini Web est indisponible.") from erreur
        return _convertir_reponse(charge, self.limite)


def _convertir_reponse(charge, limite):
    if not isinstance(charge, dict) or not isinstance(charge.get("steps"), list):
        raise ValueError("Réponse Gemini Web invalide.")
    textes = []
    citations = set()
    for etape in charge["steps"]:
        if not isinstance(etape, dict) or etape.get("type") != "model_output":
            continue
        for bloc in etape.get("content") or []:
            if not isinstance(bloc, dict) or bloc.get("type") != "text":
                continue
            textes.append(str(bloc.get("text") or ""))
            for annotation in bloc.get("annotations") or []:
                if isinstance(annotation, dict) and annotation.get("type") == "url_citation":
                    url = str(annotation.get("url") or "").strip()
                    if url.startswith(("https://", "http://")):
                        citations.add(url)
    if not textes:
        raise ValueError("Réponse Gemini Web sans contenu sourcé.")
    try:
        donnees = json.loads(textes[-1])
    except json.JSONDecodeError as erreur:
        raise ValueError("JSON Gemini Web invalide.") from erreur
    if not isinstance(donnees, list):
        raise ValueError("Réponse Gemini Web invalide.")
    propositions = []
    for valeur in donnees:
        if not isinstance(valeur, dict) or set(valeur) - {
                "nom", "adresse", "profession", "ville", "source_url"}:
            continue
        nom = str(valeur.get("nom") or "").strip()
        adresse = str(valeur.get("adresse") or "").strip()
        source = str(valeur.get("source_url") or "").strip()
        if not nom or not adresse or source not in citations:
            continue
        propositions.append(PropositionLieu(
            nom=nom, adresse=adresse, source="Gemini Web — " + source,
            profession=str(valeur.get("profession") or "").strip(),
            ville=str(valeur.get("ville") or "").strip(),
            conservation_autorisee=False,
        ))
        if len(propositions) >= limite:
            break
    return propositions


def fournisseur_gemini_depuis_environnement(environ=None):
    """Refuse l'activation réelle : Google Search n'est pas dans le Free Tier vérifié."""
    environ = os.environ if environ is None else environ
    activation = str(environ.get("LUMYN_GEMINI_WEB", "")).strip().casefold()
    if activation in {"", "0", "false", "non", "off"}:
        return None
    raise ErreurConfigurationGemini(
        "Gemini Web reste désactivé : Google Search grounding exige actuellement le niveau payant."
    )


def _poster_json(url, corps, timeout, cle_api):
    requete = Request(url, data=json.dumps(corps, ensure_ascii=False).encode("utf-8"),
        method="POST", headers={"Content-Type": "application/json",
                                "x-goog-api-key": cle_api,
                                "User-Agent": "Lumyn/0.0.4"})
    with urlopen(requete, timeout=timeout) as reponse:
        if getattr(reponse, "status", 200) != 200:
            raise OSError("Réponse Gemini inattendue")
        return json.loads(reponse.read().decode("utf-8"))

