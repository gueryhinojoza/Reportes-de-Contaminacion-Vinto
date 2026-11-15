"""Parche de compatibilidad para NiceGUI 4.x.

NiceGUI registra los módulos ESM (las carpetas ``dist`` de cada elemento, por
ejemplo el de ECharts) dos veces: una al importar ``nicegui.ui`` y otra la
primera vez que se importa la clase del elemento (``EChart``). Ese registro se
identifica por la ruta más la fecha de modificación del directorio ``dist``, de
modo que si la fecha cambia entre ambos registros -- algo habitual en carpetas
sincronizadas como OneDrive o cuando el antivirus toca los archivos -- NiceGUI
falla con::

    AssertionError: Duplicate name "nicegui-echart" for EsmModule .../echart/dist

Este parche vuelve el registro idempotente por nombre: si el módulo ESM ya está
registrado, se ignora el segundo registro en lugar de lanzar la excepción.

Se puede quitar (junto con su import en ``main.py``) cuando una versión futura
de NiceGUI corrija este comportamiento.
"""
from __future__ import annotations

import logging
from pathlib import Path

from nicegui import dependencies, element

_log = logging.getLogger(__name__)

_registrar_esm_original = dependencies.register_esm


def _registrar_esm_una_vez(name: str, path: Path, *, max_time: float | None) -> None:
    for modulo in dependencies.esm_modules.values():
        if modulo.name == name:
            if modulo.path.resolve() != path.resolve():
                _log.warning(
                    "El módulo ESM %r ya estaba registrado desde %s; se ignora %s",
                    name, modulo.path, path,
                )
            return
    _registrar_esm_original(name, path, max_time=max_time)


# ``element.py`` importa la función directamente, así que hay que sustituirla
# tanto en ``dependencies`` como en el módulo ``element``.
dependencies.register_esm = _registrar_esm_una_vez
element.register_esm = _registrar_esm_una_vez
