"""Scénarios de résolution locaux, avec adresses fictives exclusivement."""
from copy import deepcopy
import pytest
from lumyn.modules.synapse.orchestrateur_rendez_vous import preparer_rendez_vous_synapse as preparer
from lumyn.modules.synapse.interpreteur_rendez_vous import interpreter_rendez_vous

@pytest.fixture
def carnet():
    return [
        {'id':'maison','nom':'Maison','alias':[], 'adresses':[{'adresse':'1 rue Exemple, Ville Test','favorite':True}]},
        {'id':'laporte','nom':'Dr Laporte','alias':['Laporte'],'profession':'psychiatre','adresses':[{'adresse':'2 rue Exemple, Lorient','favorite':True}]},
        {'id':'dentiste','nom':'Dentiste Guégon','alias':['dentiste'],'profession':'dentiste','adresses':[{'adresse':'3 rue Exemple, Guégon','favorite':True},{'adresse':'4 rue Exemple, Lorient','favorite':False}]},
        {'id':'itep','nom':'ITEP Vannes','alias':['ITEP'],'adresses':[{'adresse':'5 rue Exemple, Vannes','favorite':True}]},
    ]

@pytest.mark.parametrize('phrase,adresse',[
    ('mardi 15h dentiste à Lorient','4 rue Exemple, Lorient'),
    ('dentiste mardi 15h Lorient','4 rue Exemple, Lorient'),
    ('Dr Laporte psychiatre Lorient jeudi 10h','2 rue Exemple, Lorient'),
    ('mardi 15h dentiste Guégon','3 rue Exemple, Guégon'),
    ('ITEP mardi 14h','5 rue Exemple, Vannes'),
])
def test_saisies_ordres_et_metiers(carnet, phrase, adresse):
    r=preparer(phrase,carnet)
    assert r['etat']=='confirmation',r['message']
    assert r['rendez_vous']['lieu']==adresse
    assert r['rendez_vous']['mode']=='physique'

@pytest.mark.parametrize('expression',['visio','à domicile','chez moi','maison'])
def test_modes_maison(carnet,expression):
    phrase='Laporte jeudi 10h '+expression
    r=preparer(phrase,carnet)
    assert r['etat']=='confirmation',r['message']
    assert r['rendez_vous']['lieu']=='1 rue Exemple, Ville Test'
    assert r['rendez_vous']['titre']=='Dr Laporte — '+('VISIO' if expression=='visio' else 'DOMICILE')
    assert r['rendez_vous']['lieu_source']=='maison'


def test_infirmiere_a_domicile(carnet):
    r=preparer('infirmière vendredi 9h à domicile',carnet)
    assert r['rendez_vous']['titre']=='Infirmière — DOMICILE'
    assert r['rendez_vous']['lieu']==carnet[0]['adresses'][0]['adresse']


def test_visio_ne_depend_pas_de_adresse_professionnel(carnet):
    carnet[1]['adresses']=[]
    assert preparer('Laporte jeudi 10h visio',carnet)['etat']=='confirmation'
    assert preparer('Laporte jeudi 10h',carnet)['etat']=='incomplet'


def test_maison_absente_pas_adresse_inventee(carnet):
    r=preparer('Laporte jeudi 10h visio',carnet[1:])
    assert r['etat']=='incomplet'
    assert r['rendez_vous']['lieu'] is None


def test_plusieurs_maisons_bloquent(carnet):
    carnet.append({'nom':'Domicile','adresses':[{'adresse':'Autre'}]})
    assert preparer('Laporte jeudi 10h visio',carnet)['etat']=='ambigu'


def test_adresses_sans_favorite_et_favorites_multiples(carnet):
    for favorite in (False,True):
        for a in carnet[2]['adresses']:a['favorite']=favorite
        assert preparer('dentiste mardi 10h',carnet)['etat']=='ambigu'
    r=preparer('dentiste mardi 10h à Lorient',carnet)
    assert r['etat']=='confirmation'
    assert r['rendez_vous']['lieu']=='4 rue Exemple, Lorient'


def test_plusieurs_candidats_et_nom_precis(carnet):
    carnet.append({'nom':'Dr Autre','profession':'psychiatre','adresses':[{'adresse':'6 rue Exemple, Lorient'}]})
    assert preparer('psychiatre jeudi 10h',carnet)['etat']=='ambigu'
    r=preparer('Dr Laporte psychiatre jeudi 10h',carnet)
    assert r['etat']=='confirmation'


def test_intention_explicite_prime_favorite(carnet):
    r=preparer('dentiste mardi 10h à Pontivy',carnet)
    assert r['rendez_vous']['lieu']=='Pontivy'
    assert '3 rue' not in r['message']


def test_telephone_aucune_adresse_ni_lien(carnet):
    r=preparer('Laporte jeudi 10h par téléphone',carnet)
    assert r['rendez_vous']['mode']=='telephone'
    assert r['rendez_vous']['lieu'] is None


def test_modes_contradictoires_bloquent(carnet):
    assert preparer('Laporte jeudi 10h visio téléphone',carnet)['etat']=='ambigu'

@pytest.mark.parametrize('phrase',['ITEP mardi 14:99','ITEP lundi 08/09/2026 10h','ITEP 31/02/2026 10h'])
def test_validation_deterministe_conservee(carnet,phrase):
    assert preparer(phrase,carnet)['etat']=='erreur'


def test_incomplet_et_non_mutation(carnet):
    avant=deepcopy(carnet)
    assert preparer('ITEP mardi',carnet)['etat']=='incomplet'
    assert carnet==avant
    assert preparer(' ',carnet)['etat']=='vide'
    assert preparer('CAF demain 10h',[])['rendez_vous']['lieu'] is None


def test_donnees_interpretees():
    r=interpreter_rendez_vous('Dr Laporte psychiatre Lorient jeudi 10h')
    assert r['intention']=='rendez_vous'
    assert r['professionnel']=='Dr Laporte'
    assert r['profession']=='psychiatre'
    assert r['lieu_explicite']=='Lorient'


def test_ville_apres_alias_prioritaire(carnet):
    carnet[1]['adresses'].append({'adresse':'7 rue Exemple, Vannes','favorite':False})
    r=preparer('Laporte Vannes jeudi 10h',carnet)
    assert r['etat']=='confirmation'
    assert r['rendez_vous']['lieu']=='7 rue Exemple, Vannes'


def test_qualificatif_inconnu_ne_declenche_pas_favorite(carnet):
    r=preparer('Laporte Quimper jeudi 10h',carnet)
    assert r['etat']=='ambigu'
    assert r['rendez_vous']['lieu'] is None


def test_physique_sans_adresse_demande_precision():
    r=preparer('Dentiste demain 10h en présentiel',[])
    assert r['etat']=='incomplet'
