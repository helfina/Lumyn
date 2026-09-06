from unittest.mock import Mock
import pytest
from tests.test_ui import interface
from lumyn.modules.lieux import stockage as carnet
from lumyn.modules.rendez_vous import stockage, ui
from lumyn.modules.synapse.recherche_lieux import PropositionLieu, proposer_recherche_externe
from lumyn.modules.synapse.selection_lieux import choisir_proposition, enregistrer_proposition
from lumyn.modules.synapse.recherche_ui import RechercheLieuxUI

PHRASE = 'Dr Dupont dermatologue Vannes mardi 14h'
P = PropositionLieu('Dr Dupont','1 rue Exemple, Vannes','https://exemple.invalid/source','dermatologue','Vannes')
Q = PropositionLieu('Dr Dupont','2 rue Exemple, Vannes','https://exemple.invalid/autre')


@pytest.mark.parametrize('resultats,etat', [([], 'incomplet'), ([P], 'ambigu'), ([P,Q], 'ambigu'), ([None], 'incomplet')])
def test_resultats_structures(resultats,etat):
    fournisseur = Mock(rechercher=Mock(return_value=resultats))
    resultat = proposer_recherche_externe(PHRASE,fournisseur,autoriser=True)
    assert resultat['etat'] == etat
    requete = fournisseur.rechercher.call_args.args[0]
    assert 'mardi' not in requete and '14h' not in requete
    assert 'Dupont' in requete and 'Vannes' in requete
    assert not carnet.FICHIER_LIEUX.exists()
    assert stockage.charger_rendez_vous() == []


@pytest.mark.parametrize('erreur', [OSError('Hors ligne'),TimeoutError('Délai')])
def test_erreur_recherche_repli_ia_et_non_necessaire(erreur):
    structure = Mock(rechercher=Mock(side_effect=erreur))
    ia = Mock(rechercher=Mock(return_value=[P]))
    resultat = proposer_recherche_externe(PHRASE,structure,autoriser=True,fournisseur_ia=ia,autoriser_ia=True)
    assert resultat['fournisseur_utilise'] == 'ia_web'
    assert ia.rechercher.call_args.args == structure.rechercher.call_args.args
    structure.rechercher.side_effect = None
    structure.rechercher.return_value = [Q]
    ia.reset_mock()
    resultat = proposer_recherche_externe(PHRASE,structure,autoriser=True,fournisseur_ia=ia,autoriser_ia=True)
    assert resultat['propositions_externes'] == [Q]
    ia.rechercher.assert_not_called()


def test_ia_absente_ou_non_autorisee():
    structure = Mock(rechercher=Mock(return_value=[]))
    ia = Mock(rechercher=Mock(side_effect=TimeoutError('Indisponible')))
    assert proposer_recherche_externe(PHRASE,structure,autoriser=True,fournisseur_ia=ia)['etat']=='incomplet'
    ia.rechercher.assert_not_called()
    assert proposer_recherche_externe(PHRASE,structure,autoriser=True,fournisseur_ia=ia,autoriser_ia=True)['etat']=='incomplet'


@pytest.mark.parametrize('phrase', ['Laporte jeudi 10h visio','infirmière vendredi 9h à domicile','CAF demain 10h par téléphone'])
def test_modes_sans_externe(phrase):
    moteur = Mock()
    proposer_recherche_externe(phrase,moteur,autoriser=True,fournisseur_ia=moteur,autoriser_ia=True)
    moteur.rechercher.assert_not_called()


def test_fiche_enregistree_prioritaire_et_pas_doublon():
    resultat = choisir_proposition(PHRASE,P,[P])
    assert resultat['etat']=='confirmation' and resultat['rendez_vous']['lieu']==P.adresse
    assert not carnet.FICHIER_LIEUX.exists()
    with pytest.raises(ValueError):enregistrer_proposition(P)
    fiche = enregistrer_proposition(P,autoriser=True)['fiche']
    moteur = Mock()
    local = proposer_recherche_externe('Dr Dupont mardi 14h',moteur,autoriser=True)
    assert local['rendez_vous']['lieu_source']=='carnet'
    moteur.rechercher.assert_not_called()
    candidats = enregistrer_proposition(P,autoriser=True)
    assert candidats['etat']=='choix_fiche'
    enregistrer_proposition(P,autoriser=True,fiche_id=fiche['id'])
    assert len(carnet.charger_lieux()) == 1
    assert len(carnet.charger_lieux()[0]['adresses']) == 1
    enregistrer_proposition(Q,autoriser=True,fiche_id=fiche['id'])
    apres = carnet.charger_lieux()[0]
    assert len(apres['adresses']) == 2 and apres['adresses'][0]['favorite']
    assert not apres['adresses'][1]['favorite']


def test_ambiguite_carnet_bloque_recherche():
    carnet.enregistrer_lieu({'nom':'Premier','alias':['Dupont']})
    carnet.enregistrer_lieu({'nom':'Second','alias':['Dupont']})
    moteur = Mock()
    assert proposer_recherche_externe('Dupont mardi 14h',moteur,autoriser=True)['etat']=='ambigu'
    moteur.rechercher.assert_not_called()


def test_proposition_hors_liste_refusee():
    with pytest.raises(ValueError):choisir_proposition(PHRASE,Q,[P])


@pytest.fixture
def panneau(interface):
    interface.recherche_lieux_ui = RechercheLieuxUI(interface,Mock(rechercher=Mock(return_value=[P,Q])))
    return interface.recherche_lieux_ui


def test_ui_choix_changement_et_confirmation(interface,panneau,monkeypatch):
    creation = Mock(return_value={'id':'g1'})
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    interface.rdv_input.value = PHRASE
    panneau.rechercher()
    assert not interface.confirmer_button.enabled
    panneau.choisir(P)
    panneau.choisir(Q)
    assert interface.resultat_courant['rendez_vous']['lieu']==Q.adresse
    creation.assert_not_called()
    assert not carnet.FICHIER_LIEUX.exists()
    interface.valider_depuis_saisie()
    creation.assert_called_once()
    assert creation.call_args.args[0]['lieu']==Q.adresse
    assert not carnet.FICHIER_LIEUX.exists()
    assert not panneau.enregistrer_button.enabled


def test_ui_enregistrement_volontaire_et_ancienne_recherche(interface,panneau):
    interface.rdv_input.value = PHRASE
    panneau.rechercher()
    panneau.choisir(P)
    panneau.enregistrer()
    assert len(carnet.charger_lieux()) == 1
    assert stockage.charger_rendez_vous()==[]
    interface.rdv_input.value = 'Autre demain 10h'
    panneau.choisir(Q)
    assert panneau.selection is None
    assert len(carnet.charger_lieux()) == 1


def test_ui_panne_recherche_saisie_manuelle_disponible(interface,panneau):
    panneau.fournisseur.rechercher.side_effect = TimeoutError('Délai')
    interface.rdv_input.value = PHRASE
    panneau.rechercher()
    assert not interface.confirmer_button.enabled
    interface.rdv_input.value='CAF demain 10h à Vannes'
    interface.analyser_rendez_vous(None)
    assert interface.confirmer_button.enabled
