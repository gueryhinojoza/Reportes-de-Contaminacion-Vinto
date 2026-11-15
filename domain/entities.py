"""Entidades del dominio: Usuario, Cuadrilla, CambioEstado e Incidente."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from .errors import TransicionInvalidaError
from .value_objects import Categoria, Coordenada, EstadoIncidente, Rol


@dataclass
class Usuario:
    nombre: str
    email: str
    password_hash: str
    rol: Rol = Rol.VECINO
    activo: bool = True
    id: Optional[int] = None


@dataclass
class Cuadrilla:
    nombre: str
    responsable: str
    activa: bool = True
    id: Optional[int] = None


@dataclass
class CambioEstado:
    estado_anterior: Optional[EstadoIncidente]
    estado_nuevo: EstadoIncidente
    fecha: datetime
    usuario_id: Optional[int]
    usuario_nombre: str
    comentario: str = ""


@dataclass
class Incidente:
    categoria: Categoria
    descripcion: str
    coordenada: Coordenada
    referencia: str
    fecha_hora: datetime
    zona: str
    reportado_por: int
    fecha_registro: datetime
    imagen: Optional[str] = None
    estado: EstadoIncidente = EstadoIncidente.REPORTADO
    cuadrilla_id: Optional[int] = None
    responsable: Optional[str] = None
    historial: list[CambioEstado] = field(default_factory=list)
    id: Optional[int] = None

    def registrar_creacion(self, usuario_id: Optional[int], usuario_nombre: str, fecha: datetime) -> None:
        self.historial.append(
            CambioEstado(None, EstadoIncidente.REPORTADO, fecha, usuario_id, usuario_nombre, "Incidente reportado")
        )

    def avanzar_estado(self, nuevo: EstadoIncidente, usuario_id: Optional[int], usuario_nombre: str,
                       fecha: datetime, comentario: str = "") -> None:
        """Regla RF-06: solo se avanza al siguiente estado, sin saltos ni retrocesos."""
        if not self.estado.puede_pasar_a(nuevo):
            permitido = self.estado.siguiente()
            detalle = (f"El siguiente estado permitido es «{permitido.etiqueta}»."
                       if permitido else "El incidente ya está en el estado final.")
            raise TransicionInvalidaError(
                f"No se puede pasar de «{self.estado.etiqueta}» a «{nuevo.etiqueta}». {detalle}"
            )
        self.historial.append(CambioEstado(self.estado, nuevo, fecha, usuario_id, usuario_nombre, comentario))
        self.estado = nuevo

    def asignar(self, cuadrilla_id: Optional[int], responsable: Optional[str]) -> None:
        self.cuadrilla_id = cuadrilla_id
        self.responsable = responsable

    def _fecha_de(self, estado: EstadoIncidente) -> Optional[datetime]:
        for cambio in self.historial:
            if cambio.estado_nuevo == estado:
                return cambio.fecha
        return None

    def tiempo_de_respuesta(self) -> Optional[timedelta]:
        """Tiempo entre REPORTADO y EN_ATENCION (None si aún no está en atención)."""
        inicio = self._fecha_de(EstadoIncidente.REPORTADO) or self.fecha_registro
        atencion = self._fecha_de(EstadoIncidente.EN_ATENCION)
        if atencion is None:
            return None
        return max(atencion - inicio, timedelta(0))
