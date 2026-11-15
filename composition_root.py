"""Composition Root: única clase que conoce las implementaciones concretas (DIP + inyección manual)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from application.autenticacion import Autenticar, GestionarUsuarios, RegistrarUsuario
from application.estadisticas import ObtenerEstadisticas
from application.incidentes import (AsignarResponsable, CambiarEstado, GestionarCuadrillas, ListarIncidentes,
                                    ListarIncidentesPublicos, ObtenerIncidente, RegistrarIncidente)
from domain.factory import IncidenteFactory
from domain.ports import AlmacenImagenes, HasheadorPassword, ServicioGeolocalizacion
from infrastructure.almacen_imagenes import AlmacenImagenesEnDisco
from infrastructure.geolocalizacion import GeolocalizacionVinto
from infrastructure.password_hasher import BcryptHasheador
from infrastructure.repositorios import (SqlCuadrillaRepository, SqlIncidenteRepository, SqlUsuarioRepository,
                                         crear_engine, crear_tablas)

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class Contenedor:
    autenticar: Autenticar
    registrar_usuario: RegistrarUsuario
    usuarios: GestionarUsuarios
    cuadrillas: GestionarCuadrillas
    registrar_incidente: RegistrarIncidente
    listar_incidentes: ListarIncidentes
    listar_publicos: ListarIncidentesPublicos
    obtener_incidente: ObtenerIncidente
    cambiar_estado: CambiarEstado
    asignar_responsable: AsignarResponsable
    estadisticas: ObtenerEstadisticas
    almacen: AlmacenImagenes
    geo: ServicioGeolocalizacion
    hasheador: HasheadorPassword
    factory: IncidenteFactory
    directorio_uploads: Path


def resolver_db_url() -> str:
    return os.environ.get("VINTO_DB_URL") or f"sqlite:///{BASE_DIR / 'data' / 'vinto.db'}"


def resolver_uploads_dir() -> Path:
    return Path(os.environ.get("VINTO_UPLOADS") or BASE_DIR / "uploads")


def construir_contenedor(db_url: str | None = None, uploads_dir: str | os.PathLike | None = None) -> Contenedor:
    db_url = db_url or resolver_db_url()
    uploads_dir = Path(uploads_dir) if uploads_dir else resolver_uploads_dir()
    (BASE_DIR / "data").mkdir(exist_ok=True)

    engine = crear_engine(db_url)
    crear_tablas(engine)

    repo_usuarios = SqlUsuarioRepository(engine)
    repo_cuadrillas = SqlCuadrillaRepository(engine)
    repo_incidentes = SqlIncidenteRepository(engine)
    hasheador = BcryptHasheador()
    almacen = AlmacenImagenesEnDisco(uploads_dir)
    geo = GeolocalizacionVinto()
    factory = IncidenteFactory(zona_de=geo.zona_de)

    return Contenedor(
        autenticar=Autenticar(repo_usuarios, hasheador),
        registrar_usuario=RegistrarUsuario(repo_usuarios, hasheador),
        usuarios=GestionarUsuarios(repo_usuarios),
        cuadrillas=GestionarCuadrillas(repo_cuadrillas),
        registrar_incidente=RegistrarIncidente(repo_incidentes, almacen, factory),
        listar_incidentes=ListarIncidentes(repo_incidentes),
        listar_publicos=ListarIncidentesPublicos(repo_incidentes),
        obtener_incidente=ObtenerIncidente(repo_incidentes),
        cambiar_estado=CambiarEstado(repo_incidentes),
        asignar_responsable=AsignarResponsable(repo_incidentes, repo_cuadrillas),
        estadisticas=ObtenerEstadisticas(repo_incidentes),
        almacen=almacen, geo=geo, hasheador=hasheador, factory=factory, directorio_uploads=Path(uploads_dir),
    )
