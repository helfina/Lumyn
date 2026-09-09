from unittest.mock import Mock
from lumyn.modules.synapse.recherche_lieux import proposer_recherche_externe, PropositionLieu, requete_minimale
from lumyn.modules.lieux import stockage


def test_carnet_prioritaire_sur_externe():
    fiche=stockage.enregistrer_lieu({'nom':'ITEP Vannes','alias':['ITEP'],'adresses':[{'adresse':'Adresse personnelle fictive','favorite':True}]})
    fournisseur=Mock()
    r=proposer_recherche_externe('ITEP mardi 14h',fournisseur,autoriser=True)
    fournisseur.rechercher.assert_not_called()
    assert r['rendez_vous']['lieu']=='Adresse personnelle fictive'
    assert stockage.charger_lieux()==[fiche]


def test_pas_de_reseau_par_defaut():
    fournisseur=Mock()
    proposer_recherche_externe('Dentiste mardi 14h à Lorient',fournisseur)
    fournisseur.rechercher.assert_not_called()


def test_proposition_unique_jamais_appliquee_ni_enregistree():
    fournisseur=Mock()
    fournisseur.rechercher.return_value=[PropositionLieu(
        'Cabinet dentaire','12 rue Test, Lorient','Source test',
        profession='dentiste', ville='Lorient')]
    r=proposer_recherche_externe('Dentiste mardi 14h à Lorient',fournisseur,autoriser=True)
    assert r['etat']=='ambigu'
    assert r['rendez_vous']['lieu'] is None
    assert not stockage.FICHIER_LIEUX.exists()


def test_propositions_multiples_exigent_choix():
    fournisseur=Mock()
    fournisseur.rechercher.return_value=[
        PropositionLieu('Cabinet dentaire A','Adresse A','Test',profession='dentiste'),
        PropositionLieu('Cabinet dentaire B','Adresse B','Test',profession='dentiste')]
    r=proposer_recherche_externe('Dentiste mardi 14h',fournisseur,autoriser=True)
    assert r['etat']=='ambigu'
    assert r['rendez_vous']['lieu'] is None


def test_absence_resultat_ou_panne_reste_incomplet():
    fournisseur=Mock()
    fournisseur.rechercher.return_value=[]
    r=proposer_recherche_externe('Dentiste mardi 14h',fournisseur,autoriser=True)
    assert r['etat']=='incomplet' and r['rendez_vous']['lieu'] is None
    fournisseur.rechercher.side_effect=OSError('Hors ligne')
    assert proposer_recherche_externe('Dentiste mardi 14h',fournisseur,autoriser=True)['etat']=='incomplet'


def test_pas_de_recherche_pour_maison_absente():
    fournisseur=Mock()
    r=proposer_recherche_externe('Laporte mardi 14h visio',fournisseur,autoriser=True)
    fournisseur.rechercher.assert_not_called()
    assert r['etat']=='incomplet'

def test_requete_minimale_retire_le_prefixe_rendez_vous_pour_un_etablissement():
    phrase = (
        "j'ai rendez-vous au Centre Hospitalier Bretagne Atlantique "
        "mardi à 14h30 à Vannes"
    )

    assert requete_minimale(phrase) == (
        "Centre Hospitalier Bretagne Atlantique Vannes"
    )
