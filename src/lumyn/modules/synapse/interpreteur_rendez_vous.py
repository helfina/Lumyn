"""Sépare les intentions explicites ; le parseur existant garde dates et heures."""
import re
from lumyn.modules.rendez_vous.analyseur import analyser_rendez_vous

PROFESSIONS = r"dentiste|psychiatre|médecin|medecin|infirmière|infirmiere|infirmier|orthophoniste|psychologue|kinésithérapeute|kinesitherapeute"
MODES = {
    'visio': r'\b(?:en\s+)?visio(?:conférence|conference)?\b',
    'telephone': r'\b(?:(?:par|au)\s+)?téléphone\b|\b(?:(?:par|au)\s+)?telephone\b',
    'physique': r'\b(?:en\s+présentiel|en\s+presentiel|sur\s+place|physique)\b',
}
DOMICILE = r'\b(?:(?:à|a)\s+)?(?:domicile|maison)\b|\bchez\s+moi\b'


def interpreter_rendez_vous(texte):
    """Retourne une interprétation prudente, sans adresse générée."""
    restant = texte.strip()
    modes = []
    for mode, motif in MODES.items():
        if re.search(motif, restant, re.IGNORECASE):
            modes.append(mode)
            restant = re.sub(motif, ' ', restant, flags=re.IGNORECASE)
    domicile = bool(re.search(DOMICILE, restant, re.IGNORECASE))
    if domicile:
        restant = re.sub(DOMICILE, ' ', restant, flags=re.IGNORECASE)
        if not modes:
            modes.append('domicile')
    restant = re.sub(r'\s*[—–]\s*(?=$)', ' ', restant).strip()
    rdv = analyser_rendez_vous(restant)
    ambiguities = []
    if len(modes) > 1:
        ambiguities.append('Plusieurs modes de rendez-vous sont indiqués. Précise lequel utiliser.')
    titre = (rdv.get('titre') or '').strip(' —–')
    lieu = rdv.get('lieu')
    profession = re.search(rf'\b({PROFESSIONS})\b', titre, re.IGNORECASE)
    professionnel = None
    # « Dr Laporte psychiatre Lorient » : métier séparateur, sans inventer de rue.
    if profession:
        avant = titre[:profession.start()].strip(' ,—–')
        apres = titre[profession.end():].strip(' ,—–')
        professionnel = avant or None
        if not lieu and apres:
            lieu = apres
            titre = avant or profession.group(0)
    rdv['titre'] = titre[:1].upper() + titre[1:] if titre else None
    rdv['lieu'] = lieu
    rdv['manquants'] = [label for cle, label in (
        ('titre', 'le titre'), ('date', 'la date'), ('heure', "l'heure")
    ) if not rdv.get(cle)]
    return {
        'intention': 'rendez_vous',
        'titre': rdv['titre'],
        'professionnel': professionnel,
        'profession': profession.group(0) if profession else None,
        'date': rdv['date'], 'heure': rdv['heure'],
        'mode': modes[0] if len(modes) == 1 else 'non_defini',
        'lieu_explicite': lieu,
        'lieu_a_resoudre': rdv['titre'],
        'manquants': list(rdv['manquants']),
        'ambiguities': ambiguities,
        'rendez_vous': rdv,
    }
