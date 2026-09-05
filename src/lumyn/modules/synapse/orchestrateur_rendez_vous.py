"""Priorité à l'intention et au carnet ; jamais de choix arbitraire d'adresse."""
from copy import deepcopy
import re
from lumyn.modules.lieux.stockage import charger_lieux
from lumyn.modules.lieux.gestion import (
    termes_lieu, normaliser_recherche, obtenir_adresse_favorite,
    est_fiche_maison,
)
from lumyn.modules.rendez_vous.gestion import valider_rendez_vous
from lumyn.modules.rendez_vous.resultat import creer_resultat
from lumyn.modules.synapse.interpreteur_rendez_vous import interpreter_rendez_vous


def _contient(texte, terme):
    return bool(terme and re.search(r'(?<!\w)' + re.escape(terme) + r'(?!\w)', texte))


def _candidats(titre, lieux):
    titre = normaliser_recherche(titre)
    trouves = []
    par_metier = []
    for lieu in lieux:
        termes = termes_lieu(lieu)
        nom_court = re.sub(r'^(?:dr\.?|docteur)\s+', '', normaliser_recherche(lieu['nom']))
        termes = termes + [nom_court]
        identifie = any(_contient(titre, t) for t in termes)
        metier = normaliser_recherche(lieu.get('profession'))
        if identifie:
            trouves.append(lieu)
        elif _contient(titre, metier):
            par_metier.append(lieu)
    return trouves or par_metier


def _adresse_explicite(lieu, explicite):
    cle = normaliser_recherche(explicite)
    return [a for a in lieu.get('adresses', []) if
            _contient(normaliser_recherche(a.get('adresse')), cle)
            or _contient(normaliser_recherche(a.get('libelle')), cle)]


def preparer_rendez_vous_synapse(texte, lieux=None):
    """Prépare un résumé validable ; n'écrit rien et ne contacte pas Google."""
    if not texte.strip():
        return creer_resultat('vide', "Écris d'abord un rendez-vous.")
    interpretation = interpreter_rendez_vous(texte)
    rdv = deepcopy(interpretation['rendez_vous'])
    ambiguities = list(interpretation['ambiguities'])
    # Les erreurs de date/heure restent bloquantes avant toute résolution.
    if rdv['erreurs']:
        return valider_rendez_vous(rdv)
    try:
        lieux = charger_lieux() if lieux is None else deepcopy(lieux)
    except (ValueError, OSError) as erreur:
        return creer_resultat('erreur', f'Impossible de lire le carnet : {erreur}', rdv)
    mode = interpretation['mode']
    explicite = interpretation['lieu_explicite']
    candidats = _candidats(interpretation['titre'], lieux)
    fiche = None
    adresse = None
    source = 'saisie' if explicite else None
    if mode in ('visio', 'domicile'):
        maisons = [lieu for lieu in lieux if est_fiche_maison(lieu)]
        if len(maisons) == 1:
            fiche = maisons[0]
            adresse = obtenir_adresse_favorite(fiche)
            if adresse is None:
                ambiguities.append('Précise une adresse favorite pour Maison dans le carnet.')
        elif maisons:
            ambiguities.append('Plusieurs fiches Maison existent. Corrige le carnet avant de confirmer.')
        else:
            rdv['manquants'].append("l'adresse de Maison dans le carnet")
        # Le professionnel peut avoir plusieurs sites physiques : cela ne
        # change pas l'adresse Maison en visio ou à domicile.
        if len(candidats) == 1 and not est_fiche_maison(candidats[0]):
            rdv['titre'] = candidats[0]['nom']
        elif len(candidats) > 1:
            ambiguities.append('Plusieurs professionnels correspondent. Précise le nom ou un alias unique.')
        rdv['lieu'] = adresse['adresse'] if adresse else None
        source = 'maison' if adresse else None
    elif mode == 'telephone':
        rdv['lieu'] = None
        source = None
        if len(candidats) == 1:
            rdv['titre'] = candidats[0]['nom']
        elif len(candidats) > 1:
            ambiguities.append('Plusieurs professionnels correspondent. Précise un nom unique.')
    else:
        if not explicite and len(candidats) == 1:
            candidat = candidats[0]
            reste = normaliser_recherche(interpretation['titre'])
            termes = termes_lieu(candidat) + [
                re.sub(r'^(?:dr\.?|docteur)\s+', '', normaliser_recherche(candidat['nom'])),
                normaliser_recherche(candidat.get('profession')),
            ]
            for terme in sorted(set(termes), key=len, reverse=True):
                if terme:
                    reste = re.sub(r'(?<!\w)' + re.escape(terme) + r'(?!\w)', ' ', reste)
            reste = normaliser_recherche(reste)
            if reste:
                if _adresse_explicite(candidat, reste):
                    explicite = reste
                    interpretation['lieu_explicite'] = reste
                else:
                    ambiguities.append('Précise si « ' + reste + ' » fait partie du titre ou du lieu.')
                    candidats = []
        if explicite:
            # Un site explicitement nommé prime sur la favorite.
            compatibles = [c for c in candidats if _adresse_explicite(c, explicite)]
            if compatibles:
                candidats = compatibles
            elif candidats:
                # Le carnet ne doit pas substituer sa favorite à un autre lieu saisi.
                candidats = []
        if len(candidats) > 1:
            ambiguities.append('Plusieurs fiches correspondent : ' + ', '.join(c['nom'] for c in candidats) + '. Précise le lieu ou un alias unique.')
        elif len(candidats) == 1:
            fiche = candidats[0]
            adresses = _adresse_explicite(fiche, explicite) if explicite else []
            adresse = adresses[0] if len(adresses) == 1 else (
                obtenir_adresse_favorite(fiche) if not explicite else None
            )
            if adresse is None:
                if fiche.get('adresses'):
                    ambiguities.append('Plusieurs adresses possibles pour ' + fiche['nom'] + '. Précise le site ou sa favorite dans le carnet.')
                else:
                    rdv['manquants'].append("l'adresse de " + fiche['nom'])
            else:
                rdv['titre'] = fiche['nom']
                rdv['lieu'] = adresse['adresse']
                source = 'carnet'
        if adresse or explicite:
            mode = 'physique'
    if mode == 'physique' and not rdv.get('lieu'):
        rdv['manquants'].append('le lieu')
    suffixes = {'visio':'VISIO', 'domicile':'DOMICILE', 'telephone':'TÉLÉPHONE'}
    if mode in suffixes and rdv['titre']:
        rdv['titre'] += ' — ' + suffixes[mode]
    rdv.update(mode=mode, lieu_source=source, lieu_explicite=explicite,
               lieu_id=fiche.get('id') if fiche else None)
    if ambiguities:
        resultat = creer_resultat('ambigu', '\n'.join(ambiguities), rdv)
    else:
        resultat = valider_rendez_vous(rdv)
    resultat['interpretation'] = interpretation
    resultat['ambiguities'] = ambiguities
    if resultat['etat'] == 'confirmation' and source in ('carnet','maison'):
        resultat['message'] += '\nAdresse issue du carnet personnel.'
    return resultat
