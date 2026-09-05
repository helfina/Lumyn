from copy import deepcopy
import json
import pytest
from lumyn.modules.lieux import stockage as s
from lumyn.modules.lieux.gestion import rechercher_lieux


def test_copies_profondes_et_alias_nettoyes():
    original={'nom':'Test','alias':[' Guégon ', 'guegon', 'TEST'], 'adresses':[{'adresse':'Rue A','favorite':True}]}
    copie=deepcopy(original)
    rdv=s.enregistrer_lieu(original)
    assert original==copie
    assert rdv['alias']==['Guégon','TEST']
    rdv['adresses'][0]['adresse']='Rue B'
    assert original==copie
    modifie=s.modifier_lieu(rdv['id'],rdv)
    modifie['alias'].append('Autre')
    assert rdv['alias']==['Guégon','TEST']

@pytest.mark.parametrize('fiche',[{}, {'nom':'  '}, {'nom':42}, {'nom':'X','alias':[4]}, {'nom':'X','adresses':[None]}, {'nom':'X','adresses':[{'adresse':'A','favorite':True},{'adresse':'B','favorite':True}]}])
def test_refus_fiche_invalide_sans_ecriture(fiche):
    with pytest.raises(ValueError):s.enregistrer_lieu(fiche)
    assert not s.FICHIER_LIEUX.exists()

@pytest.mark.parametrize('terme',['Maison','domicile','chez moi'])
def test_maison_unique_et_recherche_equivalente(terme):
    maison=s.enregistrer_lieu({'nom':'Maison'})
    assert rechercher_lieux(terme)==[maison]
    with pytest.raises(ValueError):s.enregistrer_lieu({'nom':terme})
    autre=s.enregistrer_lieu({'nom':'Autre'})
    with pytest.raises(ValueError):s.modifier_lieu(autre['id'],{'nom':terme})
    assert len(s.charger_lieux())==2

@pytest.mark.parametrize('contenu',['{cassé','{}','[null]','[{"nom":"X", "alias":42}]'])
def test_donnees_illisibles_jamais_ecrasees(contenu):
    s.FICHIER_LIEUX.write_text(contenu)
    with pytest.raises(ValueError):s.enregistrer_lieu({'nom':'Nouveau'})
    assert s.FICHIER_LIEUX.read_text()==contenu


def test_anciennes_donnees_completes_sans_perte():
    s.FICHIER_LIEUX.write_text(json.dumps([{'nom':'Ancien','champ_perso':{'x':1}}]))
    ancien=s.charger_lieux()[0]
    assert ancien['alias']==[] and ancien['adresses']==[]
    assert ancien['champ_perso']=={'x':1}
    assert s.charger_lieux()[0]['id']==ancien['id']


def test_panne_ecriture_preserve_carnet(monkeypatch):
    s.enregistrer_lieu({'nom':'Original'})
    avant=s.FICHIER_LIEUX.read_bytes()
    def erreur(*args):raise OSError('Disque plein')
    monkeypatch.setattr('os.replace',erreur)
    with pytest.raises(OSError):s.enregistrer_lieu({'nom':'Nouveau'})
    assert s.FICHIER_LIEUX.read_bytes()==avant
