"""Réconciliation explicite des rendez-vous liés, sans écriture Google."""

from copy import deepcopy
from datetime import datetime, timezone

from googleapiclient.errors import HttpError

from lumyn.modules.rendez_vous import agenda_google, stockage


def projection_locale(rdv):
    """Compare les seuls champs représentables, dans le fuseau Lumyn."""
    corps = agenda_google.construire_corps_evenement_google(rdv)
    return {k: corps.get(k, "") for k in ("summary", "location", "start", "end")}


def memoriser_reference(rdv):
    """Référence locale après une écriture Google réussie, sans secret."""
    rdv["google_reference"] = {
        "calendrier": rdv["google_calendar_id"],
        "evenement": rdv["google_event_id"],
        "contenu": projection_locale(rdv),
    }


def convertir_evenement(evenement, original):
    """Refuse les formats impossibles à réémettre sans perte par Lumyn."""
    if not isinstance(evenement, dict) or evenement.get("id") != original["google_event_id"]:
        raise ValueError("Identité distante incohérente.")
    if evenement.get("status") not in ("confirmed", "tentative"):
        raise ValueError("État distant ambigu.")
    if evenement.get("recurrence") or evenement.get("recurringEventId"):
        raise ValueError("Récurrence non représentable.")
    titre = evenement.get("summary")
    lieu = evenement.get("location", "")
    if not isinstance(titre, str) or not titre.strip() or not isinstance(lieu, str):
        raise ValueError("Contenu distant incomplet.")
    debut = datetime.fromisoformat(evenement["start"]["dateTime"])
    fin = datetime.fromisoformat(evenement["end"]["dateTime"])
    if debut.tzinfo is None or fin.tzinfo is None:
        raise ValueError("Fuseau distant absent.")
    secondes = (fin.astimezone(timezone.utc) - debut.astimezone(timezone.utc)).total_seconds()
    debut = debut.astimezone(agenda_google.FUSEAU_LUMYN)
    if secondes <= 0 or secondes % 60 or debut.second or debut.microsecond or debut.fold:
        raise ValueError("Horaire distant non représentable.")
    nouveau = deepcopy(original)
    nouveau.update(titre=titre, lieu=lieu or None, date=debut.date().isoformat(),
                   heure=debut.strftime("%Hh%M"), duree_minutes=int(secondes // 60))
    # Réutiliser la validation des heures inexistantes et du fuseau de l'adaptateur.
    projection_locale(nouveau)
    return nouveau


def _reference_valide(rdv):
    ref = rdv.get("google_reference")
    return (isinstance(ref, dict)
            and ref.get("calendrier") == rdv.get("google_calendar_id")
            and ref.get("evenement") == rdv.get("google_event_id")
            and isinstance(ref.get("contenu"), dict))


def _appliquer(original, nouveau):
    """Compare toute la version relue sous le verrou commun avant remplacement."""
    with stockage._VERROU_ECRITURE:
        liste = stockage.charger_rendez_vous()
        for i, courant in enumerate(liste):
            if courant.get("id") == original["id"]:
                if courant != original:
                    return "conflit"
                if nouveau is None:
                    del liste[i]
                else:
                    liste[i] = nouveau
                stockage.sauvegarder_rendez_vous(liste)
                return "supprime" if nouveau is None else "actualise"
        return "conflit"


def synchroniser_google(service=None):
    """Une passe explicite, erreurs isolées par rendez-vous et jamais affichées brutes.

    Les anciennes liaisons sans référence ne sont initialisées que si leur contenu
    est identique à Google. Toute divergence reste un conflit à réconcilier.
    """
    liste = stockage.charger_rendez_vous()
    resultats = []
    for original in liste:
        calendrier = original.get("google_calendar_id")
        evenement_id = original.get("google_event_id")
        if not calendrier and not evenement_id:
            continue
        etat = "erreur"
        try:
            if not all(isinstance(v, str) and v.strip() for v in (calendrier, evenement_id)):
                raise ValueError("Liaison incomplète.")
            if service is None:
                service = agenda_google.obtenir_service_google_calendar()
            # Un calendrier absent/inaccessible ne prouve jamais une suppression.
            accessible = service.calendarList().get(calendarId=calendrier).execute()
            if (not isinstance(accessible, dict) or accessible.get("id") != calendrier
                    or accessible.get("accessRole") not in ("owner", "writer")):
                raise ValueError("Calendrier inaccessible ou visibilité insuffisante.")
            try:
                evenement = service.events().get(
                    calendarId=calendrier, eventId=evenement_id).execute()
            except HttpError as erreur:
                if erreur.resp.status not in (404, 410):
                    raise
                etat = "decision_requise"
            else:
                nouveau = convertir_evenement(evenement, original)
                local = projection_locale(original)
                distant = projection_locale(nouveau)
                if local == distant:
                    if _reference_valide(original) and original["google_reference"]["contenu"] == local:
                        etat = "inchange"
                    else:
                        nouveau = deepcopy(original)
                        memoriser_reference(nouveau)
                        etat = _appliquer(original, nouveau)
                elif (_reference_valide(original)
                      and original["google_reference"]["contenu"] == local):
                    memoriser_reference(nouveau)
                    etat = _appliquer(original, nouveau)
                else:
                    etat = "conflit"
        except Exception:
            # Frontière externe/disque : aucun détail OAuth ou contenu d'exception
            # dans le résultat UI ; conserver les fichiers et permettre de réessayer.
            etat = "erreur"
        resultat = {"id": original["id"], "etat": etat}
        if etat == "decision_requise":
            resultat["instantane"] = deepcopy(original)
        resultats.append(resultat)
    return resultats


def decider_suppression(resultat, supprimer=False):
    """Conserver par défaut ; seule une décision explicite peut supprimer localement."""
    if not supprimer:
        return "conserve"
    if resultat.get("etat") != "decision_requise" or not isinstance(resultat.get("instantane"), dict):
        return "conflit"
    original = resultat["instantane"]
    try:
        with stockage._VERROU_ECRITURE:
            if not any(r.get("id") == original.get("id") for r in stockage.charger_rendez_vous()):
                return "supprime"
            return _appliquer(original, None)
    except Exception:
        return "erreur"
