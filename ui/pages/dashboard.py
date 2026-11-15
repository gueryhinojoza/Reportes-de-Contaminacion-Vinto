"""Dashboard para funcionarios (RF-09)."""
from nicegui import ui

from composition_root import Contenedor
from domain.permisos import Permiso
from domain.value_objects import Categoria, EstadoIncidente
from ui.comun import seguro
from ui.estilos import COLOR_ESTADO, VERDE
from ui.layout import marco
from ui.sesion import exigir_pagina


def _kpi(titulo: str, valor: str, icono: str) -> None:
    with ui.card().classes("tarjeta q-pa-md grow min-w-[180px]"):
        with ui.row().classes("items-center justify-between w-full no-wrap"):
            with ui.column().classes("gap-0"):
                ui.label(titulo).classes("text-sm text-gray-600")
                ui.label(valor).classes("kpi-valor")
            ui.icon(icono, size="36px", color="accent")


def registrar(c: Contenedor) -> None:
    @ui.page("/dashboard")
    def dashboard() -> None:
        usuario = exigir_pagina(c, Permiso.VER_DASHBOARD)
        if not usuario:
            return
        with marco(c, usuario, "Dashboard", "Indicadores de gestión de incidentes ambientales"):
            s = seguro(lambda: c.estadisticas.ejecutar(usuario))
            if s is None:
                ui.label("No se pudieron cargar las estadísticas.").classes("text-negative")
                return
            tiempo = f"{s.tiempo_medio_respuesta_horas:.1f} h" if s.tiempo_medio_respuesta_horas is not None else "Sin datos"
            with ui.row().classes("w-full gap-4"):
                _kpi("Total de incidentes", str(s.total), "report")
                _kpi("En atención", str(s.por_estado.get("EN_ATENCION", 0)), "engineering")
                _kpi("Sin asignar", str(s.sin_asignar), "person_off")
                _kpi("Tiempo medio de respuesta", tiempo, "timer")

            with ui.row().classes("w-full gap-4 max-md:flex-wrap no-wrap"):
                with ui.card().classes("tarjeta q-pa-md grow basis-1/2 w-full"):
                    ui.label("Incidentes por estado").classes("font-bold")
                    ui.echart({
                        "tooltip": {"trigger": "item"}, "legend": {"bottom": 0},
                        "series": [{"type": "pie", "radius": ["40%", "70%"], "data": [
                            {"name": e.etiqueta, "value": s.por_estado[e.value], "itemStyle": {"color": COLOR_ESTADO[e]}}
                            for e in EstadoIncidente]}]}).classes("w-full h-72")
                with ui.card().classes("tarjeta q-pa-md grow basis-1/2 w-full"):
                    ui.label("Incidentes por categoría").classes("font-bold")
                    ui.echart({
                        "tooltip": {}, "grid": {"containLabel": True},
                        "xAxis": {"type": "category", "data": [x.etiqueta for x in Categoria],
                                  "axisLabel": {"interval": 0, "rotate": 20}},
                        "yAxis": {"type": "value", "minInterval": 1},
                        "series": [{"type": "bar", "data": [s.por_categoria[x.value] for x in Categoria],
                                    "itemStyle": {"color": VERDE}}]}).classes("w-full h-72")

            with ui.card().classes("tarjeta q-pa-md w-full"):
                ui.label("Zonas críticas (más incidentes)").classes("font-bold")
                if s.zonas_criticas:
                    ui.echart({
                        "tooltip": {}, "grid": {"containLabel": True, "left": 10},
                        "xAxis": {"type": "value", "minInterval": 1},
                        "yAxis": {"type": "category", "inverse": True, "data": [z for z, _ in s.zonas_criticas]},
                        "series": [{"type": "bar", "data": [n for _, n in s.zonas_criticas],
                                    "itemStyle": {"color": "#c62828"}}]}).classes("w-full h-64")
                else:
                    ui.label("Aún no hay incidentes registrados.").classes("text-gray-600")
