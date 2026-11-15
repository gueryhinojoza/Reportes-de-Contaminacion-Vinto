"""Punto de entrada: solo arranca la aplicación."""
import logging
import os

from nicegui import app, ui

import nicegui_compat  # noqa: F401  # evita el error "Duplicate name ... EsmModule" (ver el módulo)
from composition_root import construir_contenedor
from ui.paginas import registrar_paginas

logging.basicConfig(level=logging.INFO)


def main() -> None:
    contenedor = construir_contenedor()
    app.add_static_files("/uploads", str(contenedor.directorio_uploads))
    registrar_paginas(contenedor)
    ui.run(
        host="0.0.0.0",
        port=8080,
        title="Vinto Ambiental",
        favicon="🌿",
        reload=False,
        show=False,
        storage_secret=os.getenv("STORAGE_SECRET", "cambiar"),
    )


if __name__ in {"__main__", "__mp_main__"}:
    try:
        main()
    except KeyboardInterrupt:
        # Ctrl+C / detener el servidor: salida limpia sin traceback.
        pass
