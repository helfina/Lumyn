from datetime import date
import json
import pytest
from lumyn.modules.rendez_vous import stockage as s


def test_cycle_local_et_metadonnees():
    rdv = s.enregistrer_rendez_vous({'titre': 'CAF', 'date': date(2026, 9, 8), 'google_event_id': 'abc'})
    assert s.charger_rendez_vous() == [rdv]
    assert rdv['date'] == '2026-09-08'
    nouveau = s.modifier_rendez_vous(rdv['id'], dict(rdv, titre='École'))
    assert nouveau['google_event_id'] == 'abc'
    assert s.supprimer_rendez_vous(rdv['id']) is True
    assert s.charger_rendez_vous() == []
    assert s.supprimer_rendez_vous(rdv['id']) is False
    assert s.modifier_rendez_vous('absent', {}) is None


def test_migration_anciens_identifiants_stables():
    s.FICHIER_RENDEZ_VOUS.write_text('[{"titre": "Ancien"}]')
    premier = s.charger_rendez_vous()
    assert premier[0]['id']
    assert s.charger_rendez_vous() == premier


@pytest.mark.parametrize('contenu', ['{cassé', '{}', '[42]', 'null'])
def test_fichier_invalide_non_ecrase(contenu):
    s.FICHIER_RENDEZ_VOUS.write_text(contenu)
    with pytest.raises(ValueError):
        s.enregistrer_rendez_vous({'titre': 'Nouveau'})
    assert s.FICHIER_RENDEZ_VOUS.read_text() == contenu


def test_echec_serialisation_conserve_fichier():
    rdv = s.enregistrer_rendez_vous({'titre': 'Original'})
    avant = s.FICHIER_RENDEZ_VOUS.read_bytes()
    with pytest.raises(TypeError):
        s.sauvegarder_rendez_vous([rdv, {'invalide': object()}])
    assert s.FICHIER_RENDEZ_VOUS.read_bytes() == avant


def test_echec_remplacement_conserve_fichier(monkeypatch):
    s.enregistrer_rendez_vous({'titre': 'Original'})
    avant = s.FICHIER_RENDEZ_VOUS.read_bytes()
    def echec(*args):
        raise PermissionError('Fichier verrouillé')
    monkeypatch.setattr('os.replace', echec)
    with pytest.raises(PermissionError):
        s.enregistrer_rendez_vous({'titre': 'Nouveau'})
    assert s.FICHIER_RENDEZ_VOUS.read_bytes() == avant
    assert list(s.DOSSIER_DONNEES.iterdir()) == [s.FICHIER_RENDEZ_VOUS]
