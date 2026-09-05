"""Invariants du carnet, indépendants du stockage et de l'interface."""
from copy import deepcopy
import re
import unicodedata
from lumyn.modules.lieux.modele import creer_modele_lieu

ALIAS_MAISON = {'maison', 'domicile', 'chez moi'}


def normaliser_recherche(texte):
    texte = unicodedata.normalize('NFKD', str(texte or ''))
    texte = ''.join(c for c in texte if not unicodedata.combining(c))
    return re.sub(r'\s+', ' ', texte.casefold()).strip()


def est_fiche_maison(lieu):
    return bool({normaliser_recherche(lieu.get('nom'))} .union(
        normaliser_recherche(a) for a in lieu.get('alias') or []
    ) & ALIAS_MAISON)


def preparer_fiche(lieu, ancienne=False):
    """Copie, complète et valide ; conserve tous les champs supplémentaires."""
    if not isinstance(lieu, dict):
        raise ValueError('Une fiche doit être un objet.')
    fiche = {**creer_modele_lieu(), **deepcopy(lieu)}
    if not isinstance(fiche['nom'], str) or not fiche['nom'].strip():
        raise ValueError('Indique un nom pour cette fiche.')
    fiche['nom'] = fiche['nom'].strip()
    alias = fiche['alias'] or []
    if not isinstance(alias, list) or not all(isinstance(a, str) for a in alias):
        raise ValueError('Les alias doivent être une liste de textes.')
    vus = set()
    fiche['alias'] = []
    for a in alias:
        cle = normaliser_recherche(a)
        if cle and cle not in vus:
            vus.add(cle)
            fiche['alias'].append(a.strip())
    adresses = fiche['adresses'] or []
    if not isinstance(adresses, list):
        raise ValueError('Les adresses doivent être une liste.')
    for adresse in adresses:
        if not isinstance(adresse, dict) or not isinstance(adresse.get('adresse'), str):
            raise ValueError('Chaque adresse doit contenir un texte.')
        adresse['adresse'] = adresse['adresse'].strip()
        if not adresse['adresse']:
            raise ValueError('Une adresse enregistrée ne peut pas être vide.')
        adresse.setdefault('favorite', False)
        if not isinstance(adresse['favorite'], bool):
            raise ValueError('Le statut favorite doit être un booléen.')
    if not ancienne and sum(a['favorite'] for a in adresses) > 1:
        raise ValueError('Choisis une seule adresse favorite.')
    fiche['adresses'] = adresses
    return fiche


def verifier_maison_unique(lieux):
    if sum(est_fiche_maison(lieu) for lieu in lieux) > 1:
        raise ValueError('Une fiche Maison existe déjà : modifie-la au lieu d’en créer une autre.')
