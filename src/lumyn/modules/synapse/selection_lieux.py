"""Choix d'adresse et enregistrement volontaire, indépendants des fournisseurs."""
from copy import deepcopy
from lumyn.modules.lieux.gestion import normaliser_recherche, est_fiche_maison
from lumyn.modules.lieux.stockage import charger_lieux, enregistrer_lieu, modifier_lieu
from lumyn.modules.rendez_vous.gestion import valider_rendez_vous
from lumyn.modules.synapse.orchestrateur_rendez_vous import preparer_rendez_vous_synapse
from lumyn.modules.synapse.recherche_lieux import proposition_valide


def choisir_proposition(texte, proposition, propositions):
    if not proposition_valide(proposition) or proposition not in propositions:
        raise ValueError('Choisis une proposition de cette recherche.')
    resultat = preparer_rendez_vous_synapse(texte)
    rdv = deepcopy(resultat.get('rendez_vous') or {})
    if resultat['etat'] not in ('confirmation', 'incomplet') or rdv.get('erreurs'):
        return resultat
    if rdv.get('lieu_source') in ('carnet', 'maison') or rdv.get('mode') in ('visio','domicile','telephone'):
        return resultat
    rdv.update(titre=proposition.nom, lieu=proposition.adresse, mode='physique',
               lieu_source='externe', lieu_explicite=proposition.adresse,
               lieu_provenance=proposition.source, lieu_id=None)
    rdv['manquants'] = [label for cle, label in
        (('titre','le titre'),('date','la date'),('heure',"l'heure")) if not rdv.get(cle)]
    resultat = valider_rendez_vous(rdv)
    resultat['message'] += '\nSource : ' + proposition.source + '\nAdresse choisie à vérifier avant confirmation.'
    return resultat


def enregistrer_proposition(proposition, *, autoriser=False, fiche_id=None):
    if not autoriser:
        raise ValueError("L'enregistrement dans le Carnet demande un accord distinct.")
    if not proposition_valide(proposition):
        raise ValueError('Proposition invalide.')
    lieux = charger_lieux()
    nom = normaliser_recherche(proposition.nom)
    adresse = normaliser_recherche(proposition.adresse)
    similaires = [f for f in lieux if normaliser_recherche(f['nom']) == nom
        or any(normaliser_recherche(a['adresse']) == adresse for a in f['adresses'])
        or nom in [normaliser_recherche(a) for a in f['alias']]]
    if fiche_id is None and similaires:
        return {'etat':'choix_fiche', 'fiches':similaires}
    nouvelle_adresse = {'adresse':proposition.adresse, 'libelle':proposition.nom,
                        'favorite':False, 'source':proposition.source}
    if fiche_id is not None:
        fiche = next((f for f in similaires if f['id'] == fiche_id), None)
        if fiche is None or est_fiche_maison(fiche):
            raise ValueError('Choisis une fiche similaire hors Maison ; Maison se modifie dans le Carnet.')
        if any(normaliser_recherche(a['adresse']) == adresse for a in fiche['adresses']):
            return {'etat':'enregistre','fiche':fiche}
        nouvelle_adresse['favorite'] = not fiche['adresses']
        fiche['adresses'].append(nouvelle_adresse)
        fiche = modifier_lieu(fiche_id, fiche)
        if fiche is None:
            raise ValueError('La fiche a disparu ; recharge le Carnet.')
    else:
        nouvelle_adresse['favorite'] = True
        fiche = enregistrer_lieu({'nom':proposition.nom, 'profession':proposition.profession or None,
            'adresses':[nouvelle_adresse], 'alias':[], 'source':proposition.source})
    return {'etat':'enregistre','fiche':fiche}
