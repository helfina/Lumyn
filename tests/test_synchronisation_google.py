from unittest.mock import Mock

import httplib2
import pytest
from googleapiclient.errors import HttpError

from lumyn.modules.rendez_vous import agenda_google, stockage
from lumyn.modules.rendez_vous.synchronisation_google import (
    memoriser_reference, synchroniser_google, decider_suppression,
)


def erreur_http(code):
    return HttpError(httplib2.Response({"status": code}), b'{"error":{"message":"secret-test"}}')


def enregistrer(calendrier="famille", identifiant="g1", reference=True):
    rdv = dict(titre="Réunion", date="2026-09-15", heure="10h", lieu="Vannes",
               google_calendar_id=calendrier, google_event_id=identifiant)
    if reference:
        memoriser_reference(rdv)
    return stockage.enregistrer_rendez_vous(rdv)


def service_pour(rdv):
    service = Mock()
    service.calendarList.return_value.get.return_value.execute.return_value = {
        "id": rdv["google_calendar_id"], "accessRole": "owner"}
    evenement = agenda_google.construire_corps_evenement_google(rdv)
    evenement.update(id=rdv["google_event_id"], status="confirmed")
    service.events.return_value.get.return_value.execute.return_value = evenement
    return service, evenement


def test_inchange_aucune_ecriture(monkeypatch):
    rdv = enregistrer()
    service, _ = service_pour(rdv)
    sauvegarde = Mock(side_effect=AssertionError("inutile"))
    monkeypatch.setattr(stockage, "sauvegarder_rendez_vous", sauvegarde)
    assert synchroniser_google(service) == [{"id": rdv["id"], "etat": "inchange"}]
    sauvegarde.assert_not_called()
    service.events.return_value.get.assert_called_once_with(calendarId="famille", eventId="g1")
    service.events.return_value.insert.assert_not_called()


def test_modification_idempotente_redemarrage():
    rdv = enregistrer()
    service, distant = service_pour(rdv)
    distant.update(summary="Déjeuner d'équipe", location="Lorient")
    distant["start"]["dateTime"] = "2026-09-16T11:30:00+02:00"
    distant["end"]["dateTime"] = "2026-09-16T13:00:00+02:00"
    assert synchroniser_google(service)[0]["etat"] == "actualise"
    relu = stockage.charger_rendez_vous()[0]
    assert (relu["titre"], relu["date"], relu["heure"], relu["duree_minutes"]) == (
        "Déjeuner d'équipe", "2026-09-16", "11h30", 90)
    assert relu["id"] == rdv["id"]
    nouveau_service, _ = service_pour(relu)
    assert synchroniser_google(nouveau_service)[0]["etat"] == "inchange"
    assert len(stockage.charger_rendez_vous()) == 1


@pytest.mark.parametrize("code", [404, 410])
def test_suppression_ciblee_et_redemarrage(code):
    rdv = enregistrer()
    service, _ = service_pour(rdv)
    service.events.return_value.get.return_value.execute.side_effect = erreur_http(code)
    decision = synchroniser_google(service)[0]
    assert decision["etat"] == "decision_requise"
    assert stockage.charger_rendez_vous() == [rdv]
    assert decider_suppression(decision) == "conserve"
    assert synchroniser_google(service)[0]["etat"] == "decision_requise"
    assert decider_suppression(decision, supprimer=True) == "supprime"
    assert decider_suppression(decision, supprimer=True) == "supprime"
    assert stockage.charger_rendez_vous() == []
    nouveau_service = Mock()
    assert synchroniser_google(nouveau_service) == []
    assert not nouveau_service.mock_calls
    service.events.return_value.insert.assert_not_called()
    service.events.return_value.delete.assert_not_called()


@pytest.mark.parametrize("erreur", [TimeoutError("secret-test"), OSError("secret-test"),
    *[erreur_http(c) for c in (401, 403, 429, 500, 503)]])
def test_erreurs_conservent_et_reessaient(erreur):
    rdv = enregistrer()
    service, _ = service_pour(rdv)
    service.events.return_value.get.return_value.execute.side_effect = erreur
    resultat = synchroniser_google(service)
    assert resultat[0]["etat"] == "erreur"
    assert "secret-test" not in repr(resultat)
    assert stockage.charger_rendez_vous() == [rdv]
    service.events.return_value.get.return_value.execute.side_effect = None
    assert synchroniser_google(service)[0]["etat"] == "inchange"


@pytest.mark.parametrize("code", [404, 410, 403, 500])
def test_erreur_calendrier_jamais_suppression(code):
    rdv = enregistrer()
    service, _ = service_pour(rdv)
    service.calendarList.return_value.get.return_value.execute.side_effect = erreur_http(code)
    assert synchroniser_google(service)[0]["etat"] == "erreur"
    assert stockage.charger_rendez_vous() == [rdv]
    service.events.assert_not_called()


@pytest.mark.parametrize("reponse", [None, [], {}, "json invalide",
    {"id": "autre"}, {"id": "g1", "status": "cancelled"}])
def test_reponse_invalide_conserve(reponse):
    rdv = enregistrer()
    service, _ = service_pour(rdv)
    service.events.return_value.get.return_value.execute.return_value = reponse
    assert synchroniser_google(service)[0]["etat"] == "erreur"
    assert stockage.charger_rendez_vous() == [rdv]


