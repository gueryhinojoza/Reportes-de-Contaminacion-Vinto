import pytest

from domain.errors import NoEncontradoError, PermisoDenegadoError, ValidacionError


def test_funcionario_asigna_cuadrilla(asignar, incidente, funcionario):
    r = asignar.ejecutar(funcionario, incidente.id, cuadrilla_id=1)
    assert r.cuadrilla_id == 1


def test_admin_asigna_responsable_texto(asignar, incidente, admin):
    r = asignar.ejecutar(admin, incidente.id, responsable="  Ing. Rojas ")
    assert r.responsable == "Ing. Rojas"


def test_vecino_no_puede_asignar(asignar, incidente, vecino):
    with pytest.raises(PermisoDenegadoError):
        asignar.ejecutar(vecino, incidente.id, cuadrilla_id=1)


def test_sin_usuario_no_puede_asignar(asignar, incidente):
    with pytest.raises(PermisoDenegadoError):
        asignar.ejecutar(None, incidente.id, cuadrilla_id=1)


def test_requiere_cuadrilla_o_responsable(asignar, incidente, funcionario):
    with pytest.raises(ValidacionError):
        asignar.ejecutar(funcionario, incidente.id)


def test_cuadrilla_inexistente(asignar, incidente, funcionario):
    with pytest.raises(NoEncontradoError):
        asignar.ejecutar(funcionario, incidente.id, cuadrilla_id=99)


def test_cuadrilla_inactiva(asignar, incidente, funcionario):
    with pytest.raises(ValidacionError):
        asignar.ejecutar(funcionario, incidente.id, cuadrilla_id=2)


def test_incidente_inexistente(asignar, funcionario):
    with pytest.raises(NoEncontradoError):
        asignar.ejecutar(funcionario, 999, cuadrilla_id=1)
