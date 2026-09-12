import subprocess

from lumyn.configuration import charger_env_local, trouver_racine_projet
from lumyn import app


def test_env_local_absent_est_normal(tmp_path):
    environnement = {}
    assert charger_env_local(racine=tmp_path, environ=environnement) == 0
    assert environnement == {}


def test_env_local_charge_lignes_simples_commentaires_et_vides(tmp_path):
    (tmp_path / '.env.local').write_text(
        '# configuration locale\n\nLUMYN_IA_LOCALE=ollama\n'
        'LUMYN_OLLAMA_MODEL=llama3.2:1b\nOLLAMA_API_KEY=\n',
        encoding='utf-8')
    environnement = {}
    assert charger_env_local(racine=tmp_path, environ=environnement) == 3
    assert environnement == {
        'LUMYN_IA_LOCALE': 'ollama',
        'LUMYN_OLLAMA_MODEL': 'llama3.2:1b',
        'OLLAMA_API_KEY': '',
    }


def test_environnement_processus_prioritaire(tmp_path):
    (tmp_path / '.env.local').write_text(
        'LUMYN_OLLAMA_MODEL=modele-fichier\n', encoding='utf-8')
    environnement = {'LUMYN_OLLAMA_MODEL': 'modele-processus'}
    assert charger_env_local(racine=tmp_path, environ=environnement) == 0
    assert environnement['LUMYN_OLLAMA_MODEL'] == 'modele-processus'


def test_fichier_malforme_est_ignore_sans_exposer_secret(tmp_path, capsys, caplog):
    secret = 'secret-ne-doit-jamais-apparaitre'
    (tmp_path / '.env.local').write_text(
        f'ligne sans egal\nCLE INVALIDE={secret}\n=autre-secret\n',
        encoding='utf-8')
    environnement = {}
    assert charger_env_local(racine=tmp_path, environ=environnement) == 0
    sortie = capsys.readouterr()
    assert secret not in sortie.out + sortie.err
    assert secret not in caplog.text
    assert environnement == {}


def test_racine_projet_et_env_local_ignore_par_git():
    racine = trouver_racine_projet()
    assert racine is not None
    resultat = subprocess.run(
        ['git', 'check-ignore', '.env.local'], cwd=racine,
        capture_output=True, text=True, check=False)
    assert resultat.returncode == 0
    suivi = subprocess.run(
        ['git', 'ls-files', '--error-unmatch', '.env.local'], cwd=racine,
        capture_output=True, text=True, check=False)
    assert suivi.returncode != 0


def test_env_local_est_charge_avant_les_fournisseurs(monkeypatch):
    appels = []
    routeur = type('Routeur', (), {'adresses': object()})()
    monkeypatch.setattr(app, 'charger_env_local',
                        lambda: appels.append('env'))
    monkeypatch.setattr(app, 'RouteurLieuxPublics',
                        lambda: appels.append('public') or routeur)
    monkeypatch.setattr(app, 'interpreteur_local_depuis_environnement',
                        lambda: appels.append('local') or 'local')
    monkeypatch.setattr(app, 'fournisseur_ollama_web_depuis_environnement',
                        lambda **kwargs: appels.append('web') or 'web')
    assert app.creer_fournisseurs_synapse() == (routeur, 'local', 'web')
    assert appels == ['env', 'public', 'local', 'web']
