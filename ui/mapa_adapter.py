"""Patrón Adapter: el mapa (Leaflet de NiceGUI) queda detrás de la interfaz MapaPort."""
from __future__ import annotations

import html
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Optional

from nicegui import ui


@dataclass
class MarcadorIncidente:
    latitud: float
    longitud: float
    categoria: str
    estado: str
    color: str
    enlace_detalle: Optional[str] = None
    zona: str = ""


class MapaPort(ABC):
    @abstractmethod
    def dibujar(self, clases: str = "") -> None: ...

    @abstractmethod
    def al_hacer_clic(self, callback: Callable[[float, float], None]) -> None: ...

    @abstractmethod
    def fijar_punto(self, latitud: float, longitud: float, centrar: bool = False) -> None: ...

    @abstractmethod
    async def mostrar_incidentes(self, marcadores: list[MarcadorIncidente]) -> None: ...


class LeafletMapaAdapter(MapaPort):
    def __init__(self, centro: tuple[float, float], zoom: int = 13) -> None:
        self._centro, self._zoom = centro, zoom
        self._mapa: Optional[ui.leaflet] = None
        self._punto = None

    def dibujar(self, clases: str = "w-full h-96") -> None:
        self._mapa = ui.leaflet(center=self._centro, zoom=self._zoom).classes(clases)

    def al_hacer_clic(self, callback: Callable[[float, float], None]) -> None:
        def _manejar(e) -> None:
            ll = e.args["latlng"]
            callback(float(ll["lat"]), float(ll["lng"]))
        self._mapa.on("map-click", _manejar)

    def fijar_punto(self, latitud: float, longitud: float, centrar: bool = False) -> None:
        if self._punto is None:
            with self._mapa:
                self._punto = self._mapa.marker(latlng=(latitud, longitud))
        else:
            self._punto.move(latitud, longitud)
        if centrar:
            self._mapa.set_center((latitud, longitud))

    async def mostrar_incidentes(self, marcadores: list[MarcadorIncidente]) -> None:
        await self._mapa.initialized()
        with self._mapa:
            for m in marcadores:
                capa = self._mapa.generic_layer(name="circleMarker", args=[
                    (m.latitud, m.longitud),
                    {"radius": 10, "color": "#ffffff", "weight": 2, "fillColor": m.color, "fillOpacity": 0.9},
                ])
                enlace = (f'<a href="{html.escape(m.enlace_detalle)}">Ver detalle</a>'
                          if m.enlace_detalle else "<i>Inicie sesión para ver el detalle</i>")
                popup = (f"<b>{html.escape(m.categoria)}</b><br>Estado: {html.escape(m.estado)}<br>"
                         f"Zona: {html.escape(m.zona)}<br>{enlace}")
                capa.run_method("bindPopup", popup)
