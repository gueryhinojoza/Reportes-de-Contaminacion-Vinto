"""Registro de todas las páginas. El orden importa: /incidentes/nuevo antes de /incidentes/{id}."""
from composition_root import Contenedor

from .pages import admin, auth, dashboard, detalle, lista, mapa, nuevo_incidente


def registrar_paginas(c: Contenedor) -> None:
    auth.registrar(c)
    mapa.registrar(c)
    nuevo_incidente.registrar(c)
    lista.registrar(c)
    detalle.registrar(c)
    dashboard.registrar(c)
    admin.registrar(c)
