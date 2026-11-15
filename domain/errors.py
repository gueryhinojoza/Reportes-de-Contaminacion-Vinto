"""Excepciones del dominio. La UI las traduce a mensajes para el usuario."""


class ErrorDeDominio(Exception):
    """Clase base de todos los errores de negocio."""


class ValidacionError(ErrorDeDominio):
    """Datos de entrada inválidos."""


class TransicionInvalidaError(ErrorDeDominio):
    """Cambio de estado no permitido."""


class PermisoDenegadoError(ErrorDeDominio):
    """El usuario no tiene permiso para la operación."""


class NoEncontradoError(ErrorDeDominio):
    """El recurso solicitado no existe."""


class AutenticacionError(ErrorDeDominio):
    """Credenciales incorrectas o usuario inactivo."""
