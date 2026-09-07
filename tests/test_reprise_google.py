"""Pannes partielles avec service Google simulé et vrais fichiers temporaires."""
from copy import deepcopy
import json
from unittest.mock import Mock
import httplib2
import pytest
from googleapiclient.errors import HttpError
from tests.test_ui import interface
from tests.test_agenda_google import service
from lumyn.modules.rendez_vous import agenda_google as g, reprise_google as r, stockage, ui

RDV = {'titre': 'Essai', 'date': '2026-10-12', 'heure': '10h'}


def http(code, raison):
    return HttpError(httplib2.Response({'status': str(code)}),
                     json.dumps({'error': {'errors': [{'reason': raison}]}}).encode())


@pytest.fixture
def google_simule(service):
    evenements = {}
    def inserer(**kwargs):
        corps = deepcopy(kwargs['body'])
        def executer():
            if corps['id'] in evenements:
                raise http(409, 'duplicate')
            evenements[corps['id']] = corps
            return deepcopy(corps)
        return Mock(execute=executer)
    service.events().insert.side_effect = inserer
    service.events().get.side_effect = lambda **kw: Mock(execute=lambda: deepcopy(evenements[kw['eventId']]))
    def supprimer(**kwargs):
        def executer():
            if kwargs['eventId'] not in evenements:
                raise http(410, 'deleted')
            del evenements[kwargs['eventId']]
        return Mock(execute=executer)
    service.events().delete.side_effect = supprimer
    return service, evenements


def test_creation_reponse_perdue_reutilise_id_apres_relecture_journal(google_simule):
    service, evenements = google_simule
    inserer = service.events().insert.side_effect
    def perdre_reponse(**kw):
        requete = inserer(**kw)
        def execute():
            requete.execute()
            raise TimeoutError('Réponse perdue')
        return Mock(execute=execute)
    service.events().insert.side_effect = perdre_reponse
    with pytest.raises(TimeoutError): g.creer_evenement_google(RDV, 'famille')
    assert len(evenements) == 1
    # Aucune mémoire globale d'opération : seconde tentative depuis le JSON.
    service.events().insert.side_effect = inserer
    resultat = g.creer_evenement_google(RDV, 'famille')
    assert len(evenements) == 1 and resultat['id'] == next(iter(evenements))
    assert 'Essai' not in r.FICHIER_REPRISE.read_text()


@pytest.mark.parametrize('champ,valeur', [('summary', 'Autre'), ('status', 'cancelled'),
                                        ('extendedProperties', {}), ('start', {})])
def test_conflit_contenu_bloque_sans_ecraser(google_simule, champ, valeur):
    service, evenements = google_simule
    original = g.creer_evenement_google(RDV, 'famille')
    evenements[original['id']][champ] = valeur
    with pytest.raises(RuntimeError, match='Vérifie'): g.creer_evenement_google(RDV, 'famille')
    assert len(evenements) == 1
    service.events().update.assert_not_called()


@pytest.mark.parametrize('statut,raison', [(403,'forbidden'), (404,'notFound'),
                                         (410,'fullSyncRequired'), (500,'backendError')])
def test_erreur_suppression_non_confondue_avec_absence(service,statut,raison):
    service.events().delete().execute.side_effect = http(statut,raison)
    with pytest.raises(HttpError):g.supprimer_evenement_google('famille','evt')
    assert ('famille','evt') not in g._EVENEMENTS_GOOGLE_SUPPRIMES


def test_suppression_deja_effectuee(service):
    service.events().delete().execute.side_effect = http(410,'deleted')
    assert g.supprimer_evenement_google('famille','evt')
    assert ('famille','evt') in g._EVENEMENTS_GOOGLE_SUPPRIMES


@pytest.mark.parametrize('contenu', ['{cassé', '[]', '{"x": {"id": "invalide"}}'])
def test_journal_illisible_bloque_avant_google(service,contenu):
    r.FICHIER_REPRISE.write_text(contenu)
    with pytest.raises(ValueError):g.creer_evenement_google(RDV,'famille')
    service.events().insert.assert_not_called()
    assert r.FICHIER_REPRISE.read_text() == contenu


