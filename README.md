# MLOps Lab — Student Success (pack étudiant)

HESTIM Engineering & Business School · Module MLOps · Prof. Azeddine KHIAT · 2026/2027

Ce dossier contient tout le code du laboratoire. Suivez le compte rendu-tutoriel Word
« Compte rendu — MLOps Lab Student Success » étape par étape.

> Données 100 % synthétiques — modèle de démonstration pédagogique.

## État de départ
- `artifacts/` contient **uniquement la version 1** (régression logistique) : `model_v1.joblib`, `metrics_v1.json`, `metadata_v1.json`
  et leurs copies actives `model.joblib`, `metrics.json`, `metadata.json`.
- La version 2 sera produite par vous à l'étape 17 (`bash scripts/04_train_v2.sh`).

## Démarrage rapide (Mac ou PC avec Docker Desktop)
```bash
cd ~/Documents/MLOPS-LAB-STUDENT-SUCCESS
bash scripts/01_diagnostic.sh     # vérifier Docker et les ports
bash scripts/02_up.sh             # construire et démarrer api + frontend
bash scripts/03_check.sh          # vérifier avec curl
open http://127.0.0.1:8501        # le site (Windows : ouvrir l'adresse dans le navigateur)
```
API directe : http://127.0.0.1:5001 (le port 5000 est occupé par AirPlay sur macOS).

## Scripts
| Script | Rôle |
|---|---|
| 00_arborescence.sh | affiche l'arborescence du projet |
| 01_diagnostic.sh | diagnostic du poste → docs/diagnostic.txt |
| 01b_train_v1.sh | (ré)entraîne la v1 dans un conteneur Python (résultats identiques à Colab) |
| 02_up.sh | `docker compose up -d --build` |
| 03_check.sh | vérifications curl → docs/check.txt |
| 04_train_v2.sh | entraîne la v2 dans un conteneur Python |
| 05_redeploy.sh | reconstruit et redéploie l'API |
| 06_tests.sh / 06b_tests_integration.sh | tests pytest (en conteneur) |
| 07_down.sh | arrêt |
| 08_restart_test.sh | test arrêt / redémarrage |
| 09_rollback.sh | `bash scripts/09_rollback.sh 1` → v1 ; sans argument → version active |

Sous Windows, exécutez les scripts dans **Git Bash** ou **WSL** (ou tapez les commandes équivalentes indiquées dans le tutoriel).
# MLOps_Lab
