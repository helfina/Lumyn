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

    from lumyn.modules.rendez_vous import stockage

    monkeypatch.setattr(stockage, "DOSSIER_DONNEES", tmp_path)
    monkeypatch.setattr(
        stockage,
        "FICHIER_RENDEZ_VOUS",
        tmp_path / "rendez_vous.json",
    )

    connexion_originale = socket.socket.connect

    def connexion_isolee(sock, adresse):
        """Autorise le loopback nécessaire à asyncio, bloque le réseau externe."""

        if isinstance(adresse, tuple) and adresse:
            hote = adresse[0]

            if hote in {"127.0.0.1", "::1", "localhost"}:
                return connexion_originale(sock, adresse)

        raise AssertionError("Accès réseau interdit pendant les tests")

    monkeypatch.setattr(socket.socket, "connect", connexion_isolee)
