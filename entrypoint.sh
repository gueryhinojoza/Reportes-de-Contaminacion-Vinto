#!/bin/sh
# Arranque del contenedor: siembra la base solo si todavía no existe y luego
# inicia la aplicación.
set -eu

# Rutas configurables por variables de entorno (valores por defecto de Docker).
export VINTO_DB_URL="${VINTO_DB_URL:-sqlite:////app/data/vinto.db}"
export VINTO_UPLOADS="${VINTO_UPLOADS:-/app/uploads}"
export STORAGE_SECRET="${STORAGE_SECRET:-cambiar}"

# Obtener la ruta del archivo SQLite a partir de la URL.
case "$VINTO_DB_URL" in
    sqlite:///*) DB_PATH="${VINTO_DB_URL#sqlite:///}" ;;
    *)           DB_PATH="" ;;
esac

mkdir -p "$VINTO_UPLOADS"
if [ -n "$DB_PATH" ]; then
    mkdir -p "$(dirname "$DB_PATH")"
fi

if [ -n "$DB_PATH" ] && [ -f "$DB_PATH" ]; then
    echo "[entrypoint] Base de datos encontrada en $DB_PATH; no se siembra de nuevo."
else
    echo "[entrypoint] No existe la base de datos; ejecutando seed_data.py..."
    python seed_data.py
fi

exec python main.py
