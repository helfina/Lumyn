"""Contrôles CI minimaux sur les fichiers de configuration suivis."""

import subprocess
from pathlib import Path


RACINE = Path(__file__).resolve().parents[1]
INTERDITS = {".env", ".env.local", "credentials.json", "token.json"}
EXEMPLE_ATTENDU = [
    "LUMYN_IA_LOCALE=ollama",
    "LUMYN_OLLAMA_MODEL=llama3.2:1b",
    "LUMYN_OLLAMA_WEB=0",
    "OLLAMA_API_KEY=",
]


def fichiers_suivis():
    resultat = subprocess.run(
        ["git", "ls-files", "-z"], cwd=RACINE, check=True,
        capture_output=True,
    )
    return [Path(p.decode("utf-8")) for p in resultat.stdout.split(b"\0") if p]


def verifier():
    suivis = fichiers_suivis()
    dangereux = sorted(str(p) for p in suivis if p.name in INTERDITS)
    if dangereux:
        raise SystemExit(
            "Fichiers locaux ou sensibles suivis par Git : " + ", ".join(dangereux)
        )
    exemple = RACINE / ".env.example"
    if Path(".env.example") not in suivis:
        raise SystemExit(".env.example doit être suivi par Git.")
    if exemple.read_text(encoding="utf-8").splitlines() != EXEMPLE_ATTENDU:
        raise SystemExit(".env.example contient une clé inattendue ou une valeur non sûre.")


if __name__ == "__main__":
    verifier()
