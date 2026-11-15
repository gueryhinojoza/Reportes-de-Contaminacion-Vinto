"""Patrón Adapter: geolocalización (zonas de Vinto) detrás del puerto ServicioGeolocalizacion."""
from __future__ import annotations

from domain.ports import ServicioGeolocalizacion
from domain.value_objects import Coordenada
from domain.zonas import CENTRO_VINTO, nombres_de_zonas, zona_mas_cercana


class GeolocalizacionVinto(ServicioGeolocalizacion):
    def zona_de(self, coordenada: Coordenada) -> str:
        return zona_mas_cercana(coordenada)

    def centro_inicial(self) -> Coordenada:
        return CENTRO_VINTO

    def zonas(self) -> list[str]:
        return nombres_de_zonas()
