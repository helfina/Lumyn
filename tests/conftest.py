"""Tests isolés : aucun agenda réel ni fichier personnel n'est utilisé."""

import os
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ["TOGA_BACKEND"] = "toga_dummy"


@pytest.fixture(autouse=True)
def isoler_donnees_et_reseau(monkeypatch, tmp_path):
    """Isole les fichiers personnels et interdit les connexions réseau externes."""

    import socket

    from lumyn.modules.rendez_vous import reprise_google
    monkeypatch.setattr(reprise_google, "FICHIER_REPRISE", tmp_path / "creations_google.json")

    from lumyn.modules.rendez_vous import stockage

    monkeypatch.setattr(stockage, "DOSSIER_DONNEES", tmp_path)
    monkeypatch.setattr(
        stockage,
        "FICHIER_RENDEZ_VOUS",
        tmp_path / "rendez_vous.json",
    )

    from lumyn.modules.lieux import stockage as stockage_lieux
    from lumyn.modules.rendez_vous import calendrier_ui
    monkeypatch.setattr(stockage_lieux, "DOSSIER_DONNEES", tmp_path)
    monkeypatch.setattr(stockage_lieux, "FICHIER_LIEUX", tmp_path / "lieux.json")
    monkeypatch.setattr(calendrier_ui, "DOSSIER_LUMYN", tmp_path)
    monkeypatch.setattr(calendrier_ui, "FICHIER_PREFERENCES_CALENDRIERS", tmp_path / "calendriers.json")

    connexion_originale = socket.socket.connect

    def message_reseau(destination):
        test = os.environ.get("PYTEST_CURRENT_TEST", "test inconnu").split(" ", 1)[0]
        return f"Accès réseau réel interdit pendant {test} : {destination!r}"

    def connexion_isolee(sock, adresse):
        """Autorise le loopback nécessaire à asyncio, bloque le réseau externe."""

        if isinstance(adresse, tuple) and adresse:
            hote = adresse[0]

            port = adresse[1] if len(adresse) > 1 else None
            if hote in {"127.0.0.1", "::1", "localhost"} and port != 11434:
                return connexion_originale(sock, adresse)

        raise AssertionError(message_reseau(adresse))

    monkeypatch.setattr(socket.socket, "connect", connexion_isolee)

    def urlopen_interdit(requete, *args, **kwargs):
        destination = getattr(requete, "full_url", requete)
        raise AssertionError(message_reseau(destination))

    from lumyn.modules.synapse import (
        entreprises, geoplateforme, ia_locale, ollama_web, sante_publique,
    )
    for module in (entreprises, geoplateforme, ia_locale, ollama_web,
                   sante_publique):
        monkeypatch.setattr(module, "urlopen", urlopen_interdit)
