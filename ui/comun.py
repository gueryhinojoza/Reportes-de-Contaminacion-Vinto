"""Utilidades de UI: manejo de errores sin que la app se caiga y formato de datos."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable, Optional, TypeVar

from nicegui import ui

from domain.errors import ErrorDeDominio, PermisoDenegadoError, ValidacionError

T = TypeVar("T")
log = logging.getLogger("vinto")


def seguro(accion: Callable[[], T], exito: Optional[str] = None) -> Optional[T]:
    """Ejecuta una acción mostrando errores con ui.notify. Devuelve None si falló."""
    try:
        resultado = accion()
    except (ValidacionError, PermisoDenegadoError) as exc:
        ui.notify(str(exc), type="warning", close_button=True)
        return None
    except ErrorDeDominio as exc:
        ui.notify(str(exc), type="negative", close_button=True)
        return None
    except Exception:  # noqa: BLE001 - la app nunca debe caerse por un error inesperado
        log.exception("Error inesperado")
        ui.notify("Ocurrió un error inesperado. Intente nuevamente.", type="negative", close_button=True)
        return None
    if exito:
        ui.notify(exito, type="positive")
    return resultado


def fmt_fecha(fecha: Optional[datetime]) -> str:
    return fecha.strftime("%d/%m/%Y %H:%M") if fecha else "—"
