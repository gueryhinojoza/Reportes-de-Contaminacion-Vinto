"""Consulta y filtrado de incidentes (RF-05)."""
from __future__ import annotations

from datetime import date
from typing import Optional

from nicegui import ui

from composition_root import Contenedor
from domain.ports import FiltroIncidentes
from domain.permisos import Permiso, tiene_permiso
from domain.value_objects import Categoria, EstadoIncidente
from ui.comun import fmt_fecha, seguro
from ui.estilos import COLOR_ESTADO
from ui.layout import marco
from ui.sesion import exigir_pagina


def _fecha(texto: Optional[str]) -> Optional[date]:
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def registrar(c: Contenedor) -> None:
    @ui.page("/incidentes")
    def lista() -> None:
        usuario = exigir_pagina(c, Permiso.VER_PROPIOS)
        if not usuario:
            return
        todos = tiene_permiso(usuario, Permiso.VER_TODOS)
        titulo = "Incidentes reportados" if todos else "Mis incidentes"
        with marco(c, usuario, titulo, "Filtre por categoría, estado, fechas o zona"):
            with ui.card().classes("tarjeta w-full q-pa-md"):
                with ui.row().classes("w-full items-end gap-3"):
                    cat = ui.select({"": "Todas", **{x.value: x.etiqueta for x in Categoria}}, value="",
                                    label="Categoría").props("outlined dense").classes("min-w-[160px]")
                    est = ui.select({"": "Todos", **{x.value: x.etiqueta for x in EstadoIncidente}}, value="",
                                    label="Estado").props("outlined dense").classes("min-w-[160px]")
                    zona = ui.select({"": "Todas", **{z: z for z in c.geo.zonas()}}, value="",
                                     label="Zona").props("outlined dense").classes("min-w-[180px]")
                    desde = ui.input("Desde").props("outlined dense type=date").classes("min-w-[150px]")
                    hasta = ui.input("Hasta").props("outlined dense type=date").classes("min-w-[150px]")
                    ui.button("Buscar", icon="search", on_click=lambda: refrescar())
                    ui.button("Limpiar", icon="clear", on_click=lambda: limpiar()).props("flat")

            columnas = [
                {"name": "id", "label": "#", "field": "id", "align": "left", "sortable": True},
                {"name": "fecha", "label": "Fecha", "field": "fecha", "align": "left"},
                {"name": "categoria", "label": "Categoría", "field": "categoria", "align": "left", "sortable": True},
                {"name": "estado", "label": "Estado", "field": "estado", "align": "left"},
                {"name": "zona", "label": "Zona", "field": "zona", "align": "left", "sortable": True},
                {"name": "referencia", "label": "Referencia", "field": "referencia", "align": "left"},
                {"name": "acciones", "label": "", "field": "id", "align": "right"},
            ]
            tabla = ui.table(columns=columnas, rows=[], row_key="id", pagination=10).classes("tarjeta w-full")
            tabla.add_slot("body-cell-estado", '''
                <q-td :props="props"><q-badge :style="'background:' + props.row.color" :label="props.value" /></q-td>''')
            tabla.add_slot("body-cell-acciones", '''
                <q-td :props="props"><q-btn flat dense no-caps color="primary" icon="visibility" label="Ver"
                    :href="'/incidentes/' + props.row.id" /></q-td>''')
            tabla.props("no-data-label='No se encontraron incidentes con esos filtros.'")
            contador = ui.label().classes("text-sm text-gray-600")

            def refrescar() -> None:
                filtro = FiltroIncidentes(
                    categoria=Categoria(cat.value) if cat.value else None,
                    estado=EstadoIncidente(est.value) if est.value else None,
                    zona=zona.value or None, desde=_fecha(desde.value), hasta=_fecha(hasta.value))
                if filtro.desde and filtro.hasta and filtro.desde > filtro.hasta:
                    ui.notify("La fecha «Desde» no puede ser posterior a «Hasta».", type="warning")
                    return
                incidentes = seguro(lambda: c.listar_incidentes.ejecutar(usuario, filtro))
                if incidentes is None:
                    return
                tabla.rows = [{
                    "id": i.id, "fecha": fmt_fecha(i.fecha_hora), "categoria": i.categoria.etiqueta,
                    "estado": i.estado.etiqueta, "color": COLOR_ESTADO[i.estado], "zona": i.zona,
                    "referencia": i.referencia or "—"} for i in incidentes]
                tabla.update()
                contador.set_text(f"{len(incidentes)} incidente(s) encontrado(s)")

            def limpiar() -> None:
                for campo, valor in ((cat, ""), (est, ""), (zona, ""), (desde, None), (hasta, None)):
                    campo.set_value(valor)
                refrescar()

            refrescar()
