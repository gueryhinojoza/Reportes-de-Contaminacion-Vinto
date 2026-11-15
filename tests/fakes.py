"""Dobles de prueba en memoria para los puertos."""
from __future__ import annotations

import copy
from typing import Optional

from domain.entities import Cuadrilla, Incidente, Usuario
from domain.ports import (AlmacenImagenes, CuadrillaRepository, FiltroIncidentes, HasheadorPassword,
                          IncidenteRepository, UsuarioRepository)


class IncidenteRepoMemoria(IncidenteRepository):
    def __init__(self) -> None:
        self.datos: dict[int, Incidente] = {}
        self._seq = 0
        self.fallar = False

    def agregar(self, incidente: Incidente) -> Incidente:
        if self.fallar:
            raise RuntimeError("fallo de base de datos")
        self._seq += 1
        incidente.id = self._seq
        self.datos[incidente.id] = copy.deepcopy(incidente)
        return incidente

    def actualizar(self, incidente: Incidente) -> Incidente:
        self.datos[incidente.id] = copy.deepcopy(incidente)
        return incidente

    def obtener(self, incidente_id: int) -> Optional[Incidente]:
        inc = self.datos.get(incidente_id)
        return copy.deepcopy(inc) if inc else None

    def listar(self, filtro: Optional[FiltroIncidentes] = None) -> list[Incidente]:
        f = filtro or FiltroIncidentes()
        res = []
        for i in self.datos.values():
            if f.categoria and i.categoria != f.categoria:
                continue
            if f.estado and i.estado != f.estado:
                continue
            if f.zona and i.zona != f.zona:
                continue
            if f.reportado_por is not None and i.reportado_por != f.reportado_por:
                continue
            if f.desde and i.fecha_hora.date() < f.desde:
                continue
            if f.hasta and i.fecha_hora.date() > f.hasta:
                continue
            res.append(copy.deepcopy(i))
        return sorted(res, key=lambda x: x.fecha_hora, reverse=True)


class CuadrillaRepoMemoria(CuadrillaRepository):
    def __init__(self) -> None:
        self.datos: dict[int, Cuadrilla] = {}
        self._seq = 0

    def agregar(self, cuadrilla: Cuadrilla) -> Cuadrilla:
        self._seq += 1
        cuadrilla.id = self._seq
        self.datos[cuadrilla.id] = cuadrilla
        return cuadrilla

    def actualizar(self, cuadrilla: Cuadrilla) -> Cuadrilla:
        self.datos[cuadrilla.id] = cuadrilla
        return cuadrilla

    def obtener(self, cuadrilla_id: int) -> Optional[Cuadrilla]:
        return self.datos.get(cuadrilla_id)

    def listar(self) -> list[Cuadrilla]:
        return list(self.datos.values())


class UsuarioRepoMemoria(UsuarioRepository):
    def __init__(self) -> None:
        self.datos: dict[int, Usuario] = {}
        self._seq = 0

    def agregar(self, usuario: Usuario) -> Usuario:
        self._seq += 1
        usuario.id = self._seq
        self.datos[usuario.id] = usuario
        return usuario

    def actualizar(self, usuario: Usuario) -> Usuario:
        self.datos[usuario.id] = usuario
        return usuario

    def obtener(self, usuario_id: int) -> Optional[Usuario]:
        return self.datos.get(usuario_id)

    def obtener_por_email(self, email: str) -> Optional[Usuario]:
        return next((u for u in self.datos.values() if u.email == email.lower()), None)

    def listar(self) -> list[Usuario]:
        return list(self.datos.values())


class AlmacenMemoria(AlmacenImagenes):
    def __init__(self) -> None:
        self.archivos: dict[str, bytes] = {}

    def guardar(self, nombre_original: str, contenido: bytes) -> str:
        nombre = f"img{len(self.archivos) + 1}_{nombre_original}"
        self.archivos[nombre] = contenido
        return nombre

    def eliminar(self, nombre: str) -> None:
        self.archivos.pop(nombre, None)

    def url_publica(self, nombre: str) -> str:
        return f"/uploads/{nombre}"


class HasheadorFalso(HasheadorPassword):
    def hashear(self, password: str) -> str:
        return f"hash:{password}"

    def verificar(self, password: str, hash_guardado: str) -> bool:
        return hash_guardado == f"hash:{password}"
