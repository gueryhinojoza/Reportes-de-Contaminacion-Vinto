"""Detalle de incidente, cambio de estado (RF-06) y asignación (RF-07)."""
from __future__ import annotations

from nicegui import ui

from composition_root import Contenedor
from domain.errors import ErrorDeDominio
from domain.permisos import Permiso, tiene_permiso
from ui.comun import fmt_fecha, seguro
from ui.estilos import COLOR_ESTADO
from ui.layout import marco
from ui.mapa_adapter import LeafletMapaAdapter, MarcadorIncidente
from ui.sesion import exigir_pagina


def _campo(etiqueta: str, valor: str) -> None:
    with ui.row().classes("gap-2 no-wrap"):
        ui.label(f"{etiqueta}:").classes("font-bold min-w-[130px]")
        ui.label(valor or "—")


def registrar(c: Contenedor) -> None:
    @ui.page("/incidentes/{incidente_id}")
    def detalle(incidente_id: int) -> None:
        usuario = exigir_pagina(c, Permiso.VER_PROPIOS)
        if not usuario:
            return
        try:
            inc = c.obtener_incidente.ejecutar(usuario, incidente_id)
        except ErrorDeDominio as exc:
            ui.notify(str(exc), type="negative")
            ui.navigate.to("/incidentes")
            return
        except Exception:  # noqa: BLE001
            ui.notify("No se pudo cargar el incidente.", type="negative")
            ui.navigate.to("/incidentes")
            return

        reportante = c.usuarios.obtener(inc.reportado_por)
        cuadrilla = c.cuadrillas.obtener(inc.cuadrilla_id) if inc.cuadrilla_id else None
        asignado = " / ".join(x for x in (cuadrilla.nombre if cuadrilla else "", inc.responsable or "") if x)

        with marco(c, usuario, f"Incidente #{inc.id} · {inc.categoria.etiqueta}", f"Zona: {inc.zona}"):
            with ui.row().classes("w-full gap-4 items-start max-md:flex-wrap no-wrap"):
                with ui.card().classes("tarjeta q-pa-md gap-2 grow basis-1/2 w-full"):
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Estado:").classes("font-bold min-w-[130px]")
                        ui.badge(inc.estado.etiqueta).style(f"background:{COLOR_ESTADO[inc.estado]}")
                    _campo("Categoría", inc.categoria.etiqueta)
                    _campo("Fecha del hecho", fmt_fecha(inc.fecha_hora))
                    _campo("Registrado el", fmt_fecha(inc.fecha_registro))
                    _campo("Reportado por", reportante.nombre if reportante else "—")
                    _campo("Referencias", inc.referencia)
                    _campo("Coordenadas", f"{inc.coordenada.latitud:.6f}, {inc.coordenada.longitud:.6f}")
                    _campo("Responsable", asignado or "Sin asignar")
                    ui.separator()
                    ui.label("Descripción").classes("font-bold")
                    ui.label(inc.descripcion).classes("whitespace-pre-wrap")
                    if inc.imagen:
                        ui.label("Evidencia fotográfica").classes("font-bold q-mt-sm")
                        ui.image(c.almacen.url_publica(inc.imagen)).classes("w-full max-w-md rounded")
                with ui.card().classes("tarjeta q-pa-sm grow basis-1/2 w-full"):
                    mapa = LeafletMapaAdapter((inc.coordenada.latitud, inc.coordenada.longitud), zoom=16)
                    mapa.dibujar("w-full h-80")

                    async def pintar() -> None:
                        await mapa.mostrar_incidentes([MarcadorIncidente(
                            inc.coordenada.latitud, inc.coordenada.longitud, inc.categoria.etiqueta,
                            inc.estado.etiqueta, COLOR_ESTADO[inc.estado], None, inc.zona)])
                    ui.timer(0.2, pintar, once=True)

            if tiene_permiso(usuario, Permiso.CAMBIAR_ESTADO) or tiene_permiso(usuario, Permiso.ASIGNAR_RESPONSABLE):
                with ui.row().classes("w-full gap-4 items-start max-md:flex-wrap no-wrap"):
                    if tiene_permiso(usuario, Permiso.CAMBIAR_ESTADO):
                        with ui.card().classes("tarjeta q-pa-md gap-2 grow basis-1/2 w-full"):
                            ui.label("Cambiar estado").classes("font-bold")
                            siguiente = inc.estado.siguiente()
                            if siguiente is None:
                                ui.label("El incidente está cerrado: no admite más cambios.").classes("text-gray-600")
                            else:
                                comentario = ui.input("Comentario (opcional)").props("outlined dense").classes("w-full")

                                def avanzar() -> None:
                                    r = seguro(lambda: c.cambiar_estado.ejecutar(usuario, inc.id, siguiente, comentario.value),
                                               f"Estado actualizado a «{siguiente.etiqueta}».")
                                    if r:
                                        ui.navigate.reload()
                                ui.button(f"Avanzar a «{siguiente.etiqueta}»", icon="arrow_forward",
                                          on_click=avanzar)
                    if tiene_permiso(usuario, Permiso.ASIGNAR_RESPONSABLE):
                        with ui.card().classes("tarjeta q-pa-md gap-2 grow basis-1/2 w-full"):
                            ui.label("Asignar responsable").classes("font-bold")
                            activas = seguro(lambda: c.cuadrillas.listar(usuario, solo_activas=True)) or []
                            opciones = {0: "— Sin cuadrilla —", **{x.id: f"{x.nombre} ({x.responsable})" for x in activas}}
                            sel = ui.select(opciones, value=inc.cuadrilla_id or 0, label="Cuadrilla") \
                                .props("outlined dense").classes("w-full")
                            resp = ui.input("Responsable (opcional)", value=inc.responsable or "") \
                                .props("outlined dense").classes("w-full")

                            def asignar() -> None:
                                r = seguro(lambda: c.asignar_responsable.ejecutar(
                                    usuario, inc.id, sel.value or None, resp.value), "Responsable asignado.")
                                if r:
                                    ui.navigate.reload()
                            ui.button("Asignar", icon="assignment_ind", on_click=asignar)

            ui.label("Historial de estados").classes("text-lg font-bold text-primary")
            columnas = [
                {"name": "fecha", "label": "Fecha", "field": "fecha", "align": "left"},
                {"name": "de", "label": "De", "field": "de", "align": "left"},
                {"name": "a", "label": "A", "field": "a", "align": "left"},
                {"name": "usuario", "label": "Usuario", "field": "usuario", "align": "left"},
                {"name": "comentario", "label": "Comentario", "field": "comentario", "align": "left"},
            ]
            filas = [{"fecha": fmt_fecha(h.fecha), "de": h.estado_anterior.etiqueta if h.estado_anterior else "—",
                      "a": h.estado_nuevo.etiqueta, "usuario": h.usuario_nombre, "comentario": h.comentario or "—"}
                     for h in inc.historial]
            ui.table(columns=columnas, rows=filas).classes("tarjeta w-full")
            ui.button("Volver al listado", icon="arrow_back", on_click=lambda: ui.navigate.to("/incidentes")).props("flat")
