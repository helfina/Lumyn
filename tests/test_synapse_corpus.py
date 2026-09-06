from unittest.mock import Mock

import pytest

from lumyn.modules.synapse.interpreteur_rendez_vous import (
    extraire_indices_deterministes,
)
from lumyn.modules.synapse.recherche_lieux import proposer_recherche_externe


ADRESSE_LORIENT = '2 rue Exemple, 56100 Lorient'
CORPUS = [
    ('rdv avec ma psy Laporte jeudi à 10h dans son cabinet à Lorient', 'psy'),
    ('jeudi 10h je vois Laporte ma psy à Lorient', 'psy'),
    ('rendez-vous jeudi à 10h avec le docteur Laporte à son cabinet de Lorient',
     'docteur'),
    ('jeudi vers 10 heures chez ma psy Laporte à Lorient', 'psy'),
]


def fiche_laporte(*adresses):
    return {
        'id': 'laporte', 'nom': 'Dr Laporte', 'alias': ['Laporte'],
        'profession': 'psy',
        'adresses': [
            {'adresse': adresse, 'favorite': index == 0}
            for index, adresse in enumerate(adresses)
        ],
    }


@pytest.mark.parametrize('phrase,profession', CORPUS)
def test_corpus_extrait_prudemment_et_resout_carnet_sans_fournisseur(
        phrase, profession):
    indices = extraire_indices_deterministes(phrase)
    assert indices == {
        'personne': 'Laporte', 'profession': profession, 'ville': 'Lorient'}
    ollama = Mock()
    public = Mock()
    web = Mock()

    resultat = proposer_recherche_externe(
        phrase, public, autoriser=True,
        lieux=[fiche_laporte(ADRESSE_LORIENT)],
        interpreteur_local=ollama, fournisseur_ia=web, autoriser_ia=True)

    rdv = resultat['rendez_vous']
    assert resultat['etat'] == 'confirmation'
    assert rdv['lieu'] == ADRESSE_LORIENT
    assert rdv['lieu_source'] == 'carnet'
    assert rdv['date'].isoformat() == '2026-09-10'
    assert rdv['heure'] == '10h'
    assert 'cabinet' not in rdv['lieu'].casefold()
    ollama.interpreter.assert_not_called()
    public.rechercher.assert_not_called()
    web.rechercher.assert_not_called()


def test_corpus_plusieurs_adresses_locales_reste_ambigu_sans_internet():
    phrase = CORPUS[0][0]
    ollama = Mock()
    public = Mock()
    web = Mock()
    resultat = proposer_recherche_externe(
        phrase, public, autoriser=True,
        lieux=[fiche_laporte(
            ADRESSE_LORIENT, '8 avenue Exemple, 56100 Lorient')],
        interpreteur_local=ollama, fournisseur_ia=web, autoriser_ia=True)
    assert resultat['etat'] == 'ambigu'
    assert 'Plusieurs adresses du Carnet' in resultat['message']
    assert resultat['rendez_vous']['lieu'] is None
    ollama.interpreter.assert_not_called()
    public.rechercher.assert_not_called()
    web.rechercher.assert_not_called()


def test_corpus_plusieurs_fiches_locales_reste_ambigu_sans_internet():
    phrase = CORPUS[1][0]
    lieux = [fiche_laporte(ADRESSE_LORIENT)]
    autre = fiche_laporte('8 avenue Exemple, 56100 Lorient')
    autre.update(id='laporte-2', nom='Dr Laporte homonyme')
    lieux.append(autre)
    public = Mock()
    resultat = proposer_recherche_externe(
        phrase, public, autoriser=True, lieux=lieux,
        interpreteur_local=Mock())
    assert resultat['etat'] == 'ambigu'
    assert 'Plusieurs fiches correspondent' in resultat['message']
    public.rechercher.assert_not_called()


def test_ville_seule_ne_selectionne_aucun_professionnel_du_carnet():
    phrase = 'jeudi 10h à Lorient'
    indices = extraire_indices_deterministes(phrase)
    assert indices == {'ville': 'Lorient'}
    resultat = proposer_recherche_externe(
        phrase, Mock(), autoriser=True,
        lieux=[fiche_laporte(ADRESSE_LORIENT)])
    assert resultat['rendez_vous']['lieu_source'] is None
    assert resultat['rendez_vous']['lieu'] is None
    assert resultat['etat'] == 'incomplet'


def test_chez_le_medecin_et_ville_ne_deviennent_pas_une_adresse():
    phrase = 'jeudi 10h chez le médecin à Lorient'
    assert extraire_indices_deterministes(phrase) == {
        'profession': 'médecin', 'ville': 'Lorient'}
    resultat = proposer_recherche_externe(
        phrase, Mock(), autoriser=False, lieux=[])
    assert resultat['rendez_vous']['lieu'] is None
    assert resultat['rendez_vous']['lieu_source'] is None
    assert resultat['etat'] == 'incomplet'