def test_panne_journal_avant_google(service,monkeypatch):
    monkeypatch.setattr(r.os,'replace',Mock(side_effect=OSError('Disque plein')))
    with pytest.raises(OSError):g.creer_evenement_google(RDV,'famille')
    service.events().insert.assert_not_called()


def test_creation_panne_locale_et_compensation_reprise(interface,google_simule,monkeypatch):
    service, evenements = google_simule
    sauver = ui.enregistrer_rendez_vous
    supprimer = service.events().delete.side_effect
    monkeypatch.setattr(ui,'enregistrer_rendez_vous',Mock(side_effect=OSError('Disque plein')))
    service.events().delete.side_effect = OSError('Hors ligne')
    with pytest.raises(OSError):interface._creer_rendez_vous_lie(RDV)
    assert len(evenements) == 1 and stockage.charger_rendez_vous() == []
    monkeypatch.setattr(ui,'enregistrer_rendez_vous',sauver)
    service.events().delete.side_effect = supprimer
    interface._creer_rendez_vous_lie(RDV)
    assert len(evenements) == len(stockage.charger_rendez_vous()) == 1
    assert json.loads(r.FICHIER_REPRISE.read_text()) == {}


def test_creation_compensation_reussie_nouvel_id_a_la_reprise(interface,google_simule,monkeypatch):
    service, evenements = google_simule
    sauver = ui.enregistrer_rendez_vous
    monkeypatch.setattr(ui,'enregistrer_rendez_vous',Mock(side_effect=OSError('Panne')))
    with pytest.raises(OSError):interface._creer_rendez_vous_lie(RDV)
    assert not evenements
    premier_id = service.events().insert.call_args.kwargs['body']['id']
    monkeypatch.setattr(ui,'enregistrer_rendez_vous',sauver)
    resultat = interface._creer_rendez_vous_lie(RDV)
    assert resultat['google_event_id'] != premier_id


def test_ecriture_locale_reussie_nettoyage_journal_echoue_pas_de_doublon(interface,google_simule,monkeypatch):
    terminer = ui.terminer_creation
    monkeypatch.setattr(ui,'terminer_creation',Mock(side_effect=OSError('Panne journal')))
    with pytest.raises(OSError):interface._creer_rendez_vous_lie(RDV)
    original = stockage.charger_rendez_vous()[0]
    monkeypatch.setattr(ui,'terminer_creation',terminer)
    resultat = interface._creer_rendez_vous_lie(RDV)
    assert resultat['id'] == original['id']
    assert len(stockage.charger_rendez_vous()) == len(google_simule[1]) == 1


def test_suppression_panne_locale_reprise_sans_recreation(interface,google_simule,monkeypatch):
    interface._creer_rendez_vous_lie(RDV)
    original = stockage.charger_rendez_vous()[0]
    supprimer = ui.supprimer_rendez_vous
    monkeypatch.setattr(ui,'supprimer_rendez_vous',Mock(side_effect=OSError('Disque plein')))
    with pytest.raises(RuntimeError,match='clique à nouveau'):interface._supprimer_rendez_vous_lie(original)
    assert not google_simule[1] and stockage.charger_rendez_vous() == [original]
    monkeypatch.setattr(ui,'supprimer_rendez_vous',supprimer)
    interface._supprimer_rendez_vous_lie(original)
    assert stockage.charger_rendez_vous() == []
    assert google_simule[0].events().insert.call_count == 1


def test_nouvelle_creation_identique_apres_succes_reste_possible(interface,google_simule):
    interface._creer_rendez_vous_lie(RDV)
    interface._creer_rendez_vous_lie(RDV)
    assert len(google_simule[1]) == len(stockage.charger_rendez_vous()) == 2


