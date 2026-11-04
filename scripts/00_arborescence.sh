#!/bin/bash
# Affiche l'arborescence du projet (2 niveaux, sans fichiers cachés)
cd "$(dirname "$0")/.." && mkdir -p docs
find . -mindepth 1 -maxdepth 2 -not -path '*__pycache__*' -not -path '*/.*' -not -name 'Icon*' -not -path './_sync*' -not -path './docs/screenshots/*' | sort | sed 's|^\./||' | awk -F/ '{ indent=""; for(i=1;i<NF;i++) indent=indent"│   "; print indent "├── " $NF }'