@pytest.mark.parametrize("code", [404, 410, None])
def test_ancienne_liaison_divergente_conflit(code):
    rdv = enregistrer(reference=False)
    service, distant = service_pour(rdv)
    distant["summary"] = "Changé"
    if code:
        service.events.return_value.get.return_value.execute.side_effect = erreur_http(code)
    assert synchroniser_google(service)[0]["etat"] == ("decision_requise" if code else "conflit")
    assert stockage.charger_rendez_vous() == [rdv]


def test_initialiser_ancienne_liaison_identique():
    rdv = enregistrer(reference=False)
    service, _ = service_pour(rdv)
    assert synchroniser_google(service)[0]["etat"] == "actualise"
    assert "google_reference" in stockage.charger_rendez_vous()[0]
    assert synchroniser_google(service)[0]["etat"] == "inchange"


def test_conflit_deux_cotes():
    rdv = enregistrer()
    service, distant = service_pour(rdv)
    distant["summary"] = "Google"
    local = dict(rdv, titre="Local")
    stockage.modifier_rendez_vous(rdv["id"], local)
    assert synchroniser_google(service)[0]["etat"] == "conflit"
    assert stockage.charger_rendez_vous() == [local]


@pytest.mark.parametrize("suppression", [False, True])
def test_changement_concurrent_identifiants(suppression):
    rdv = enregistrer()
    service, distant = service_pour(rdv)
    distant["summary"] = "Changé"
    def lecture():
        stockage.modifier_rendez_vous(rdv["id"], dict(rdv, google_event_id="nouveau"))
        if suppression:
            raise erreur_http(404)
        return distant
    service.events.return_value.get.return_value.execute.side_effect = lecture
    resultat = synchroniser_google(service)[0]
    assert (decider_suppression(resultat, supprimer=True) if suppression else resultat["etat"]) == "conflit"
    assert stockage.charger_rendez_vous()[0]["google_event_id"] == "nouveau"


@pytest.mark.parametrize("suppression", [False, True])
def test_panne_disque_et_reprise(monkeypatch, suppression):
    rdv = enregistrer()
    service, distant = service_pour(rdv)
    distant["summary"] = "Changé"
    if suppression:
        service.events.return_value.get.return_value.execute.side_effect = erreur_http(410)
    with monkeypatch.context() as m:
        m.setattr(stockage.os, "replace", Mock(side_effect=PermissionError("secret-test")))
        resultat = synchroniser_google(service)[0]
        assert (decider_suppression(resultat, supprimer=True) if suppression else resultat["etat"]) == "erreur"
    assert stockage.charger_rendez_vous() == [rdv]
    resultat = synchroniser_google(service)[0]
    assert (decider_suppression(resultat, supprimer=True) if suppression else resultat["etat"]) == ("supprime" if suppression else "actualise")


def test_plusieurs_calendriers_erreur_isolee():
    a = enregistrer()
    b = enregistrer("travail", "g2")
    service, distant = service_pour(b)
    distant["summary"] = "Changé"
    service.calendarList.return_value.get.return_value.execute.side_effect = [
        {"id": "famille", "accessRole": "owner"}, {"id": "travail", "accessRole": "writer"}]
    service.events.return_value.get.return_value.execute.side_effect = [TimeoutError(), distant]
    assert [r["etat"] for r in synchroniser_google(service)] == ["erreur", "actualise"]
    relus = stockage.charger_rendez_vous()
    assert relus[0] == a
    assert relus[1]["google_calendar_id"] == "travail"


def test_local_sans_reseau(monkeypatch):
    stockage.enregistrer_rendez_vous({"titre": "Local"})
    fournisseur = Mock(side_effect=AssertionError("réseau"))
    monkeypatch.setattr(agenda_google, "obtenir_service_google_calendar", fournisseur)
    assert synchroniser_google() == []
    fournisseur.assert_not_called()


@pytest.mark.parametrize("debut,fin", [
    ({"date": "2026-09-16"}, {"date": "2026-09-17"}),
    ({"dateTime": "2026-09-16T10:00:00"}, {"dateTime": "2026-09-16T11:00:00"}),
    ({"dateTime": "2026-10-25T02:30:00+01:00"}, {"dateTime": "2026-10-25T03:30:00+01:00"}),
    ({"dateTime": "2026-09-16T10:00:30+02:00"}, {"dateTime": "2026-09-16T11:00:30+02:00"}),
])
def test_horaires_non_representables(debut, fin):
    rdv = enregistrer()
    service, distant = service_pour(rdv)
    distant.update(start=debut, end=fin)
    assert synchroniser_google(service)[0]["etat"] == "erreur"
    assert stockage.charger_rendez_vous() == [rdv]


def test_utc_converti_paris_sans_decalage_repete():
    rdv = enregistrer()
    service, distant = service_pour(rdv)
    distant.update(start={"dateTime": "2026-12-31T23:30:00Z"},
                   end={"dateTime": "2027-01-01T00:30:00Z"})
    assert synchroniser_google(service)[0]["etat"] == "actualise"
    relu = stockage.charger_rendez_vous()[0]
    assert (relu["date"], relu["heure"]) == ("2027-01-01", "00h30")
    assert synchroniser_google(service)[0]["etat"] == "inchange"


def test_oauth_ne_supprime_pas(monkeypatch):
    from google.auth.exceptions import RefreshError
    rdv = enregistrer()
    monkeypatch.setattr(agenda_google, "obtenir_service_google_calendar",
                        Mock(side_effect=RefreshError("secret-test")))
    assert synchroniser_google()[0]["etat"] == "erreur"
    assert stockage.charger_rendez_vous() == [rdv]
