"""Reglas de negocio para la evidencia fotográfica (RF-04)."""
from __future__ import annotations

import os

from .errors import ValidacionError

EXTENSIONES_PERMITIDAS = {".jpg", ".jpeg", ".png", ".webp"}
TAMANO_MAXIMO_BYTES = 5 * 1024 * 1024


def _firma_valida(extension: str, contenido: bytes) -> bool:
    if extension in (".jpg", ".jpeg"):
        return contenido.startswith(b"\xff\xd8\xff")
    if extension == ".png":
        return contenido.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == ".webp":
        return contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP"
    return False


def validar_imagen(nombre: str, contenido: bytes, max_bytes: int = TAMANO_MAXIMO_BYTES) -> str:
    """Valida formato, firma binaria y tamaño. Devuelve la extensión normalizada."""
    extension = os.path.splitext(nombre or "")[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValidacionError("Formato de imagen no permitido. Use JPG, PNG o WEBP.")
    if not contenido:
        raise ValidacionError("El archivo de imagen está vacío.")
    if len(contenido) > max_bytes:
        raise ValidacionError(f"La imagen supera el tamaño máximo de {max_bytes // (1024 * 1024)} MB.")
    if not _firma_valida(extension, contenido):
        raise ValidacionError("El contenido del archivo no corresponde a una imagen válida.")
    return extension
