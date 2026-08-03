#!/usr/bin/env bash
#
# deploy.sh — Despliegue seguro de CASA VERDE en cPanel
# -----------------------------------------------------
# Uso:
#   1) Entra a cPanel -> Terminal
#   2) cd ~/casa-verde
#   3) bash deploy.sh
#
# El script se detiene ante cualquier error (set -e) y verifica el
# SECRET_KEY ANTES de tocar nada, para que la app nunca quede caida.

set -euo pipefail

# --- Configuracion (ajusta solo si cambia tu hosting) -------------------
VENV_ACTIVATE="/home/marhalco/virtualenv/casa-verde/3.9/bin/activate"
PROJECT_DIR="/home/marhalco/casa-verde"
# ------------------------------------------------------------------------

echo "=================================================="
echo "  Despliegue CASA VERDE  ($(date '+%Y-%m-%d %H:%M:%S'))"
echo "=================================================="

# 1) Activar el entorno virtual si no esta ya activo -----------------------
if [ -z "${VIRTUAL_ENV:-}" ]; then
  if [ -f "$VENV_ACTIVATE" ]; then
    echo "-> Activando entorno virtual..."
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
  else
    echo "!! No encontre el entorno virtual en:"
    echo "   $VENV_ACTIVATE"
    echo "   Actívalo manualmente y vuelve a correr el script."
    exit 1
  fi
fi

cd "$PROJECT_DIR"

# 2) Verificar SECRET_KEY ANTES de actualizar ------------------------------
echo "-> Verificando SECRET_KEY en .env..."
if grep -q '^SECRET_KEY=.\+' .env; then
  echo "   OK — SECRET_KEY presente."
else
  echo "!! FALTA SECRET_KEY en .env — ABORTANDO."
  echo "   Sin esa clave la app no arranca (error 500)."
  exit 1
fi

# 3) Traer cambios ---------------------------------------------------------
echo "-> git pull..."
git pull

# 4) Migraciones y estaticos ----------------------------------------------
echo "-> Aplicando migraciones..."
python manage.py migrate --noinput

echo "-> Recopilando archivos estaticos..."
python manage.py collectstatic --noinput

# 5) Chequeo de seguridad: contraseña debil admin123 ----------------------
echo "-> Revisando superusuarios con contraseña débil 'admin123'..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
debiles = [u.username for u in get_user_model().objects.filter(is_superuser=True) if u.check_password('admin123')]
if debiles:
    print('   !! ALERTA — estos usuarios AUN usan admin123:', ', '.join(debiles))
    print('      Cambia la contraseña con: python manage.py changepassword <usuario>')
else:
    print('   OK — ningun superusuario usa admin123.')
"

# 6) Reiniciar la app (Passenger) -----------------------------------------
echo "-> Reiniciando la aplicacion..."
mkdir -p "$PROJECT_DIR/tmp"
touch "$PROJECT_DIR/tmp/restart.txt"
echo "   Se solicito reinicio (tmp/restart.txt)."
echo "   Si el sitio no refleja los cambios, usa el boton Restart en"
echo "   cPanel -> Setup Python App."

echo "=================================================="
echo "  Despliegue completado."
echo "  Ultimo commit desplegado:"
git log -1 --oneline | sed 's/^/    /'
echo "=================================================="
