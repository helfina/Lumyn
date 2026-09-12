from unittest.mock import Mock
from datetime import date

import pytest

from lumyn.modules.rendez_vous import analyseur
from lumyn.modules.synapse.interpreteur_rendez_vous import (
    extraire_indices_deterministes,
    interpreter_rendez_vous,
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


@pytest.fixture(autouse=True)
def date_reference_mercredi(monkeypatch):
    class DateFixe(date):
        @classmethod
        def today(cls):
            return cls(2026, 9, 9)

    monkeypatch.setattr(analyseur, 'date', DateFixe)


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


@pytest.mark.parametrize('phrase,heure', [
    ("j'ai rdv avec Dr Martin mardi à 14h30 à Vannes", '14h30'),
    ('mardi 14 h 30 je vois le docteur Martin à Vannes', '14h30'),
    ('rdv chez ma dentiste Dupont mercredi à 9 heures', '09h'),
    ('vendredi 10h avec ma psy Laporte à Lorient', '10h'),
    ('consultation avec le centre médical Ker Anna lundi à 11h', '11h'),
    ("j'ai rendez-vous vers 15h avec Martin au cabinet de Vannes", '15h'),
    ('JEUDI 10 H CHEZ MA PSY LAPORTE À LORIENT merci', '10h'),
    ('clinique Ker Anna, lundi 10 heures s’il vous plaît', '10h'),
])
def test_corpus_large_neleve_pas_et_ninvente_pas_adresse(phrase, heure):
    interpretation = interpreter_rendez_vous(phrase)
    resultat = proposer_recherche_externe(
        phrase, Mock(), autoriser=False, lieux=[])

    assert interpretation['heure'] == heure
    assert resultat['rendez_vous'].get('lieu_source') != 'carnet'
    lieu = resultat['rendez_vous'].get('lieu')
    if lieu:
        assert normaliser_sans_ponctuation(lieu) in normaliser_sans_ponctuation(phrase)
        assert not any(mot in lieu.casefold() for mot in (
            'rue ', 'avenue ', 'boulevard ', 'impasse '))


@pytest.mark.parametrize('forme', ['10h', '10 h', '10 heures'])
def test_variantes_heures_entieres(forme):
    resultat = interpreter_rendez_vous(f'rdv dentiste mardi {forme}')
    assert resultat['heure'] == '10h'


def test_nom_seul_reste_dans_le_texte_sans_identite_inventee():
    phrase = 'mardi 14h je vois Martin à Vannes'
    interpretation = interpreter_rendez_vous(phrase)
    assert interpretation['professionnel'] is None
    assert 'Martin' in interpretation['titre']
    assert interpretation['ville'] == 'Vannes'


def normaliser_sans_ponctuation(texte):
    return ' '.join(str(texte).casefold().replace(',', ' ').split())
