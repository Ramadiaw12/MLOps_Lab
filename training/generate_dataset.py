"""Génération du dataset synthétique « Student Success ».

Variables d'entrée :
  - note          : note sur 20
  - absences      : nombre d'absences (0 à 30)
  - participation : score de participation sur 10
Variable cible :
  - reussite      : 1 si l'étudiant réussit, 0 sinon

⚠️ Données 100 % synthétiques, à but pédagogique uniquement.
"""
import argparse
import os

import numpy as np
import pandas as pd

SEED = 42


def generate(n: int = 1000, seed: int = SEED, drift: float = 0.0) -> pd.DataFrame:
    """Crée n étudiants fictifs. `drift` décale légèrement la distribution
    (utilisé pour simuler la dérive des données lors du réentraînement v2)."""
    rng = np.random.default_rng(seed)
    note = np.clip(rng.normal(11.5 + drift, 3.2, n), 0, 20).round(1)
    absences = np.clip(rng.poisson(5 + 2 * drift, n), 0, 30)
    participation = np.clip(rng.normal(6 + drift, 2.0, n), 0, 10).round(1)

    # Score latent : la note pèse le plus, les absences pénalisent, la participation aide
    score = 0.55 * (note - 10) - 0.18 * (absences - 5) + 0.35 * (participation - 5)
    proba = 1 / (1 + np.exp(-score))                 # sigmoïde
    reussite = (rng.random(n) < proba).astype(int)   # tirage aléatoire → étiquette 0/1

    return pd.DataFrame({
        "note": note,
        "absences": absences,
        "participation": participation,
        "reussite": reussite,
    })


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=1000)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--drift", type=float, default=0.0)
    p.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "data", "students.csv"))
    a = p.parse_args()
    df = generate(a.n, a.seed, a.drift)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    df.to_csv(a.out, index=False)
    print(f"Dataset écrit : {a.out} ({len(df)} lignes)")
    print(df.head())
    print("Taux de réussite :", round(df.reussite.mean(), 3))
