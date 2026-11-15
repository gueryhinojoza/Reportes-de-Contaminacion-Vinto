import pytest

from domain.errors import NoEncontradoError, PermisoDenegadoError, TransicionInvalidaError, ValidacionError
from domain.value_objects import EstadoIncidente as E


def test_flujo_completo_valido(cambiar_estado, incidente, funcionario):
    for nuevo in (E.EN_REVISION, E.EN_ATENCION, E.ATENDIDO, E.CERRADO):
        resultado = cambiar_estado.ejecutar(funcionario, incidente.id, nuevo, "ok")
        assert resultado.estado == nuevo
    assert len(resultado.historial) == 5
    ultimo = resultado.historial[-1]
    assert ultimo.estado_anterior == E.ATENDIDO and ultimo.usuario_id == funcionario.id and ultimo.fecha


@pytest.mark.parametrize("destino", [E.EN_ATENCION, E.ATENDIDO, E.CERRADO, E.REPORTADO])
def test_no_se_permiten_saltos_ni_repeticiones(cambiar_estado, incidente, funcionario, destino):
    with pytest.raises(TransicionInvalidaError):
        cambiar_estado.ejecutar(funcionario, incidente.id, destino)


def test_no_se_puede_retroceder(cambiar_estado, incidente, funcionario):
    cambiar_estado.ejecutar(funcionario, incidente.id, E.EN_REVISION)
    with pytest.raises(TransicionInvalidaError):
        cambiar_estado.ejecutar(funcionario, incidente.id, E.REPORTADO)


def test_desde_cerrado_no_hay_transicion(cambiar_estado, incidente, admin):
    for nuevo in (E.EN_REVISION, E.EN_ATENCION, E.ATENDIDO, E.CERRADO):
        cambiar_estado.ejecutar(admin, incidente.id, nuevo)
    with pytest.raises(TransicionInvalidaError):
        cambiar_estado.ejecutar(admin, incidente.id, E.CERRADO)


def test_estado_invalido(cambiar_estado, incidente, funcionario):
    with pytest.raises(ValidacionError):
        cambiar_estado.ejecutar(funcionario, incidente.id, "VOLANDO")


def test_vecino_no_puede_cambiar_estado(cambiar_estado, incidente, vecino):
    with pytest.raises(PermisoDenegadoError):
        cambiar_estado.ejecutar(vecino, incidente.id, E.EN_REVISION)


def test_incidente_inexistente(cambiar_estado, funcionario):
    with pytest.raises(NoEncontradoError):
        cambiar_estado.ejecutar(funcionario, 999, E.EN_REVISION)
