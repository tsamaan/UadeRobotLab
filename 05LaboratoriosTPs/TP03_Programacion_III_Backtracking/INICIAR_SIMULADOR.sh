#!/usr/bin/env bash
# ============================================================
#   Programacion III - Backtracking - TP03BT
#   Levanta el simulador oficial de Unitree listo para el TP.
# ============================================================
cd "$(dirname "$0")" || exit 1

echo "============================================================"
echo "   Programacion III - Backtracking"
echo "   Simulador de robots Unitree"
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
echo "   Revisando que este todo instalado..."
echo "   (la primera vez puede tardar unos minutos)"
echo

# Buscamos un Python que ademas pueda abrir la ventana 3D. Una maquina puede
# tener varios Python y que solo uno tenga MuJoCo: si elegimos el primero que
# aparece, el simulador arranca sin ventana y parece roto.
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

cd entorno || exit 1
"$PYTHON" -m sim --robot "$ROBOT" --materia tp03

echo
read -r -p "El simulador se cerro. Enter para salir..."
