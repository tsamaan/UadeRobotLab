#!/usr/bin/env bash
# Ejecuta tu programa contra el simulador que ya tenes abierto.
cd "$(dirname "$0")" || exit 1

ARCHIVO="${1:-mi_desarrollo/mi_tp02.py}"
if [ ! -f "$ARCHIVO" ]; then
  echo "No encuentro $ARCHIVO"; read -r -p "Enter para cerrar..."; exit 1
fi

# Tu programa solo necesita Python: habla con el simulador por socket, asi
# que aca no hace falta que tenga MuJoCo.
CANDIDATOS="python3 python3.13 python3.12 python3.11 python3.10 python"
[ -x "$HOME/.venvs/unitree/bin/python" ] && CANDIDATOS="$HOME/.venvs/unitree/bin/python $CANDIDATOS"
PYTHON=""
for PY in $CANDIDATOS; do
  command -v "$PY" >/dev/null 2>&1 || [ -x "$PY" ] || continue
  PYTHON="$PY"; break
done

if [ -z "$PYTHON" ]; then
  echo "   No encuentro Python. Instalalo y volve a intentar."
  read -r -p "   Enter para cerrar..."; exit 1
fi

"$PYTHON" "$ARCHIVO"
echo
read -r -p "Enter para cerrar..."
