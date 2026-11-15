"""Adaptador de hash de contraseñas con bcrypt."""
from __future__ import annotations

import bcrypt

from domain.ports import HasheadorPassword


def _bytes(password: str) -> bytes:
    return password.encode("utf-8")[:72]  # bcrypt solo usa los primeros 72 bytes


class BcryptHasheador(HasheadorPassword):
    def hashear(self, password: str) -> str:
        return bcrypt.hashpw(_bytes(password), bcrypt.gensalt()).decode("utf-8")

    def verificar(self, password: str, hash_guardado: str) -> bool:
        try:
            return bcrypt.checkpw(_bytes(password), hash_guardado.encode("utf-8"))
        except (ValueError, TypeError):
            return False