def test_move_update_timeout_retour_contenu_et_id(interface,monkeypatch):
    original = stockage.enregistrer_rendez_vous(dict(RDV,google_event_id='g1',google_calendar_id='autre'))
    interface.rendez_vous_en_modification = original
    deplacer = Mock(side_effect=[{'id':'g2'}, {'id':'g3'}])
    modifier = Mock(side_effect=[TimeoutError('Réponse perdue'), {'id':'g2'}])
    monkeypatch.setattr(ui,'deplacer_evenement_google',deplacer)
    monkeypatch.setattr(ui,'modifier_evenement_google',modifier)
    with pytest.raises(RuntimeError):interface._modifier_rendez_vous_lie(dict(RDV,heure='11h'))
    assert modifier.call_args.args[0]['heure'] == '10h'
    assert deplacer.call_args.args == ('famille','autre','g2')
    assert stockage.charger_rendez_vous()[0]['google_event_id'] == 'g3'
    assert interface.rendez_vous_en_modification['google_event_id'] == 'g3'


def test_rollback_contenu_echoue_tente_quand_meme_retour(interface,monkeypatch):
    original = dict(RDV,id='local',google_event_id='g1',google_calendar_id='autre')
    deplacer = Mock(return_value={'id':'g1'})
    monkeypatch.setattr(ui,'modifier_evenement_google',Mock(side_effect=OSError('Hors ligne')))
    monkeypatch.setattr(ui,'deplacer_evenement_google',deplacer)
    with pytest.raises(RuntimeError,match='Restauration incomplète'):
        interface._restaurer_apres_modification(original,'famille','g1')
    deplacer.assert_called_once_with('famille','autre','g1')


def test_move_reponse_perdue_pas_de_creation_ou_ecriture_locale(interface,monkeypatch):
    original = stockage.enregistrer_rendez_vous(dict(RDV,google_event_id='g1',google_calendar_id='autre'))
    interface.rendez_vous_en_modification = original
    monkeypatch.setattr(ui,'deplacer_evenement_google',Mock(side_effect=TimeoutError('Réponse perdue')))
    creation = Mock()
    monkeypatch.setattr(ui,'creer_evenement_google',creation)
    with pytest.raises(RuntimeError,match='réponse perdue'):
        interface._modifier_rendez_vous_lie(dict(RDV,heure='11h'))
    creation.assert_not_called()
    assert stockage.charger_rendez_vous() == [original]


def nouvelle_instance():
    instance = ui.InterfaceRendezVous()
    instance.construire()
    return instance


def test_redemarrage_apres_reservation_non_envoyee_reutilise_identifiant(
        interface, google_simule):
    service, evenements = google_simule
    corps = g.construire_corps_evenement_google(RDV)
    identifiant = r.reserver_creation('famille', corps)

    redemarree = nouvelle_instance()
    resultat = redemarree._creer_rendez_vous_lie(RDV)

    assert resultat['google_event_id'] == identifiant
    assert list(evenements) == [identifiant]
    assert len(stockage.charger_rendez_vous()) == 1


def test_redemarrage_apres_reponse_google_perdue_ne_duplique_pas(
        interface, google_simule):
    service, evenements = google_simule
    inserer = service.events().insert.side_effect

    def perdre_reponse(**kwargs):
        requete = inserer(**kwargs)
        return Mock(execute=lambda: (requete.execute(), (_ for _ in ()).throw(
            TimeoutError('Réponse perdue')))[1])

    service.events().insert.side_effect = perdre_reponse
    with pytest.raises(TimeoutError):
        g.creer_evenement_google(RDV, 'famille')
    service.events().insert.side_effect = inserer

    resultat = nouvelle_instance()._creer_rendez_vous_lie(RDV)
    assert len(evenements) == 1
    assert len(stockage.charger_rendez_vous()) == 1
    assert resultat['google_event_id'] == next(iter(evenements))


