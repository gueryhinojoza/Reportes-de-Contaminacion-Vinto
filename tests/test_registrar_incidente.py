from dataclasses import replace

import pytest

from application.incidentes import DatosIncidente
from domain.errors import PermisoDenegadoError, ValidacionError
from domain.value_objects import EstadoIncidente
from tests.conftest import PNG


def test_caso_feliz(registrar, repo, vecino, datos_validos):
    inc = registrar.ejecutar(vecino, datos_validos)
    assert inc.id == 1
    assert inc.estado == EstadoIncidente.REPORTADO
    assert inc.reportado_por == vecino.id
    assert inc.zona
    assert len(inc.historial) == 1 and inc.historial[0].estado_nuevo == EstadoIncidente.REPORTADO
    assert repo.obtener(1) is not None


@pytest.mark.parametrize("campo,valor", [("descripcion", ""), ("descripcion", "   "), ("descripcion", None),
                                         ("latitud", None), ("longitud", ""), ("fecha_hora", None)])
def test_campos_vacios(registrar, vecino, datos_validos, campo, valor):
    with pytest.raises(ValidacionError):
        registrar.ejecutar(vecino, replace(datos_validos, **{campo: valor}))


def test_categoria_invalida(registrar, vecino, datos_validos):
    with pytest.raises(ValidacionError):
        registrar.ejecutar(vecino, replace(datos_validos, categoria="INEXISTENTE"))


@pytest.mark.parametrize("lat,lon", [(91, -66), (-91, -66), (-17, 181), (-17, -181), ("abc", -66)])
def test_coordenadas_fuera_de_rango(registrar, vecino, datos_validos, lat, lon):
    with pytest.raises(ValidacionError):
        registrar.ejecutar(vecino, replace(datos_validos, latitud=lat, longitud=lon))


def test_fecha_futura_rechazada(registrar, vecino, datos_validos):
    from datetime import datetime
    with pytest.raises(ValidacionError):
        registrar.ejecutar(vecino, replace(datos_validos, fecha_hora=datetime(2027, 1, 1)))


@pytest.mark.parametrize("nombre,contenido", [("foto.gif", PNG), ("foto.pdf", PNG), ("foto.png", b""),
                                              ("foto.png", b"no soy una imagen"),
                                              ("foto.png", PNG + b"0" * (5 * 1024 * 1024))])
def test_imagen_invalida(registrar, almacen, repo, vecino, datos_validos, nombre, contenido):
    with pytest.raises(ValidacionError):
        registrar.ejecutar(vecino, replace(datos_validos, imagen_nombre=nombre, imagen_contenido=contenido))
    assert almacen.archivos == {} and repo.datos == {}


def test_imagen_valida_se_guarda(registrar, almacen, vecino, datos_validos):
    inc = registrar.ejecutar(vecino, replace(datos_validos, imagen_nombre="foto.png", imagen_contenido=PNG))
    assert inc.imagen in almacen.archivos


def test_si_falla_el_repositorio_se_elimina_la_imagen(registrar, repo, almacen, vecino, datos_validos):
    repo.fallar = True
    with pytest.raises(RuntimeError):
        registrar.ejecutar(vecino, replace(datos_validos, imagen_nombre="foto.png", imagen_contenido=PNG))
    assert almacen.archivos == {}


def test_usuario_inactivo_no_puede_registrar(registrar, vecino, datos_validos):
    vecino.activo = False
    with pytest.raises(PermisoDenegadoError):
        registrar.ejecutar(vecino, datos_validos)


def test_sin_usuario_no_puede_registrar(registrar, datos_validos):
    with pytest.raises(PermisoDenegadoError):
        registrar.ejecutar(None, datos_validos)
