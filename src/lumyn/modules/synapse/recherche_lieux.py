"""Contrat pour un futur fournisseur ; aucune API ni recherche active par défaut."""
from dataclasses import dataclass
import re
import unicodedata
from typing import Protocol, Sequence
from lumyn.modules.synapse.interpreteur_rendez_vous import interpreter_rendez_vous
from lumyn.modules.synapse.orchestrateur_rendez_vous import preparer_rendez_vous_synapse


@dataclass(frozen=True)
class PropositionLieu:
    nom: str
    adresse: str
    source: str
    profession: str = ""
    ville: str = ""
    identifiant: str = ""
    conservation_autorisee: bool = False
    adresse_verifiee: bool = False


class FournisseurLieux(Protocol):
    def rechercher(self, texte: str) -> Sequence[PropositionLieu]:
        """Propose des adresses sourcées sans enregistrer de fiche personnelle."""
        ...


class FournisseurIAWeb(FournisseurLieux, Protocol):
    """Repli sourcé sur la requête minimale, sans accès au Carnet ni à Google."""


def proposition_valide(p):
    return (
        isinstance(p, PropositionLieu)
        and all(isinstance(v, str) and v.strip() for v in (p.nom, p.adresse, p.source))
        and all(isinstance(v, str) for v in (p.profession, p.ville, p.identifiant))
        and isinstance(p.conservation_autorisee, bool)
        and isinstance(p.adresse_verifiee, bool)
    )


def requete_minimale(texte):
    interpretation = interpreter_rendez_vous(texte)
    morceaux = []
    for cle in ('titre', 'profession', 'lieu_explicite'):
        valeur = interpretation.get(cle)
        if valeur and valeur.casefold() not in ' '.join(morceaux).casefold():
            morceaux.append(valeur)
    return ' '.join(morceaux)


def _obtenir_indices_locaux(texte, interpreteur_local):
    if interpreteur_local is None:
        return {}, None
    try:
        return interpreteur_local.interpreter(texte), None
    except (OSError, TimeoutError, ValueError) as erreur:
        return {}, type(erreur).__name__


def _enrichir_requete_locale(requete, indices):
    """Ajoute seulement des indices non sensibles à la requête externe."""
    morceaux = [requete]
    courant = requete.casefold()
    for cle in ("personne", "profession", "etablissement", "ville"):
        valeur = indices.get(cle)
        if valeur and valeur.casefold() not in courant:
            morceaux.append(valeur)
            courant += " " + valeur.casefold()
    return " ".join(morceaux)


MOTS_FAIBLES = {
    'adresse', 'cabinet', 'centre', 'rdv', 'rendez', 'vous', 'avec', 'chez',
    'son', 'de', 'du', 'des', 'la', 'le', 'les', 'a', 'au', 'aux', 'en',
}


def _mots(texte):
    texte = unicodedata.normalize('NFKD', str(texte or '').casefold())
    texte = ''.join(c for c in texte if not unicodedata.combining(c))
    return {m for m in re.findall(r"[a-z0-9]+", texte)
            if len(m) > 1 and m not in MOTS_FAIBLES}


def _pertinence(proposition, interpretation, indices):
    """Score explicable : identité, métier et ville, jamais code d'activité."""
    personne = indices.get('personne') or interpretation.get('professionnel')
    etablissement = indices.get('etablissement')
    profession = indices.get('profession') or interpretation.get('profession')
    ville = indices.get('ville') or interpretation.get('lieu_explicite')
    nom = _mots(proposition.nom)
    metier = _mots(proposition.profession)
    localisation = _mots(proposition.ville) | _mots(proposition.adresse)
    score = 0
    signaux = 0
    identite_ou_metier = False
    for valeur, cible, poids in (
        (personne, nom, 6), (etablissement, nom, 6),
        (profession, nom | metier, 4), (ville, localisation, 3),
    ):
        attendus = _mots(valeur)
        if attendus and attendus <= cible:
            score += poids
            signaux += 1
            if poids > 3:
                identite_ou_metier = True
    # Sans données locales, le titre analysé fournit encore des mots d'identité.
    identite_requete = _mots(interpretation.get('titre'))
    communs = identite_requete & (nom | metier)
    if communs:
        score += min(4, len(communs) * 2)
        signaux += 1
        identite_ou_metier = True
    return score, signaux, identite_ou_metier


def filtrer_propositions_pertinentes(propositions, texte, indices=None):
    """Retire les propositions sans rapport réel avant affichage ou fallback."""
    interpretation = interpreter_rendez_vous(texte)
    indices = indices or {}
    retenues = []
    for proposition in propositions:
        score, signaux, identite_ou_metier = _pertinence(
            proposition, interpretation, indices)
        if signaux and identite_ou_metier and score >= 3:
            retenues.append(proposition)
    return retenues


def proposer_recherche_externe(texte, fournisseur=None, *, autoriser=False, lieux=None,
                               fournisseur_ia=None, autoriser_ia=False,
                               interpreteur_local=None):
    """Carnet d'abord, puis structuré, puis IA autorisée si aucun résultat valable.

    Fournisseurs concrets non configurés par défaut. Leur adaptateur doit borner
    les délais réseau. Une erreur n'écrit rien et laisse la saisie locale disponible.
    """
    indices_locaux, probleme_local = _obtenir_indices_locaux(
        texte, interpreteur_local) if autoriser else ({}, None)
    resultat = preparer_rendez_vous_synapse(
        texte, lieux, indices_locaux=indices_locaux)
    rdv = resultat.get('rendez_vous') or {}
    if (not autoriser or fournisseur is None
        or rdv.get('lieu_source') in ('carnet', 'maison')
        or rdv.get('mode') in ('visio', 'domicile', 'telephone')
        or resultat['etat'] not in ('confirmation', 'incomplet')
        or any(not rdv.get(c) for c in ('titre','date','heure'))):
        return resultat
    requete = requete_minimale(texte)
    if not requete:
        return resultat
    requete = _enrichir_requete_locale(requete, indices_locaux)
    fournisseurs = [('structure', fournisseur)]
    if autoriser_ia and fournisseur_ia is not None:
        fournisseurs.append(('ia_web', fournisseur_ia))
    problemes = [probleme_local] if probleme_local else []
    propositions = []
    for origine, moteur in fournisseurs:
        try:
            propositions = list(moteur.rechercher(requete))
            if not all(proposition_valide(p) for p in propositions):
                raise ValueError('Propositions invalides ou non sourcées')
            propositions = filtrer_propositions_pertinentes(
                propositions, texte, indices_locaux)
        except (OSError, ValueError) as erreur:
            problemes.append(type(erreur).__name__)
            propositions = []
        if propositions:
            resultat['fournisseur_utilise'] = origine
            break
    resultat['propositions_externes'] = list(dict.fromkeys(propositions))
    resultat['requete_externe'] = requete
    resultat['problemes_recherche'] = problemes
    if propositions:
        resultat['etat'] = 'ambigu'
        resultat['message'] = 'Choisis et vérifie une adresse proposée avant de confirmer.'
    else:
        resultat['etat'] = 'incomplet'
        resultat['message'] = ('Recherche indisponible ou sans résultat fiable. '
                               'Tu peux préciser le lieu manuellement et analyser à nouveau.')
    return resultat
