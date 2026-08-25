#!/usr/bin/env bash
# ============================================================
#   Desarrollo de Aplicaciones II
#   Levanta el simulador y el backend para tu app.
# ============================================================
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "   Desarrollo de Aplicaciones II"
echo "============================================================"
echo
echo "   Que robot queres usar?"
echo
echo "     1)  G1   - robot humanoide (camina en dos patas)"
echo "     2)  Go2  - robot perro     (camina en cuatro patas)"
echo
read -r -p "   Elegi 1 o 2 [1]: " OPCION
case "$OPCION" in
  2) ROBOT="go2" ;;
  *) ROBOT="g1"  ;;
esac
echo

CANDIDATOS="python3 python"
[ -x "$HOME/.venvs/unitree/bin/python" ] && CANDIDATOS="$HOME/.venvs/unitree/bin/python $CANDIDATOS"
PYTHON=""; PRIMERO=""
for PY in $CANDIDATOS; do
  command -v "$PY" >/dev/null 2>&1 || [ -x "$PY" ] || continue
  [ -z "$PRIMERO" ] && PRIMERO="$PY"
  if "$PY" -c "import mujoco" >/dev/null 2>&1; then PYTHON="$PY"; break; fi
done
[ -z "$PYTHON" ] && PYTHON="$PRIMERO"
if [ -z "$PYTHON" ]; then
  echo "   ERROR: no encuentro Python. Instalalo desde https://python.org"
  read -r -p "   Enter para cerrar..."; exit 1
fi

# 1. El simulador, en segundo plano.
echo "   Abriendo el simulador..."
( cd entorno && "$PYTHON" -m sim --robot "$ROBOT" --materia tp05 ) &
SIM_PID=$!
trap 'kill $SIM_PID 2>/dev/null' EXIT INT TERM
sleep 8

# 2. El backend, en primer plano: su salida es la que importa.
"$PYTHON" entorno/arrancar_api.py --robot "$ROBOT"

echo
read -r -p "El backend se cerro. Enter para salir..."
