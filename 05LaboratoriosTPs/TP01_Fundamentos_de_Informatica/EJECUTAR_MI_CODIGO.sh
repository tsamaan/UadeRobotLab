#!/usr/bin/env bash
# Ejecuta tu programa contra el simulador que ya tenes abierto.
cd "$(dirname "$0")" || exit 1

ARCHIVO="${1:-mi_desarrollo/mi_tp01.py}"
if [ ! -f "$ARCHIVO" ]; then
  echo "No encuentro $ARCHIVO"; read -r -p "Enter para cerrar..."; exit 1
fi

CANDIDATOS="python3 python"
[ -x "$HOME/.venvs/unitree/bin/python" ] && CANDIDATOS="$HOME/.venvs/unitree/bin/python $CANDIDATOS"
for PY in $CANDIDATOS; do
  command -v "$PY" >/dev/null 2>&1 || [ -x "$PY" ] || continue
  PYTHON="$PY"; break
done

"$PYTHON" "$ARCHIVO"
echo
read -r -p "Enter para cerrar..."
