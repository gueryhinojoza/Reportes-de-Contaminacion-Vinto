"""Patrón Factory: IncidenteFactory crea incidentes con validaciones propias por categoría."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Callable, Optional

from .entities import Incidente
from .errors import ValidacionError
from .value_objects import Categoria, Coordenada
from .zonas import zona_mas_cercana

MAX_DESCRIPCION = 1000


class ReglaCategoria(ABC):
    """Validaciones específicas de un tipo de incidente."""

    categoria: Categoria

    @abstractmethod
    def validar(self, descripcion: str, referencia: str) -> None: ...

    @staticmethod
    def _minimo(descripcion: str, minimo: int, nombre: str) -> None:
        if len(descripcion) < minimo:
            raise ValidacionError(f"Para «{nombre}» la descripción debe tener al menos {minimo} caracteres.")


class ReglaBasura(ReglaCategoria):
    categoria = Categoria.BASURA

    def validar(self, descripcion: str, referencia: str) -> None:
        self._minimo(descripcion, 10, "Basura")


class ReglaVertidoIlegal(ReglaCategoria):
    categoria = Categoria.VERTIDO_ILEGAL

    def validar(self, descripcion: str, referencia: str) -> None:
        self._minimo(descripcion, 15, "Vertido Ilegal")
        if not referencia:
            raise ValidacionError("Un vertido ilegal requiere una referencia del lugar u origen del vertido.")


class ReglaQuema(ReglaCategoria):
    categoria = Categoria.QUEMA

    def validar(self, descripcion: str, referencia: str) -> None:
        self._minimo(descripcion, 10, "Quema")


class ReglaContaminacionRios(ReglaCategoria):
    categoria = Categoria.CONTAMINACION_RIOS

    def validar(self, descripcion: str, referencia: str) -> None:
        self._minimo(descripcion, 15, "Contaminación de Ríos")
        if not referencia:
            raise ValidacionError("Indique el nombre del río o tramo afectado en la referencia.")


class ReglaOtro(ReglaCategoria):
    categoria = Categoria.OTRO

    def validar(self, descripcion: str, referencia: str) -> None:
        self._minimo(descripcion, 20, "Otro")


class IncidenteFactory:
    """Crea la entidad Incidente aplicando validaciones comunes y las propias de cada tipo."""

    def __init__(self, zona_de: Callable[[Coordenada], str] = zona_mas_cercana,
                 reglas: Optional[list[ReglaCategoria]] = None) -> None:
        self._zona_de = zona_de
        lista = reglas or [ReglaBasura(), ReglaVertidoIlegal(), ReglaQuema(),
                           ReglaContaminacionRios(), ReglaOtro()]
        self._reglas = {r.categoria: r for r in lista}

    def crear(self, *, categoria: object, descripcion: Optional[str], latitud: object, longitud: object,
              referencia: Optional[str], fecha_hora: Optional[datetime], reportado_por: int,
              ahora: datetime, imagen: Optional[str] = None) -> Incidente:
        cat = Categoria.desde_texto(categoria)
        descripcion = (descripcion or "").strip()
        referencia = (referencia or "").strip()
        if not descripcion:
            raise ValidacionError("La descripción es obligatoria.")
        if len(descripcion) > MAX_DESCRIPCION:
            raise ValidacionError(f"La descripción no puede superar {MAX_DESCRIPCION} caracteres.")
        if latitud in (None, "") or longitud in (None, ""):
            raise ValidacionError("Debe indicar la ubicación (latitud y longitud).")
        coordenada = Coordenada(latitud, longitud)
        if fecha_hora is None:
            raise ValidacionError("La fecha y hora son obligatorias.")
        if fecha_hora > ahora + timedelta(minutes=5):
            raise ValidacionError("La fecha y hora del incidente no pueden estar en el futuro.")
        self._reglas[cat].validar(descripcion, referencia)
        return Incidente(
            categoria=cat, descripcion=descripcion, coordenada=coordenada, referencia=referencia,
            fecha_hora=fecha_hora, zona=self._zona_de(coordenada), reportado_por=reportado_por,
            fecha_registro=ahora, imagen=imagen,
        )
