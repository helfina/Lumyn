import socket

import pytest

from lumyn.modules.synapse import geoplateforme, ia_locale


def test_socket_externe_est_bloquee_avec_nom_du_test():
    connexion = socket.socket()
    try:
        with pytest.raises(AssertionError, match=(
                r"Accès réseau réel interdit pendant "
                r"tests/test_reseau_interdit.py::test_socket_externe")):
            connexion.connect(("203.0.113.1", 443))
    finally:
        connexion.close()


def test_socket_ollama_locale_est_bloquee():
    connexion = socket.socket()
    try:
        with pytest.raises(AssertionError, match="Accès réseau réel interdit"):
            connexion.connect(("127.0.0.1", 11434))
    finally:
        connexion.close()


@pytest.mark.parametrize("appel", [
    lambda: geoplateforme._charger_json("https://example.invalid", 1),
    lambda: ia_locale._poster_json("http://127.0.0.1:11434/api/generate", {}, 1),
])
def test_http_et_ollama_local_reels_sont_bloques(appel):
    with pytest.raises(AssertionError, match="Accès réseau réel interdit"):
        appel()
