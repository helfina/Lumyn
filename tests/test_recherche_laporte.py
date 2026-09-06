import asyncio
from unittest.mock import Mock

from lumyn.modules.lieux import stockage as carnet
from lumyn.modules.rendez_vous import stockage as rendez_vous
from lumyn.modules.rendez_vous import ui
from lumyn.modules.synapse.orchestrateur_rendez_vous import preparer_rendez_vous_synapse
from lumyn.modules.synapse.interpreteur_rendez_vous import extraire_indices_deterministes
from lumyn.modules.synapse.recherche_lieux import PropositionLieu, proposer_recherche_externe
from lumyn.modules.synapse.recherche_ui import RechercheLieuxUI
from lumyn.modules.synapse.selection_lieux import choisir_proposition
from tests.test_ui import interface


PHRASE = "j'ai rendez-vous avec ma psy Laporte jeudi vers 10h à son cabinet de Lorient"
INDICES = {'personne': 'Laporte', 'profession': 'psy', 'ville': 'Lorient'}


class InterpreteurLocal:
    def interpreter(self, texte):
        assert texte == PHRASE
        return dict(INDICES)


def test_indices_laporte_extraits_sans_ollama_et_cabinet_reste_un_indice():
    assert extraire_indices_deterministes(PHRASE) == INDICES
    resultat = preparer_rendez_vous_synapse(PHRASE, [])
    assert resultat['rendez_vous']['lieu'] is None
    assert resultat['rendez_vous']['lieu_explicite'] == 'son cabinet de Lorient'


def proposition(nom, adresse, profession='', ville=''):
    return PropositionLieu(nom, adresse, 'FINESS — source publique', profession, ville)


def test_titre_reconstruit_depuis_indices_sans_fragments_naturels():
    resultat = preparer_rendez_vous_synapse(PHRASE, [], indices_locaux=INDICES)
    assert resultat['rendez_vous']['titre'] == 'Rdv psy Laporte'
    titre = resultat['rendez_vous']['titre'].casefold()
    assert "j'ai rendez-vous avec" not in titre
    assert ' vers' not in titre
    assert 'son cabinet' not in titre


def test_nom_canonique_du_carnet_prime_et_adresse_unique_est_resolue():
    lieux = [{'id': 'laporte', 'nom': 'Dr Laporte', 'alias': ['Laporte'],
              'profession': 'psy', 'adresses': [
                  {'adresse': '2 rue Exemple, Lorient', 'favorite': True}]}]
    resultat = preparer_rendez_vous_synapse(PHRASE, lieux, indices_locaux=INDICES)
    assert resultat['rendez_vous']['titre'] == 'Rdv psy Dr Laporte'
    assert resultat['rendez_vous']['lieu'] == '2 rue Exemple, Lorient'
    assert resultat['rendez_vous']['lieu_source'] == 'carnet'
    assert resultat['etat'] == 'confirmation'


def test_titre_profession_seule_ninvente_pas_de_civilite():
    indices = {'profession': 'psy', 'ville': 'Lorient'}
    resultat = preparer_rendez_vous_synapse(
        'rendez-vous psy jeudi 10h à Lorient', [], indices_locaux=indices)
    assert resultat['rendez_vous']['titre'] == 'Rdv psy'
    assert 'Dr' not in resultat['rendez_vous']['titre']


def test_lieu_vague_non_confirmable_et_adresse_structuree_confirmable():
    vague = preparer_rendez_vous_synapse(PHRASE, [], indices_locaux=INDICES)
    assert vague['etat'] == 'incomplet'
    assert vague['rendez_vous']['lieu'] is None
    structuree = preparer_rendez_vous_synapse(
        "psy Laporte jeudi 10h à 12 rue des Fleurs, Lorient", [])
    assert structuree['etat'] == 'confirmation'


def test_ui_lieu_vague_garde_confirmation_desactivee(interface):
    interface.rdv_input.value = PHRASE
    interface.analyser_rendez_vous(None)
    assert not interface.confirmer_button.enabled


def test_analyser_resout_deterministe_avant_ollama_et_sans_internet(
        interface):
    local = Mock(interpreter=Mock(side_effect=TimeoutError('Ollama trop lent')))
    public = Mock()
    web = Mock()
    carnet.enregistrer_lieu({
        'nom': 'Dr Laporte', 'alias': ['Laporte'], 'profession': 'psy',
        'adresses': [{'adresse': '2 rue Exemple, 56100 Lorient',
                      'favorite': True}],
    })
    interface.interpreteur_local = local
    interface.fournisseur_lieux = public
    interface.fournisseur_ia = web
    interface.rdv_input.value = PHRASE

    interface.analyser_rendez_vous(None)

    rdv = interface.resultat_courant['rendez_vous']
    assert interface.resultat_courant['etat'] == 'confirmation'
    assert rdv['titre'] == 'Rdv psy Dr Laporte'
    assert rdv['date'].isoformat() == '2026-09-10'
    assert rdv['heure'] == '10h'
    assert rdv['lieu'] == '2 rue Exemple, 56100 Lorient'
    assert rdv['lieu_source'] == 'carnet'
    assert interface.confirmer_button.enabled
    local.interpreter.assert_not_called()
    public.rechercher.assert_not_called()
    web.rechercher.assert_not_called()


