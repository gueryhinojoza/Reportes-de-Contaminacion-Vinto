"""Objetos de valor del dominio: Coordenada, Categoria, EstadoIncidente y Rol."""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .errors import ValidacionError


class Rol(str, Enum):
    VECINO = "VECINO"
    FUNCIONARIO = "FUNCIONARIO"
    ADMIN = "ADMIN"

    @property
    def etiqueta(self) -> str:
        return {"VECINO": "Vecino", "FUNCIONARIO": "Funcionario", "ADMIN": "Administrador"}[self.value]


class Categoria(str, Enum):
    BASURA = "BASURA"
    VERTIDO_ILEGAL = "VERTIDO_ILEGAL"
    QUEMA = "QUEMA"
    CONTAMINACION_RIOS = "CONTAMINACION_RIOS"
    OTRO = "OTRO"

    @property
    def etiqueta(self) -> str:
        return {
            "BASURA": "Basura",
            "VERTIDO_ILEGAL": "Vertido Ilegal",
            "QUEMA": "Quema",
            "CONTAMINACION_RIOS": "Contaminación de Ríos",
            "OTRO": "Otro",
        }[self.value]

    @classmethod
    def desde_texto(cls, valor: object) -> "Categoria":
        if isinstance(valor, cls):
            return valor
        try:
            return cls(str(valor))
        except ValueError:
            raise ValidacionError("La categoría seleccionada no es válida.") from None


class EstadoIncidente(str, Enum):
    REPORTADO = "REPORTADO"
    EN_REVISION = "EN_REVISION"
    EN_ATENCION = "EN_ATENCION"
    ATENDIDO = "ATENDIDO"
    CERRADO = "CERRADO"

    @property
    def etiqueta(self) -> str:
        return {
            "REPORTADO": "Reportado",
            "EN_REVISION": "En revisión",
            "EN_ATENCION": "En atención",
            "ATENDIDO": "Atendido",
            "CERRADO": "Cerrado",
        }[self.value]

    @classmethod
    def desde_texto(cls, valor: object) -> "EstadoIncidente":
        if isinstance(valor, cls):
            return valor
        try:
            return cls(str(valor))
        except ValueError:
            raise ValidacionError("El estado indicado no es válido.") from None

    def siguiente(self) -> Optional["EstadoIncidente"]:
        orden = list(EstadoIncidente)
        indice = orden.index(self)
        return orden[indice + 1] if indice + 1 < len(orden) else None

    def puede_pasar_a(self, nuevo: "EstadoIncidente") -> bool:
        """Solo se permite avanzar un paso en el orden definido."""
        return self.siguiente() == nuevo


@dataclass(frozen=True)
class Coordenada:
    latitud: float
    longitud: float

    def __post_init__(self) -> None:
        try:
            lat = float(self.latitud)
            lon = float(self.longitud)
        except (TypeError, ValueError):
            raise ValidacionError("Latitud y longitud deben ser números.") from None
        if not (math.isfinite(lat) and math.isfinite(lon)):
            raise ValidacionError("Latitud y longitud deben ser números finitos.")
        if not -90.0 <= lat <= 90.0:
            raise ValidacionError("La latitud debe estar entre -90 y 90.")
        if not -180.0 <= lon <= 180.0:
            raise ValidacionError("La longitud debe estar entre -180 y 180.")
        object.__setattr__(self, "latitud", lat)
        object.__setattr__(self, "longitud", lon)
