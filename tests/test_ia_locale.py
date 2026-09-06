import pytest

from lumyn.modules.synapse.ia_locale import (
    ErreurConfigurationIALocale,
    InterpreteurOllama,
    interpreteur_local_depuis_environnement,
)
from lumyn.modules.synapse.interpreteur_rendez_vous import interpreter_rendez_vous


def test_absence_ia_laisse_synapse_fonctionner():
    assert interpreteur_local_depuis_environnement({}) is None
    resultat = interpreter_rendez_vous("Dentiste mardi 14h")
    assert resultat["date"] and resultat["heure"] == "14h"


def test_ollama_sortie_valide_et_requete_locale_minimale():
    appels = []
    moteur = InterpreteurOllama("qwen-test", transport=lambda url, corps, timeout:
        appels.append((url, corps, timeout)) or {"response":
            '{"personne":"Laporte","profession":"psychologue","ville":"Lorient","mode":"physique"}'})
    resultat = moteur.interpreter("ma psy Laporte jeudi 10h à Lorient")
    assert resultat == {"personne": "Laporte", "profession": "psychologue",
                        "ville": "Lorient", "mode": "physique"}
    assert appels[0][0] == "http://127.0.0.1:11434/api/generate"
    assert appels[0][1]["stream"] is False and appels[0][1]["format"] == "json"


@pytest.mark.parametrize("reponse", [
    "pas du json",
    '{"adresse":"1 rue inventée"}',
    '{"mode":"magique"}',
    '{"indices":"pas une liste"}',
])
def test_sortie_invalide_hallucination_ou_champ_inconnu_rejetee(reponse):
    moteur = InterpreteurOllama("test", transport=lambda u, c, t: {"response": reponse})
    with pytest.raises(ValueError):
        moteur.interpreter("demande")


def test_timeout_et_configuration_stricte():
    moteur = InterpreteurOllama("test", transport=lambda u, c, t:
        (_ for _ in ()).throw(TimeoutError()))
    with pytest.raises(TimeoutError):
        moteur.interpreter("demande")
    with pytest.raises(ErreurConfigurationIALocale, match="MODEL"):
        interpreteur_local_depuis_environnement({"LUMYN_IA_LOCALE": "ollama"})
    with pytest.raises(ErreurConfigurationIALocale, match="local"):
        InterpreteurOllama("test", url="https://serveur.example")