def test_analyser_demande_choix_si_deux_adresses_carnet_a_lorient(interface):
    local = Mock(interpreter=Mock(side_effect=TimeoutError('Ollama trop lent')))
    public = Mock()
    carnet.enregistrer_lieu({
        'nom': 'Dr Laporte', 'alias': ['Laporte'], 'profession': 'psy',
        'adresses': [
            {'adresse': '2 rue Exemple, 56100 Lorient', 'favorite': True},
            {'adresse': '8 avenue Exemple, 56100 Lorient', 'favorite': False},
        ],
    })
    interface.interpreteur_local = local
    interface.fournisseur_lieux = public
    interface.rdv_input.value = PHRASE

    interface.analyser_rendez_vous(None)

    assert interface.resultat_courant['etat'] == 'ambigu'
    assert 'Plusieurs adresses du Carnet' in interface.resultat_courant['message']
    assert not interface.confirmer_button.enabled
    local.interpreter.assert_not_called()
    public.rechercher.assert_not_called()


def test_analyser_demande_choix_si_deux_fiches_carnet_correspondent(interface):
    local = Mock(interpreter=Mock(side_effect=TimeoutError('Ollama trop lent')))
    public = Mock()
    for suffixe, adresse in (
        ('A', '2 rue Exemple, 56100 Lorient'),
        ('B', '8 avenue Exemple, 56100 Lorient'),
    ):
        carnet.enregistrer_lieu({
            'nom': 'Dr Laporte ' + suffixe, 'alias': ['Laporte'],
            'profession': 'psy',
            'adresses': [{'adresse': adresse, 'favorite': True}],
        })
    interface.interpreteur_local = local
    interface.fournisseur_lieux = public
    interface.rdv_input.value = PHRASE

    interface.analyser_rendez_vous(None)

    assert interface.resultat_courant['etat'] == 'ambigu'
    assert 'Plusieurs fiches correspondent' in interface.resultat_courant['message']
    assert not interface.confirmer_button.enabled
    local.interpreter.assert_not_called()
    public.rechercher.assert_not_called()


def test_resultats_publics_hors_sujet_sont_tous_rejetes():
    public = Mock(rechercher=Mock(return_value=[
        proposition('La Poste', '1 rue Paris, 75001 Paris', ville='Paris'),
        proposition('La Poste Lorient', '1 rue Test, 56100 Lorient', ville='Lorient'),
        proposition('EDF', '2 rue Paris, 75002 Paris', ville='Paris'),
        proposition('Elior', '3 rue Paris, 75003 Paris', ville='Paris'),
        proposition('Ville de Paris', '4 place Hôtel de Ville, 75004 Paris', ville='Paris'),
    ]))
    resultat = proposer_recherche_externe(
        PHRASE, public, autoriser=True, interpreteur_local=InterpreteurLocal())
    assert resultat['propositions_externes'] == []
    assert resultat['etat'] == 'incomplet'


def test_resultat_public_pertinent_est_conserve_sans_fallback_web():
    pertinent = proposition('Cabinet Laporte', '8 rue Test, 56100 Lorient', 'psy', 'Lorient')
    public = Mock(rechercher=Mock(return_value=[pertinent]))
    web = Mock()
    resultat = proposer_recherche_externe(
        PHRASE, public, autoriser=True, fournisseur_ia=web, autoriser_ia=True,
        interpreteur_local=InterpreteurLocal())
    assert resultat['propositions_externes'] == [pertinent]
    assert resultat['fournisseur_utilise'] == 'structure'
    web.rechercher.assert_not_called()


def test_public_non_pertinent_equivaut_a_zero_et_declenche_web():
    web_laporte = PropositionLieu(
        'Cabinet Laporte', '8 rue Test, 56100 Lorient',
        'Ollama Web Search — https://source.example', 'psy', 'Lorient')
    public = Mock(rechercher=Mock(return_value=[
        proposition('La Poste', '1 rue Paris, 75001 Paris', ville='Paris')]))
    web = Mock(rechercher=Mock(return_value=[web_laporte]))
    resultat = proposer_recherche_externe(
        PHRASE, public, autoriser=True, fournisseur_ia=web, autoriser_ia=True,
        interpreteur_local=InterpreteurLocal())
    assert resultat['propositions_externes'] == [web_laporte]
    assert resultat['fournisseur_utilise'] == 'ia_web'
    web.rechercher.assert_called_once()


def test_choix_explicite_conserve_le_titre_structure():
    choix = PropositionLieu(
        'Cabinet du Dr Laporte', '8 rue Test, 56100 Lorient',
        'Ollama Web Search — https://source.example', 'psy', 'Lorient')
    prepare = preparer_rendez_vous_synapse(PHRASE, [], indices_locaux=INDICES)
    resultat = choisir_proposition(
        PHRASE, choix, [choix], resultat_prepare=prepare)
    assert resultat['rendez_vous']['titre'] == 'Rdv psy Laporte'
    assert resultat['etat'] == 'confirmation'


def test_recherche_necrit_ni_carnet_ni_rendez_vous_et_ui_neconfirme_pas(
        interface, monkeypatch):
    creation_google = Mock()
    monkeypatch.setattr(ui, 'creer_evenement_google', creation_google)
    public = Mock(rechercher=Mock(return_value=[
        proposition('La Poste', '1 rue Paris, 75001 Paris', ville='Paris')]))
    panneau = RechercheLieuxUI(interface, public, interpreteur_local=InterpreteurLocal())
    interface.rdv_input.value = PHRASE
    asyncio.run(panneau.rechercher())
    assert panneau.propositions == []
    assert not interface.confirmer_button.enabled
    interface.confirmer_rendez_vous(None)
    creation_google.assert_not_called()
    assert not carnet.FICHIER_LIEUX.exists()
    assert rendez_vous.charger_rendez_vous() == []
