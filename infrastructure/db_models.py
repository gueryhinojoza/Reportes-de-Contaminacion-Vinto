"""Modelos de tabla SQLModel (detalle de persistencia, separados de las entidades del dominio)."""
from typing import Optional

from pydantic import NaiveDatetime
from sqlmodel import Field, SQLModel


class UsuarioDB(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    rol: str
    activo: bool = True


class CuadrillaDB(SQLModel, table=True):
    __tablename__ = "cuadrillas"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    responsable: str
    activa: bool = True


class IncidenteDB(SQLModel, table=True):
    __tablename__ = "incidentes"
    id: Optional[int] = Field(default=None, primary_key=True)
    categoria: str = Field(index=True)
    descripcion: str
    latitud: float
    longitud: float
    referencia: str = ""
    fecha_hora: NaiveDatetime = Field(index=True)
    fecha_registro: NaiveDatetime
    zona: str = Field(index=True)
    imagen: Optional[str] = None
    estado: str = Field(index=True)
    reportado_por: int = Field(index=True)
    cuadrilla_id: Optional[int] = None
    responsable: Optional[str] = None


class CambioEstadoDB(SQLModel, table=True):
    __tablename__ = "historial_estados"
    id: Optional[int] = Field(default=None, primary_key=True)
    incidente_id: int = Field(index=True)
    estado_anterior: Optional[str] = None
    estado_nuevo: str
    fecha: NaiveDatetime
    usuario_id: Optional[int] = None
    usuario_nombre: str = ""
    comentario: str = ""