def test_redemarrage_apres_google_reussi_et_panne_locale_reprend_sans_doublon(
        interface, google_simule, monkeypatch):
    service, evenements = google_simule
    sauvegarde = ui.enregistrer_rendez_vous
    suppression = service.events().delete.side_effect
    monkeypatch.setattr(ui, 'enregistrer_rendez_vous',
                        Mock(side_effect=PermissionError('lecture seule')))
    service.events().delete.side_effect = OSError('suppression indisponible')
    with pytest.raises(PermissionError):
        interface._creer_rendez_vous_lie(RDV)
    assert len(evenements) == 1

    monkeypatch.setattr(ui, 'enregistrer_rendez_vous', sauvegarde)
    service.events().delete.side_effect = suppression
    resultat = nouvelle_instance()._creer_rendez_vous_lie(RDV)
    assert len(evenements) == len(stockage.charger_rendez_vous()) == 1
    assert resultat['google_event_id'] == next(iter(evenements))


def test_redemarrage_apres_delete_google_et_panne_locale_ne_recree_jamais(
        interface, google_simule, monkeypatch):
    interface._creer_rendez_vous_lie(RDV)
    original = stockage.charger_rendez_vous()[0]
    suppression_locale = ui.supprimer_rendez_vous
    monkeypatch.setattr(ui, 'supprimer_rendez_vous',
                        Mock(side_effect=OSError('disque plein')))
    with pytest.raises(RuntimeError, match='clique à nouveau'):
        interface._supprimer_rendez_vous_lie(original)
    assert google_simule[1] == {}

    monkeypatch.setattr(ui, 'supprimer_rendez_vous', suppression_locale)
    redemarree = nouvelle_instance()
    redemarree._supprimer_rendez_vous_lie(original)
    assert stockage.charger_rendez_vous() == []
    assert google_simule[0].events().insert.call_count == 1


def test_redemarrage_apres_update_interrompu_garde_identite_et_ne_cree_pas(
        interface, monkeypatch):
    original = stockage.enregistrer_rendez_vous(dict(
        RDV, google_event_id='g1', google_calendar_id='famille'))
    modification = Mock(side_effect=TimeoutError('réponse perdue'))
    creation = Mock()
    monkeypatch.setattr(ui, 'modifier_evenement_google', modification)
    monkeypatch.setattr(ui, 'creer_evenement_google', creation)

    redemarree = nouvelle_instance()
    redemarree.rendez_vous_en_modification = stockage.charger_rendez_vous()[0]
    with pytest.raises(RuntimeError, match='réponse perdue'):
        redemarree._modifier_rendez_vous_lie(dict(RDV, heure='11h'))

    assert stockage.charger_rendez_vous() == [original]
    creation.assert_not_called()


def test_journal_absent_ou_vide_est_un_etat_normal():
    assert r._charger() == {}
    r.FICHIER_REPRISE.write_text('{}', encoding='utf-8')
    assert r._charger() == {}


def test_redemarrage_apres_move_interrompu_ne_cree_rien(
        interface, monkeypatch):
    original = stockage.enregistrer_rendez_vous(dict(
        RDV, google_event_id='g1', google_calendar_id='autre'))
    deplacement = Mock(side_effect=TimeoutError('réponse perdue'))
    creation = Mock()
    monkeypatch.setattr(ui, 'deplacer_evenement_google', deplacement)
    monkeypatch.setattr(ui, 'creer_evenement_google', creation)

    redemarree = nouvelle_instance()
    redemarree.rendez_vous_en_modification = stockage.charger_rendez_vous()[0]
    with pytest.raises(RuntimeError, match='réponse perdue'):
        redemarree._modifier_rendez_vous_lie(dict(RDV, heure='11h'))

    assert stockage.charger_rendez_vous() == [original]
    creation.assert_not_called()


def test_fichier_local_corrompu_bloque_create_avant_google(interface, monkeypatch):
    contenu = '[{"id":"duplique"},{"id":"duplique"}]'
    stockage.FICHIER_RENDEZ_VOUS.write_text(contenu, encoding='utf-8')
    creation = Mock()
    monkeypatch.setattr(ui, 'creer_evenement_google', creation)
    with pytest.raises(ValueError, match='même identifiant'):
        nouvelle_instance()._creer_rendez_vous_lie(RDV)
    creation.assert_not_called()
    assert stockage.FICHIER_RENDEZ_VOUS.read_text(encoding='utf-8') == contenu
