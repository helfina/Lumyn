"""Configuration locale de développement, sans dépendance externe."""

import os
import re
from pathlib import Path


NOM_ENV_LOCAL = ".env.local"
CLE_ENV = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def trouver_racine_projet(depart=None):
    """Trouve un dépôt Lumyn parent ; retourne None hors du dépôt."""
    courant = Path(depart or Path.cwd()).resolve()
    if courant.is_file():
        courant = courant.parent
    for dossier in (courant, *courant.parents):
        if ((dossier / "pyproject.toml").is_file()
                and (dossier / "src" / "lumyn").is_dir()):
            return dossier
    return None


def charger_env_local(*, racine=None, environ=None):
    """Charge les paires simples de .env.local sans écraser le processus.

    Les lignes mal formées sont ignorées silencieusement : leur contenu, qui
    peut être secret, ne doit jamais apparaître dans un message ou un journal.
    """
    environ = os.environ if environ is None else environ
    racine = Path(racine) if racine is not None else trouver_racine_projet()
    if racine is None:
        return 0
    chemin = racine / NOM_ENV_LOCAL
    try:
        lignes = chemin.read_text(encoding="utf-8-sig").splitlines()
    except (FileNotFoundError, OSError, UnicodeError):
        return 0
    chargees = 0
    for ligne in lignes:
        nettoyee = ligne.strip()
        if not nettoyee or nettoyee.startswith("#") or "=" not in nettoyee:
            continue
        cle, valeur = nettoyee.split("=", 1)
        cle = cle.strip()
        if not CLE_ENV.fullmatch(cle) or cle in environ:
            continue
        environ[cle] = valeur.strip()
        chargees += 1
    return chargees
