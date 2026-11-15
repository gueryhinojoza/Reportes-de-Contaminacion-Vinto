"""Caso de uso ObtenerEstadisticas (RF-09)."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from domain.entities import Usuario
from domain.permisos import Permiso, exigir
from domain.ports import FiltroIncidentes, IncidenteRepository
from domain.value_objects import Categoria, EstadoIncidente


@dataclass
class Estadisticas:
    total: int = 0
    por_estado: dict[str, int] = field(default_factory=dict)
    por_categoria: dict[str, int] = field(default_factory=dict)
    tiempo_medio_respuesta_horas: Optional[float] = None
    zonas_criticas: list[tuple[str, int]] = field(default_factory=list)
    sin_asignar: int = 0


class ObtenerEstadisticas:
    def __init__(self, incidentes: IncidenteRepository, top_zonas: int = 5) -> None:
        self._incidentes = incidentes
        self._top = top_zonas

    def ejecutar(self, actor: Usuario) -> Estadisticas:
        exigir(actor, Permiso.VER_DASHBOARD)
        incidentes = self._incidentes.listar(FiltroIncidentes())
        por_estado = {e.value: 0 for e in EstadoIncidente}
        por_categoria = {c.value: 0 for c in Categoria}
        zonas: Counter[str] = Counter()
        tiempos: list[float] = []
        sin_asignar = 0
        for inc in incidentes:
            por_estado[inc.estado.value] += 1
            por_categoria[inc.categoria.value] += 1
            zonas[inc.zona] += 1
            if inc.cuadrilla_id is None and not inc.responsable:
                sin_asignar += 1
            tiempo = inc.tiempo_de_respuesta()
            if tiempo is not None:
                tiempos.append(tiempo.total_seconds() / 3600)
        medio = round(sum(tiempos) / len(tiempos), 2) if tiempos else None
        criticas = sorted(zonas.items(), key=lambda kv: (-kv[1], kv[0]))[: self._top]
        return Estadisticas(len(incidentes), por_estado, por_categoria, medio, criticas, sin_asignar)
