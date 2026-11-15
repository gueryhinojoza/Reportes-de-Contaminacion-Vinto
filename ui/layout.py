"""Layout común: cabecera responsive con navegación según el rol."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

from nicegui import ui

from composition_root import Contenedor
from domain.entities import Usuario
from domain.permisos import Permiso, tiene_permiso
from domain.value_objects import Rol

from .estilos import CSS, VERDE, VERDE_CLARO, VERDE_OSCURO
from .sesion import cerrar_sesion


def _enlaces(usuario: Optional[Usuario]) -> list[tuple[str, str, str]]:
    enlaces = [("Mapa", "map", "/")]
    if usuario:
        if tiene_permiso(usuario, Permiso.REGISTRAR_INCIDENTE):
            enlaces.append(("Nuevo incidente", "add_location_alt", "/incidentes/nuevo"))
        etiqueta = "Incidentes" if tiene_permiso(usuario, Permiso.VER_TODOS) else "Mis incidentes"
        enlaces.append((etiqueta, "list_alt", "/incidentes"))
        if tiene_permiso(usuario, Permiso.VER_DASHBOARD):
            enlaces.append(("Dashboard", "insights", "/dashboard"))
        if tiene_permiso(usuario, Permiso.GESTIONAR_USUARIOS):
            enlaces.append(("Usuarios", "group", "/admin/usuarios"))
        if tiene_permiso(usuario, Permiso.GESTIONAR_CUADRILLAS):
            enlaces.append(("Cuadrillas", "engineering", "/admin/cuadrillas"))
    return enlaces


@contextmanager
def marco(c: Contenedor, usuario: Optional[Usuario], titulo: str, subtitulo: str = ""):
    ui.colors(primary=VERDE_OSCURO, secondary=VERDE, accent=VERDE_CLARO)
    ui.add_head_html(CSS)
    enlaces = _enlaces(usuario)

    def salir() -> None:
        cerrar_sesion()
        ui.notify("Sesión cerrada.", type="info")
        ui.navigate.to("/login")

    with ui.header().classes("items-center justify-between bg-primary text-white q-px-md"):
        with ui.row().classes("items-center gap-2 cursor-pointer").on("click", lambda: ui.navigate.to("/")):
            ui.icon("eco", size="28px")
            ui.label("Vinto Ambiental").classes("text-lg font-bold")
        with ui.row().classes("items-center gap-1 gt-sm"):
            for etiqueta, icono, ruta in enlaces:
                ui.button(etiqueta, icon=icono, on_click=lambda r=ruta: ui.navigate.to(r)).props("flat color=white no-caps dense")
            if usuario:
                ui.label(f"{usuario.nombre} · {Rol(usuario.rol).etiqueta}").classes("text-sm q-mx-sm")
                ui.button(icon="logout", on_click=salir).props("flat round color=white dense").tooltip("Cerrar sesión")
            else:
                ui.button("Ingresar", icon="login", on_click=lambda: ui.navigate.to("/login")).props("flat color=white no-caps dense")
                ui.button("Registrarse", on_click=lambda: ui.navigate.to("/registro")).props("outline color=white no-caps dense")
        with ui.button(icon="menu").props("flat round color=white dense").classes("lt-md"):
            with ui.menu():
                for etiqueta, icono, ruta in enlaces:
                    with ui.menu_item(on_click=lambda r=ruta: ui.navigate.to(r)):
                        ui.icon(icono).classes("q-mr-sm")
                        ui.label(etiqueta)
                ui.separator()
                if usuario:
                    ui.menu_item(f"Salir ({usuario.nombre})", on_click=salir)
                else:
                    ui.menu_item("Ingresar", on_click=lambda: ui.navigate.to("/login"))
                    ui.menu_item("Registrarse", on_click=lambda: ui.navigate.to("/registro"))

    with ui.column().classes("w-full max-w-6xl mx-auto q-pa-md gap-4"):
        with ui.column().classes("gap-0"):
            ui.label(titulo).classes("text-2xl font-bold text-primary")
            if subtitulo:
                ui.label(subtitulo).classes("text-gray-600")
        yield
