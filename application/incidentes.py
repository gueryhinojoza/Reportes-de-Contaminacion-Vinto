"""Casos de uso sobre incidentes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from domain.entities import Cuadrilla, Incidente, Usuario
from domain.errors import NoEncontradoError, PermisoDenegadoError, ValidacionError
from domain.factory import IncidenteFactory
from domain.permisos import Permiso, exigir, tiene_permiso
from domain.ports import (AlmacenImagenes, CuadrillaRepository, FiltroIncidentes, IncidenteRepository)
from domain.reglas_imagen import validar_imagen
from domain.value_objects import EstadoIncidente

Reloj = Callable[[], datetime]


@dataclass
class DatosIncidente:
    categoria: object
    descripcion: Optional[str]
    latitud: object
    longitud: object
    referencia: Optional[str] = ""
    fecha_hora: Optional[datetime] = None
    imagen_nombre: Optional[str] = None
    imagen_contenido: Optional[bytes] = None


class RegistrarIncidente:
    def __init__(self, incidentes: IncidenteRepository, almacen: AlmacenImagenes,
                 factory: IncidenteFactory, reloj: Reloj = datetime.now) -> None:
        self._incidentes = incidentes
        self._almacen = almacen
        self._factory = factory
        self._reloj = reloj

    def ejecutar(self, actor: Usuario, datos: DatosIncidente) -> Incidente:
        exigir(actor, Permiso.REGISTRAR_INCIDENTE)
        ahora = self._reloj()
        tiene_imagen = datos.imagen_contenido is not None or datos.imagen_nombre
        if tiene_imagen:
            validar_imagen(datos.imagen_nombre or "", datos.imagen_contenido or b"")
        incidente = self._factory.crear(
            categoria=datos.categoria, descripcion=datos.descripcion, latitud=datos.latitud,
            longitud=datos.longitud, referencia=datos.referencia, fecha_hora=datos.fecha_hora,
            reportado_por=actor.id, ahora=ahora,
        )
        nombre_imagen: Optional[str] = None
        if tiene_imagen:
            nombre_imagen = self._almacen.guardar(datos.imagen_nombre, datos.imagen_contenido)
            incidente.imagen = nombre_imagen
        incidente.registrar_creacion(actor.id, actor.nombre, ahora)
        try:
            return self._incidentes.agregar(incidente)
        except Exception:
            if nombre_imagen:
                self._almacen.eliminar(nombre_imagen)
            raise


class ListarIncidentes:
    """RF-05 + RF-10: el vecino solo ve los suyos; funcionario/admin ven todos."""

    def __init__(self, incidentes: IncidenteRepository) -> None:
        self._incidentes = incidentes

    def ejecutar(self, actor: Usuario, filtro: Optional[FiltroIncidentes] = None) -> list[Incidente]:
        filtro = filtro or FiltroIncidentes()
        if tiene_permiso(actor, Permiso.VER_TODOS):
            return self._incidentes.listar(filtro)
        exigir(actor, Permiso.VER_PROPIOS)
        filtro.reportado_por = actor.id
        return self._incidentes.listar(filtro)


class ListarIncidentesPublicos:
    """Datos para el mapa público (RF-08): no requiere sesión."""

    def __init__(self, incidentes: IncidenteRepository) -> None:
        self._incidentes = incidentes

    def ejecutar(self) -> list[Incidente]:
        return self._incidentes.listar(FiltroIncidentes())


class ObtenerIncidente:
    def __init__(self, incidentes: IncidenteRepository) -> None:
        self._incidentes = incidentes

    def ejecutar(self, actor: Usuario, incidente_id: int) -> Incidente:
        incidente = self._incidentes.obtener(incidente_id)
        if incidente is None:
            raise NoEncontradoError("El incidente no existe.")
        if tiene_permiso(actor, Permiso.VER_TODOS):
            return incidente
        exigir(actor, Permiso.VER_PROPIOS)
        if incidente.reportado_por != actor.id:
            raise PermisoDenegadoError("Solo puede consultar los incidentes que usted reportó.")
        return incidente


class CambiarEstado:
    def __init__(self, incidentes: IncidenteRepository, reloj: Reloj = datetime.now) -> None:
        self._incidentes = incidentes
        self._reloj = reloj

    def ejecutar(self, actor: Usuario, incidente_id: int, nuevo_estado: object,
                 comentario: str = "") -> Incidente:
        exigir(actor, Permiso.CAMBIAR_ESTADO)
        incidente = self._incidentes.obtener(incidente_id)
        if incidente is None:
            raise NoEncontradoError("El incidente no existe.")
        nuevo = EstadoIncidente.desde_texto(nuevo_estado)
        incidente.avanzar_estado(nuevo, actor.id, actor.nombre, self._reloj(), (comentario or "").strip())
        return self._incidentes.actualizar(incidente)


class AsignarResponsable:
    def __init__(self, incidentes: IncidenteRepository, cuadrillas: CuadrillaRepository) -> None:
        self._incidentes = incidentes
        self._cuadrillas = cuadrillas

    def ejecutar(self, actor: Usuario, incidente_id: int, cuadrilla_id: Optional[int] = None,
                 responsable: Optional[str] = None) -> Incidente:
        exigir(actor, Permiso.ASIGNAR_RESPONSABLE)
        responsable = (responsable or "").strip() or None
        if cuadrilla_id is None and responsable is None:
            raise ValidacionError("Indique una cuadrilla o un responsable.")
        incidente = self._incidentes.obtener(incidente_id)
        if incidente is None:
            raise NoEncontradoError("El incidente no existe.")
        if cuadrilla_id is not None:
            cuadrilla = self._cuadrillas.obtener(cuadrilla_id)
            if cuadrilla is None:
                raise NoEncontradoError("La cuadrilla no existe.")
            if not cuadrilla.activa:
                raise ValidacionError("La cuadrilla seleccionada está inactiva.")
        incidente.asignar(cuadrilla_id, responsable)
        return self._incidentes.actualizar(incidente)


class GestionarCuadrillas:
    def __init__(self, cuadrillas: CuadrillaRepository) -> None:
        self._cuadrillas = cuadrillas

    def listar(self, actor: Usuario, solo_activas: bool = False) -> list[Cuadrilla]:
        if not (tiene_permiso(actor, Permiso.ASIGNAR_RESPONSABLE)
                or tiene_permiso(actor, Permiso.GESTIONAR_CUADRILLAS)):
            exigir(None, Permiso.GESTIONAR_CUADRILLAS)
        todas = self._cuadrillas.listar()
        return [c for c in todas if c.activa] if solo_activas else todas

    def obtener(self, cuadrilla_id: int) -> Optional[Cuadrilla]:
        return self._cuadrillas.obtener(cuadrilla_id)

    def crear(self, actor: Usuario, nombre: str, responsable: str) -> Cuadrilla:
        exigir(actor, Permiso.GESTIONAR_CUADRILLAS)
        nombre, responsable = (nombre or "").strip(), (responsable or "").strip()
        if not nombre or not responsable:
            raise ValidacionError("El nombre de la cuadrilla y su responsable son obligatorios.")
        return self._cuadrillas.agregar(Cuadrilla(nombre, responsable))

    def cambiar_activa(self, actor: Usuario, cuadrilla_id: int, activa: bool) -> Cuadrilla:
        exigir(actor, Permiso.GESTIONAR_CUADRILLAS)
        cuadrilla = self._cuadrillas.obtener(cuadrilla_id)
        if cuadrilla is None:
            raise NoEncontradoError("La cuadrilla no existe.")
        cuadrilla.activa = activa
        return self._cuadrillas.actualizar(cuadrilla)
