from datetime import datetime

import pytest

from application.estadisticas import ObtenerEstadisticas
from application.incidentes import (AsignarResponsable, CambiarEstado, DatosIncidente, RegistrarIncidente)
from domain.entities import Cuadrilla, Usuario
from domain.factory import IncidenteFactory
from domain.value_objects import Rol
from tests.fakes import AlmacenMemoria, CuadrillaRepoMemoria, IncidenteRepoMemoria, UsuarioRepoMemoria

AHORA = datetime(2026, 11, 15, 12, 0, 0)
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


@pytest.fixture
def repo():
    return IncidenteRepoMemoria()


@pytest.fixture
def cuadrillas():
    r = CuadrillaRepoMemoria()
    r.agregar(Cuadrilla("Cuadrilla Norte", "Juan Pérez"))
    r.agregar(Cuadrilla("Cuadrilla Inactiva", "Ana Gómez", activa=False))
    return r


@pytest.fixture
def almacen():
    return AlmacenMemoria()


@pytest.fixture
def usuarios():
    r = UsuarioRepoMemoria()
    r.agregar(Usuario("Admin", "admin@x.bo", "h", Rol.ADMIN))
    r.agregar(Usuario("Func", "func@x.bo", "h", Rol.FUNCIONARIO))
    r.agregar(Usuario("Vecino", "vecino@x.bo", "h", Rol.VECINO))
    return r


@pytest.fixture
def admin(usuarios):
    return usuarios.obtener(1)


@pytest.fixture
def funcionario(usuarios):
    return usuarios.obtener(2)


@pytest.fixture
def vecino(usuarios):
    return usuarios.obtener(3)


@pytest.fixture
def registrar(repo, almacen):
    return RegistrarIncidente(repo, almacen, IncidenteFactory(), reloj=lambda: AHORA)


@pytest.fixture
def datos_validos():
    return DatosIncidente(categoria="BASURA", descripcion="Acumulación de basura en la esquina",
                          latitud=-17.39, longitud=-66.31, referencia="Frente a la plaza",
                          fecha_hora=datetime(2026, 11, 14, 9, 0))


@pytest.fixture
def incidente(registrar, vecino, datos_validos):
    return registrar.ejecutar(vecino, datos_validos)


@pytest.fixture
def cambiar_estado(repo):
    return CambiarEstado(repo, reloj=lambda: AHORA)


@pytest.fixture
def asignar(repo, cuadrillas):
    return AsignarResponsable(repo, cuadrillas)


@pytest.fixture
def estadisticas(repo):
    return ObtenerEstadisticas(repo)
