from datetime import datetime

import pytest

from domain.errors import ValidacionError
from domain.factory import IncidenteFactory
from domain.value_objects import Categoria

AHORA = datetime(2026, 11, 15, 12, 0)


def crear(**kw):
    base = dict(categoria="BASURA", descripcion="Basura acumulada en la calle", latitud=-17.39, longitud=-66.31,
                referencia="", fecha_hora=datetime(2026, 11, 14), reportado_por=1, ahora=AHORA)
    base.update(kw)
    return IncidenteFactory().crear(**base)


@pytest.mark.parametrize("cat,desc,ref", [
    ("BASURA", "Basura en la vía", ""),
    ("VERTIDO_ILEGAL", "Vertido de aceite en el canal", "Detrás de la fábrica"),
    ("QUEMA", "Quema de llantas viejas", ""),
    ("CONTAMINACION_RIOS", "Espuma y mal olor en el agua", "Río Rocha, puente Vinto"),
    ("OTRO", "Ruido y polvo excesivo de una cantera", ""),
])
def test_crea_cada_categoria(cat, desc, ref):
    inc = crear(categoria=cat, descripcion=desc, referencia=ref)
    assert inc.categoria == Categoria(cat) and inc.zona


@pytest.mark.parametrize("cat,desc,ref", [
    ("BASURA", "corta", ""),
    ("VERTIDO_ILEGAL", "Vertido de aceite en el canal", ""),
    ("VERTIDO_ILEGAL", "corto", "ref"),
    ("QUEMA", "humo", ""),
    ("CONTAMINACION_RIOS", "Espuma y mal olor en el agua", ""),
    ("OTRO", "Algo raro pasa aqui", ""),
])
def test_reglas_propias_por_categoria(cat, desc, ref):
    with pytest.raises(ValidacionError):
        crear(categoria=cat, descripcion=desc, referencia=ref)


def test_descripcion_demasiado_larga():
    with pytest.raises(ValidacionError):
        crear(descripcion="x" * 1001)


def test_zona_asignada_segun_coordenada():
    assert crear(latitud=-17.3700, longitud=-66.3300).zona == "Chilimarca"
    assert crear(latitud=-10.0, longitud=-60.0).zona == "Otra zona"


def test_descripcion_se_normaliza():
    assert crear(descripcion="   Basura en la esquina   ").descripcion == "Basura en la esquina"
