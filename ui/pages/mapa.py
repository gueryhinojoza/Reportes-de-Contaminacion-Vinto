"""Mapa público con todos los incidentes (RF-08)."""
from nicegui import ui

from composition_root import Contenedor
from domain.value_objects import EstadoIncidente
from ui.comun import seguro
from ui.estilos import COLOR_ESTADO
from ui.layout import marco
from ui.mapa_adapter import LeafletMapaAdapter, MarcadorIncidente
from ui.sesion import usuario_actual


def registrar(c: Contenedor) -> None:
    @ui.page("/")
    def mapa_publico() -> None:
        usuario = usuario_actual(c)
        with marco(c, usuario, "Mapa de incidentes", "Incidentes ambientales reportados en el Municipio de Vinto"):
            centro = c.geo.centro_inicial()
            mapa = LeafletMapaAdapter((centro.latitud, centro.longitud), zoom=13)
            with ui.card().classes("tarjeta w-full q-pa-sm"):
                mapa.dibujar("w-full h-[60vh]")
            with ui.row().classes("items-center gap-4"):
                for estado in EstadoIncidente:
                    with ui.row().classes("items-center gap-1"):
                        ui.element("span").style(
                            f"display:inline-block;width:14px;height:14px;border-radius:50%;background:{COLOR_ESTADO[estado]}")
                        ui.label(estado.etiqueta).classes("text-sm")

            async def cargar() -> None:
                incidentes = seguro(c.listar_publicos.ejecutar) or []
                marcadores = [
                    MarcadorIncidente(i.coordenada.latitud, i.coordenada.longitud, i.categoria.etiqueta,
                                      i.estado.etiqueta, COLOR_ESTADO[i.estado],
                                      f"/incidentes/{i.id}" if usuario else None, i.zona)
                    for i in incidentes
                ]
                await mapa.mostrar_incidentes(marcadores)

            ui.timer(0.2, cargar, once=True)
