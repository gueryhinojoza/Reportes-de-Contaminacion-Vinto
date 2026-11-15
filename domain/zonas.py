"""Zonas referenciales del Municipio de Vinto (coordenadas aproximadas)."""
from __future__ import annotations

from dataclasses import dataclass

from .value_objects import Coordenada

CENTRO_VINTO = Coordenada(-17.40, -66.31)
ZONA_DESCONOCIDA = "Otra zona"
DISTANCIA_MAXIMA_GRADOS = 0.08


@dataclass(frozen=True)
class Zona:
    nombre: str
    centro: Coordenada


ZONAS_VINTO: tuple[Zona, ...] = (
    Zona("Vinto Centro", Coordenada(-17.3925, -66.3130)),
    Zona("Chilimarca", Coordenada(-17.3700, -66.3300)),
    Zona("Linde", Coordenada(-17.4150, -66.3450)),
    Zona("Pairumani", Coordenada(-17.3900, -66.2850)),
    Zona("Ribera del Río Rocha", Coordenada(-17.4100, -66.3050)),
    Zona("Lacma", Coordenada(-17.4300, -66.3250)),
)


def nombres_de_zonas() -> list[str]:
    return [z.nombre for z in ZONAS_VINTO] + [ZONA_DESCONOCIDA]


def zona_mas_cercana(coordenada: Coordenada) -> str:
    """Devuelve el nombre de la zona cuyo centro está más cerca de la coordenada."""
    mejor, mejor_dist = ZONA_DESCONOCIDA, float("inf")
    for zona in ZONAS_VINTO:
        d = ((zona.centro.latitud - coordenada.latitud) ** 2
             + (zona.centro.longitud - coordenada.longitud) ** 2) ** 0.5
        if d < mejor_dist:
            mejor, mejor_dist = zona.nombre, d
    return mejor if mejor_dist <= DISTANCIA_MAXIMA_GRADOS else ZONA_DESCONOCIDA
