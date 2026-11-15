"""Casos de uso de autenticación y usuarios."""
from __future__ import annotations

import re
from typing import Optional

from domain.entities import Usuario
from domain.errors import AutenticacionError, NoEncontradoError, ValidacionError
from domain.permisos import Permiso, exigir
from domain.ports import HasheadorPassword, UsuarioRepository
from domain.value_objects import Rol

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8


class Autenticar:
    def __init__(self, usuarios: UsuarioRepository, hasheador: HasheadorPassword) -> None:
        self._usuarios = usuarios
        self._hasheador = hasheador

    def ejecutar(self, email: str, password: str) -> Usuario:
        usuario = self._usuarios.obtener_por_email((email or "").strip().lower())
        if (usuario is None or not password
                or not self._hasheador.verificar(password, usuario.password_hash)):
            raise AutenticacionError("Correo o contraseña incorrectos.")
        if not usuario.activo:
            raise AutenticacionError("Su cuenta está desactivada. Contacte al administrador.")
        return usuario


class RegistrarUsuario:
    """Registro público (rol VECINO) o creación por un administrador (cualquier rol)."""

    def __init__(self, usuarios: UsuarioRepository, hasheador: HasheadorPassword) -> None:
        self._usuarios = usuarios
        self._hasheador = hasheador

    def ejecutar(self, nombre: str, email: str, password: str, rol: Rol = Rol.VECINO,
                 actor: Optional[Usuario] = None) -> Usuario:
        if rol != Rol.VECINO:
            exigir(actor, Permiso.GESTIONAR_USUARIOS)
        nombre = (nombre or "").strip()
        email = (email or "").strip().lower()
        if not nombre:
            raise ValidacionError("El nombre es obligatorio.")
        if not _EMAIL.match(email):
            raise ValidacionError("El correo electrónico no es válido.")
        if not password or len(password) < MIN_PASSWORD:
            raise ValidacionError(f"La contraseña debe tener al menos {MIN_PASSWORD} caracteres.")
        if self._usuarios.obtener_por_email(email):
            raise ValidacionError("Ya existe un usuario registrado con ese correo.")
        return self._usuarios.agregar(Usuario(nombre, email, self._hasheador.hashear(password), rol))


class GestionarUsuarios:
    def __init__(self, usuarios: UsuarioRepository) -> None:
        self._usuarios = usuarios

    def obtener(self, usuario_id: int) -> Optional[Usuario]:
        """Consulta sin permisos: usada para restaurar la sesión y mostrar nombres."""
        return self._usuarios.obtener(usuario_id)

    def listar(self, actor: Usuario) -> list[Usuario]:
        exigir(actor, Permiso.GESTIONAR_USUARIOS)
        return self._usuarios.listar()

    def cambiar_rol(self, actor: Usuario, usuario_id: int, rol: Rol) -> Usuario:
        exigir(actor, Permiso.GESTIONAR_USUARIOS)
        usuario = self._usuarios.obtener(usuario_id)
        if usuario is None:
            raise NoEncontradoError("El usuario no existe.")
        if usuario.id == actor.id and rol != Rol.ADMIN:
            raise ValidacionError("No puede quitarse a sí mismo el rol de administrador.")
        usuario.rol = Rol(rol)
        return self._usuarios.actualizar(usuario)

    def cambiar_activo(self, actor: Usuario, usuario_id: int, activo: bool) -> Usuario:
        exigir(actor, Permiso.GESTIONAR_USUARIOS)
        usuario = self._usuarios.obtener(usuario_id)
        if usuario is None:
            raise NoEncontradoError("El usuario no existe.")
        if usuario.id == actor.id and not activo:
            raise ValidacionError("No puede desactivar su propia cuenta.")
        usuario.activo = activo
        return self._usuarios.actualizar(usuario)
