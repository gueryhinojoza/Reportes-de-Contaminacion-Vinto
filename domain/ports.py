"""Puertos (interfaces) que el dominio/aplicación necesitan de la infraestructura."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional

from .entities import Cuadrilla, Incidente, Usuario
from .value_objects import Categoria, Coordenada, EstadoIncidente


@dataclass
class FiltroIncidentes:
    categoria: Optional[Categoria] = None
    estado: Optional[EstadoIncidente] = None
    desde: Optional[date] = None
    hasta: Optional[date] = None
    zona: Optional[str] = None
    reportado_por: Optional[int] = None


class IncidenteRepository(ABC):
    @abstractmethod
    def agregar(self, incidente: Incidente) -> Incidente: ...

    @abstractmethod
    def actualizar(self, incidente: Incidente) -> Incidente: ...

    @abstractmethod
    def obtener(self, incidente_id: int) -> Optional[Incidente]: ...

    @abstractmethod
    def listar(self, filtro: Optional[FiltroIncidentes] = None) -> list[Incidente]: ...


class UsuarioRepository(ABC):
    @abstractmethod
    def agregar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def actualizar(self, usuario: Usuario) -> Usuario: ...

    @abstractmethod
    def obtener(self, usuario_id: int) -> Optional[Usuario]: ...

    @abstractmethod
    def obtener_por_email(self, email: str) -> Optional[Usuario]: ...

    @abstractmethod
    def listar(self) -> list[Usuario]: ...


class CuadrillaRepository(ABC):
    @abstractmethod
    def agregar(self, cuadrilla: Cuadrilla) -> Cuadrilla: ...

    @abstractmethod
    def actualizar(self, cuadrilla: Cuadrilla) -> Cuadrilla: ...

    @abstractmethod
    def obtener(self, cuadrilla_id: int) -> Optional[Cuadrilla]: ...

    @abstractmethod
    def listar(self) -> list[Cuadrilla]: ...


class AlmacenImagenes(ABC):
    """Puerto para guardar evidencia fotográfica (Adapter en infraestructura)."""

    @abstractmethod
    def guardar(self, nombre_original: str, contenido: bytes) -> str:
        """Guarda la imagen y devuelve el nombre con el que quedó almacenada."""

    @abstractmethod
    def eliminar(self, nombre: str) -> None: ...

    @abstractmethod
    def url_publica(self, nombre: str) -> str: ...


class HasheadorPassword(ABC):
    @abstractmethod
    def hashear(self, password: str) -> str: ...

    @abstractmethod
    def verificar(self, password: str, hash_guardado: str) -> bool: ...


class ServicioGeolocalizacion(ABC):
    """Puerto de geolocalización: resuelve la zona de una coordenada y el centro del mapa."""

    @abstractmethod
    def zona_de(self, coordenada: Coordenada) -> str: ...

    @abstractmethod
    def centro_inicial(self) -> Coordenada: ...

    @abstractmethod
    def zonas(self) -> list[str]: ...
