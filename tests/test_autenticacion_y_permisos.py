import pytest

from application.autenticacion import Autenticar, RegistrarUsuario
from domain.errors import AutenticacionError, PermisoDenegadoError, ValidacionError
from domain.value_objects import Rol
from tests.fakes import HasheadorFalso, UsuarioRepoMemoria


@pytest.fixture
def servicios():
    repo, h = UsuarioRepoMemoria(), HasheadorFalso()
    return repo, RegistrarUsuario(repo, h), Autenticar(repo, h)


def test_registro_y_login(servicios):
    _, registrar, autenticar = servicios
    registrar.ejecutar("Ana", "Ana@Mail.com", "secreta123")
    assert autenticar.ejecutar("ana@mail.com", "secreta123").rol == Rol.VECINO


def test_login_incorrecto(servicios):
    _, registrar, autenticar = servicios
    registrar.ejecutar("Ana", "ana@mail.com", "secreta123")
    with pytest.raises(AutenticacionError):
        autenticar.ejecutar("ana@mail.com", "otra")
    with pytest.raises(AutenticacionError):
        autenticar.ejecutar("nadie@mail.com", "secreta123")


def test_usuario_inactivo_no_entra(servicios):
    repo, registrar, autenticar = servicios
    u = registrar.ejecutar("Ana", "ana@mail.com", "secreta123")
    u.activo = False
    with pytest.raises(AutenticacionError):
        autenticar.ejecutar("ana@mail.com", "secreta123")


@pytest.mark.parametrize("nombre,email,pwd", [("", "a@b.co", "12345678"), ("A", "malo", "12345678"),
                                              ("A", "a@b.co", "corta")])
def test_validaciones_de_registro(servicios, nombre, email, pwd):
    with pytest.raises(ValidacionError):
        servicios[1].ejecutar(nombre, email, pwd)


def test_email_duplicado(servicios):
    registrar = servicios[1]
    registrar.ejecutar("Ana", "ana@mail.com", "secreta123")
    with pytest.raises(ValidacionError):
        registrar.ejecutar("Otra", "ana@mail.com", "secreta123")


def test_solo_admin_crea_roles_privilegiados(servicios, vecino, funcionario, admin):
    registrar = servicios[1]
    with pytest.raises(PermisoDenegadoError):
        registrar.ejecutar("X", "x@mail.com", "secreta123", Rol.FUNCIONARIO)
    with pytest.raises(PermisoDenegadoError):
        registrar.ejecutar("X", "x@mail.com", "secreta123", Rol.ADMIN, actor=funcionario)
    assert registrar.ejecutar("X", "x@mail.com", "secreta123", Rol.FUNCIONARIO, actor=admin).rol == Rol.FUNCIONARIO


def test_vecino_solo_ve_sus_incidentes(registrar, repo, vecino, funcionario, datos_validos):
    from application.incidentes import ListarIncidentes, ObtenerIncidente
    mio = registrar.ejecutar(vecino, datos_validos)
    ajeno = registrar.ejecutar(funcionario, datos_validos)
    assert [i.id for i in ListarIncidentes(repo).ejecutar(vecino)] == [mio.id]
    assert len(ListarIncidentes(repo).ejecutar(funcionario)) == 2
    with pytest.raises(PermisoDenegadoError):
        ObtenerIncidente(repo).ejecutar(vecino, ajeno.id)
