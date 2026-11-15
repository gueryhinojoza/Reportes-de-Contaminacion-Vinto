"""Adaptadores SQLModel/SQLite de los puertos de repositorio."""
from __future__ import annotations

from datetime import datetime, time
from typing import Optional

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, col, create_engine, select

from domain.entities import CambioEstado, Cuadrilla, Incidente, Usuario
from domain.ports import (CuadrillaRepository, FiltroIncidentes, IncidenteRepository, UsuarioRepository)
from domain.value_objects import Categoria, Coordenada, EstadoIncidente, Rol

from .db_models import CambioEstadoDB, CuadrillaDB, IncidenteDB, UsuarioDB


def crear_engine(url: str = "sqlite:///data/vinto.db") -> Engine:
    return create_engine(url, connect_args={"check_same_thread": False})


def crear_tablas(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def _sesion(engine: Engine) -> Session:
    return Session(engine, expire_on_commit=False)


# ----------------------------------------------------------------- Usuarios
def _usuario(row: UsuarioDB) -> Usuario:
    return Usuario(row.nombre, row.email, row.password_hash, Rol(row.rol), row.activo, row.id)


class SqlUsuarioRepository(UsuarioRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def agregar(self, usuario: Usuario) -> Usuario:
        row = UsuarioDB(nombre=usuario.nombre, email=usuario.email.lower(), password_hash=usuario.password_hash,
                        rol=usuario.rol.value, activo=usuario.activo)
        with _sesion(self._engine) as s:
            s.add(row)
            s.commit()
            s.refresh(row)
        usuario.id = row.id
        return usuario

    def actualizar(self, usuario: Usuario) -> Usuario:
        with _sesion(self._engine) as s:
            row = s.get(UsuarioDB, usuario.id)
            if row is None:
                return usuario
            row.nombre, row.email = usuario.nombre, usuario.email.lower()
            row.password_hash, row.rol, row.activo = usuario.password_hash, usuario.rol.value, usuario.activo
            s.add(row)
            s.commit()
        return usuario

    def obtener(self, usuario_id: int) -> Optional[Usuario]:
        with _sesion(self._engine) as s:
            row = s.get(UsuarioDB, usuario_id)
            return _usuario(row) if row else None

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        with _sesion(self._engine) as s:
            row = s.exec(select(UsuarioDB).where(UsuarioDB.email == email.lower())).first()
            return _usuario(row) if row else None

    def listar(self) -> list[Usuario]:
        with _sesion(self._engine) as s:
            return [_usuario(r) for r in s.exec(select(UsuarioDB).order_by(col(UsuarioDB.id))).all()]


# --------------------------------------------------------------- Cuadrillas
def _cuadrilla(row: CuadrillaDB) -> Cuadrilla:
    return Cuadrilla(row.nombre, row.responsable, row.activa, row.id)


class SqlCuadrillaRepository(CuadrillaRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def agregar(self, cuadrilla: Cuadrilla) -> Cuadrilla:
        row = CuadrillaDB(nombre=cuadrilla.nombre, responsable=cuadrilla.responsable, activa=cuadrilla.activa)
        with _sesion(self._engine) as s:
            s.add(row)
            s.commit()
            s.refresh(row)
        cuadrilla.id = row.id
        return cuadrilla

    def actualizar(self, cuadrilla: Cuadrilla) -> Cuadrilla:
        with _sesion(self._engine) as s:
            row = s.get(CuadrillaDB, cuadrilla.id)
            if row is None:
                return cuadrilla
            row.nombre, row.responsable, row.activa = cuadrilla.nombre, cuadrilla.responsable, cuadrilla.activa
            s.add(row)
            s.commit()
        return cuadrilla

    def obtener(self, cuadrilla_id: int) -> Optional[Cuadrilla]:
        with _sesion(self._engine) as s:
            row = s.get(CuadrillaDB, cuadrilla_id)
            return _cuadrilla(row) if row else None

    def listar(self) -> list[Cuadrilla]:
        with _sesion(self._engine) as s:
            return [_cuadrilla(r) for r in s.exec(select(CuadrillaDB).order_by(col(CuadrillaDB.id))).all()]


# --------------------------------------------------------------- Incidentes
def _cambio(row: CambioEstadoDB) -> CambioEstado:
    anterior = EstadoIncidente(row.estado_anterior) if row.estado_anterior else None
    return CambioEstado(anterior, EstadoIncidente(row.estado_nuevo), row.fecha, row.usuario_id,
                        row.usuario_nombre, row.comentario)


def _incidente(row: IncidenteDB, historial: list[CambioEstadoDB]) -> Incidente:
    return Incidente(
        categoria=Categoria(row.categoria), descripcion=row.descripcion,
        coordenada=Coordenada(row.latitud, row.longitud), referencia=row.referencia,
        fecha_hora=row.fecha_hora, zona=row.zona, reportado_por=row.reportado_por,
        fecha_registro=row.fecha_registro, imagen=row.imagen, estado=EstadoIncidente(row.estado),
        cuadrilla_id=row.cuadrilla_id, responsable=row.responsable,
        historial=[_cambio(h) for h in historial], id=row.id,
    )


class SqlIncidenteRepository(IncidenteRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    @staticmethod
    def _copiar(incidente: Incidente, row: IncidenteDB) -> None:
        row.categoria = incidente.categoria.value
        row.descripcion = incidente.descripcion
        row.latitud, row.longitud = incidente.coordenada.latitud, incidente.coordenada.longitud
        row.referencia = incidente.referencia
        row.fecha_hora, row.fecha_registro = incidente.fecha_hora, incidente.fecha_registro
        row.zona, row.imagen = incidente.zona, incidente.imagen
        row.estado = incidente.estado.value
        row.reportado_por = incidente.reportado_por
        row.cuadrilla_id, row.responsable = incidente.cuadrilla_id, incidente.responsable

    @staticmethod
    def _guardar_historial(s: Session, incidente: Incidente) -> None:
        for h in s.exec(select(CambioEstadoDB).where(CambioEstadoDB.incidente_id == incidente.id)).all():
            s.delete(h)
        s.flush()
        for c in incidente.historial:
            s.add(CambioEstadoDB(
                incidente_id=incidente.id, estado_anterior=c.estado_anterior.value if c.estado_anterior else None,
                estado_nuevo=c.estado_nuevo.value, fecha=c.fecha, usuario_id=c.usuario_id,
                usuario_nombre=c.usuario_nombre, comentario=c.comentario))

    def agregar(self, incidente: Incidente) -> Incidente:
        row = IncidenteDB(categoria="", descripcion="", latitud=0, longitud=0, fecha_hora=datetime.now(),
                          fecha_registro=datetime.now(), zona="", estado="", reportado_por=0)
        self._copiar(incidente, row)
        with _sesion(self._engine) as s:
            s.add(row)
            s.flush()
            incidente.id = row.id
            self._guardar_historial(s, incidente)
            s.commit()
        return incidente

    def actualizar(self, incidente: Incidente) -> Incidente:
        with _sesion(self._engine) as s:
            row = s.get(IncidenteDB, incidente.id)
            if row is None:
                return incidente
            self._copiar(incidente, row)
            s.add(row)
            self._guardar_historial(s, incidente)
            s.commit()
        return incidente

    def _con_historial(self, s: Session, rows: list[IncidenteDB]) -> list[Incidente]:
        ids = [r.id for r in rows]
        por_incidente: dict[int, list[CambioEstadoDB]] = {i: [] for i in ids}
        if ids:
            cambios = s.exec(select(CambioEstadoDB).where(col(CambioEstadoDB.incidente_id).in_(ids))
                             .order_by(col(CambioEstadoDB.fecha), col(CambioEstadoDB.id))).all()
            for c in cambios:
                por_incidente[c.incidente_id].append(c)
        return [_incidente(r, por_incidente[r.id]) for r in rows]

    def obtener(self, incidente_id: int) -> Optional[Incidente]:
        with _sesion(self._engine) as s:
            row = s.get(IncidenteDB, incidente_id)
            return self._con_historial(s, [row])[0] if row else None

    def listar(self, filtro: Optional[FiltroIncidentes] = None) -> list[Incidente]:
        filtro = filtro or FiltroIncidentes()
        consulta = select(IncidenteDB)
        if filtro.categoria:
            consulta = consulta.where(IncidenteDB.categoria == filtro.categoria.value)
        if filtro.estado:
            consulta = consulta.where(IncidenteDB.estado == filtro.estado.value)
        if filtro.zona:
            consulta = consulta.where(IncidenteDB.zona == filtro.zona)
        if filtro.reportado_por is not None:
            consulta = consulta.where(IncidenteDB.reportado_por == filtro.reportado_por)
        if filtro.desde:
            consulta = consulta.where(IncidenteDB.fecha_hora >= datetime.combine(filtro.desde, time.min))
        if filtro.hasta:
            consulta = consulta.where(IncidenteDB.fecha_hora <= datetime.combine(filtro.hasta, time.max))
        consulta = consulta.order_by(col(IncidenteDB.fecha_hora).desc(), col(IncidenteDB.id).desc())
        with _sesion(self._engine) as s:
            return self._con_historial(s, list(s.exec(consulta).all()))
