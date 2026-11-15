"""Patrón Adapter: almacenamiento de imágenes en disco detrás del puerto AlmacenImagenes."""
from __future__ import annotations

import os
import uuid
from pathlib import Path

from domain.ports import AlmacenImagenes


class AlmacenImagenesEnDisco(AlmacenImagenes):
    def __init__(self, directorio: str | os.PathLike, prefijo_url: str = "/uploads") -> None:
        self._directorio = Path(directorio)
        self._directorio.mkdir(parents=True, exist_ok=True)
        self._prefijo = prefijo_url.rstrip("/")

    @property
    def directorio(self) -> Path:
        return self._directorio

    def guardar(self, nombre_original: str, contenido: bytes) -> str:
        extension = os.path.splitext(nombre_original)[1].lower()
        nombre = f"{uuid.uuid4().hex}{extension}"
        (self._directorio / nombre).write_bytes(contenido)
        return nombre

    def eliminar(self, nombre: str) -> None:
        try:
            (self._directorio / os.path.basename(nombre)).unlink(missing_ok=True)
        except OSError:
            pass

    def url_publica(self, nombre: str) -> str:
        return f"{self._prefijo}/{nombre}"
