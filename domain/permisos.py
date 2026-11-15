"""RBAC (RF-10): permisos por rol y verificación centralizada."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from .entities import Usuario
from .errors import PermisoDenegadoError
from .value_objects import Rol


class Permiso(str, Enum):
    REGISTRAR_INCIDENTE = "REGISTRAR_INCIDENTE"
    VER_PROPIOS = "VER_PROPIOS"
    VER_TODOS = "VER_TODOS"
    CAMBIAR_ESTADO = "CAMBIAR_ESTADO"
    ASIGNAR_RESPONSABLE = "ASIGNAR_RESPONSABLE"
    VER_DASHBOARD = "VER_DASHBOARD"
    GESTIONAR_USUARIOS = "GESTIONAR_USUARIOS"
    GESTIONAR_CUADRILLAS = "GESTIONAR_CUADRILLAS"


_VECINO = {Permiso.REGISTRAR_INCIDENTE, Permiso.VER_PROPIOS}
_FUNCIONARIO = _VECINO | {Permiso.VER_TODOS, Permiso.CAMBIAR_ESTADO,
                          Permiso.ASIGNAR_RESPONSABLE, Permiso.VER_DASHBOARD}
_ADMIN = _FUNCIONARIO | {Permiso.GESTIONAR_USUARIOS, Permiso.GESTIONAR_CUADRILLAS}

PERMISOS_POR_ROL: dict[Rol, set[Permiso]] = {
    Rol.VECINO: _VECINO,
    Rol.FUNCIONARIO: _FUNCIONARIO,
    Rol.ADMIN: _ADMIN,
}


def tiene_permiso(usuario: Optional[Usuario], permiso: Permiso) -> bool:
    return bool(usuario and usuario.activo and permiso in PERMISOS_POR_ROL.get(usuario.rol, set()))


def exigir(usuario: Optional[Usuario], permiso: Permiso) -> None:
    if not tiene_permiso(usuario, permiso):
        raise PermisoDenegadoError("No tiene permisos para realizar esta operación.")
