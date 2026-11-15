"""Paleta verde/institucional y colores por estado."""
from domain.value_objects import EstadoIncidente

VERDE_OSCURO = "#1b5e20"
VERDE = "#2e7d32"
VERDE_CLARO = "#66bb6a"

COLOR_ESTADO = {
    EstadoIncidente.REPORTADO: "#e53935",
    EstadoIncidente.EN_REVISION: "#fb8c00",
    EstadoIncidente.EN_ATENCION: "#1e88e5",
    EstadoIncidente.ATENDIDO: "#43a047",
    EstadoIncidente.CERRADO: "#757575",
}

CSS = """
<style>
  body { background: #f3f7f3; }
  .tarjeta { border-radius: 12px; box-shadow: 0 1px 6px rgba(27,94,32,.12); }
  .kpi-valor { font-size: 2rem; font-weight: 700; color: #1b5e20; line-height: 1.1; }
  .leaflet-container { z-index: 0; }
</style>
"""
