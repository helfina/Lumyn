"""Réservations persistantes d'identifiants, avant toute création Google.

Un seul processus écrivain, comme le stockage principal. Aucun contenu de
rendez-vous ni secret : empreinte de la demande, calendrier et identifiant.
"""
import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path

FICHIER_REPRISE = Path.home() / '.lumyn' / 'creations_google.json'


def _charger():
    if not FICHIER_REPRISE.exists():
        return {}
    try:
        donnees = json.loads(FICHIER_REPRISE.read_text(encoding='utf-8'))
        if not isinstance(donnees, dict) or not all(
            isinstance(k, str) and isinstance(v, dict)
            and isinstance(v.get('id'), str) and len(v['id']) == 32
            and all(c in '0123456789abcdef' for c in v['id'])
            and isinstance(v.get('calendrier'), str)
            for k, v in donnees.items()
        ):
            raise ValueError('Format invalide')
        return donnees
    except (ValueError, UnicodeError) as erreur:
        raise ValueError('Le journal de reprise Google est illisible ; il est conservé. '
                         'Vérifie les créations en attente avant de le restaurer.') from erreur


def _sauvegarder(donnees):
    contenu = json.dumps(donnees, ensure_ascii=False, indent=2)
    FICHIER_REPRISE.parent.mkdir(parents=True, exist_ok=True)
    temporaire = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                dir=FICHIER_REPRISE.parent, prefix='reprise-', suffix='.tmp', delete=False) as f:
            temporaire = Path(f.name)
            f.write(contenu)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporaire, FICHIER_REPRISE)
    finally:
        if temporaire is not None:
            temporaire.unlink(missing_ok=True)


def reserver_creation(calendrier, corps):
    cle = hashlib.sha256(json.dumps([calendrier, corps], sort_keys=True,
                                   ensure_ascii=False).encode()).hexdigest()
    donnees = _charger()
    if cle not in donnees:
        donnees[cle] = {'id': uuid.uuid4().hex, 'calendrier': calendrier}
        _sauvegarder(donnees)
    return donnees[cle]['id']


def terminer_creation(calendrier, evenement_id):
    donnees = _charger()
    restantes = {k: v for k, v in donnees.items()
                 if (v['calendrier'], v['id']) != (calendrier, evenement_id)}
    if restantes != donnees:
        _sauvegarder(restantes)
