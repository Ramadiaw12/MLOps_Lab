
#!/bin/bash

# Diagnostic de l'environnement MLOps
# Compatible macOS et Linux
# Écrit le résultat dans docs/diagnostic.txt

cd "$(dirname "$0")/.." || exit 1
mkdir -p docs

OUT=docs/diagnostic.txt

{
echo "=== DIAGNOSTIC MLOps Lab — $(date) ==="

echo "--- Architecture ---"
uname -m

echo "--- Système d'exploitation ---"
if command -v sw_vers >/dev/null 2>&1; then
    sw_vers
elif [ -f /etc/os-release ]; then
    grep -E 'PRETTY_NAME|VERSION_ID' /etc/os-release
else
    uname -a
fi

echo "--- Docker ---"
docker --version 2>&1
docker compose version 2>&1

echo "--- Moteur Docker ---"
docker info --format 'Server: {{.ServerVersion}} | OS: {{.OperatingSystem}} | Arch: {{.Architecture}} | CPUs: {{.NCPU}}' 2>&1

echo "--- Python ---"
python3 --version 2>&1

echo "--- Outils ---"
for t in git curl python3 pip3 node; do
    printf "%-8s %s\n" "$t" "$(command -v "$t" || echo ABSENT)"
done

echo "--- Ports 5000 / 8501 ---"

if command -v lsof >/dev/null 2>&1; then
    for port in 5000 8501; do
        if lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null; then
            :
        else
            echo "$port libre"
        fi
    done
else
    echo "lsof absent : vérification des ports ignorée"
fi

echo "--- Navigateurs ---"

if command -v google-chrome >/dev/null 2>&1; then
    echo "Google Chrome : $(command -v google-chrome)"
fi

if command -v chromium >/dev/null 2>&1; then
    echo "Chromium : $(command -v chromium)"
fi

if command -v firefox >/dev/null 2>&1; then
    echo "Firefox : $(command -v firefox)"
fi

if command -v brave-browser >/dev/null 2>&1; then
    echo "Brave : $(command -v brave-browser)"
fi

if [ "$(uname -s)" = "Darwin" ]; then
    echo "Applications macOS :"
    ls /Applications 2>/dev/null | grep -Ei "chrome|safari|firefox" || true
fi

echo "--- Disque ---"
df -h / | tail -1

echo "--- Dossier projet ---"
pwd
ls

} 2>&1 | tee "$OUT"

