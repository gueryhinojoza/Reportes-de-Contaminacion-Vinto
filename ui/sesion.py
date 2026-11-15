"""Sesión con app.storage.user y protección de páginas por permiso (RBAC)."""
from __future__ import annotations

from typing import Optional

from nicegui import app, ui

from composition_root import Contenedor
from domain.entities import Usuario
from domain.permisos import Permiso, tiene_permiso

_CLAVE = "usuario_id"


def usuario_actual(c: Contenedor) -> Optional[Usuario]:
    uid = app.storage.user.get(_CLAVE)
    if uid is None:
        return None
    usuario = c.usuarios.obtener(uid)
    if usuario is None or not usuario.activo:
        app.storage.user.pop(_CLAVE, None)
        return None
    return usuario


def iniciar_sesion(usuario: Usuario) -> None:
    app.storage.user[_CLAVE] = usuario.id


def cerrar_sesion() -> None:
    app.storage.user.pop(_CLAVE, None)


def exigir_pagina(c: Contenedor, permiso: Optional[Permiso] = None) -> Optional[Usuario]:
    """Devuelve el usuario si puede ver la página; si no, redirige y devuelve None."""
    usuario = usuario_actual(c)
    if usuario is None:
        ui.notify("Inicie sesión para continuar.", type="warning")
        ui.navigate.to("/login")
        return None
    if permiso is not None and not tiene_permiso(usuario, permiso):
        ui.notify("No tiene permisos para acceder a esa sección.", type="negative")
        ui.navigate.to("/")
        return None
    return usuario
