from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from application.incidentes import CambiarEstado
from domain.errors import PermisoDenegadoError
from domain.value_objects import EstadoIncidente as E


def test_vecino_no_ve_dashboard(estadisticas, vecino):
    with pytest.raises(PermisoDenegadoError):
        estadisticas.ejecutar(vecino)


def test_sin_datos(estadisticas, funcionario):
    s = estadisticas.ejecutar(funcionario)
    assert s.total == 0 and s.tiempo_medio_respuesta_horas is None and s.zonas_criticas == []
    assert all(v == 0 for v in s.por_estado.values())


def test_conteos_zonas_y_tiempo_medio(registrar, repo, estadisticas, vecino, funcionario, datos_validos):
    a = registrar.ejecutar(vecino, datos_validos)
    b = registrar.ejecutar(vecino, replace(datos_validos, categoria="QUEMA", descripcion="Quema de residuos agrícolas"))
    registrar.ejecutar(vecino, replace(datos_validos, latitud=-17.37, longitud=-66.33))
    # a pasa a EN_ATENCION 10 h después de reportado; b 20 h después
    base = a.historial[0].fecha
    for inc, horas in ((a, 10), (b, 20)):
        cambiar = CambiarEstado(repo, reloj=lambda h=horas: base + timedelta(hours=h))
        cambiar.ejecutar(funcionario, inc.id, E.EN_REVISION)
        cambiar.ejecutar(funcionario, inc.id, E.EN_ATENCION)
    s = estadisticas.ejecutar(funcionario)
    assert s.total == 3
    assert s.por_estado["EN_ATENCION"] == 2 and s.por_estado["REPORTADO"] == 1
    assert s.por_categoria["BASURA"] == 2 and s.por_categoria["QUEMA"] == 1
    assert s.tiempo_medio_respuesta_horas == 15.0
    assert s.zonas_criticas[0][1] >= s.zonas_criticas[-1][1]
    assert sum(n for _, n in s.zonas_criticas) == 3
    assert s.sin_asignar == 3
