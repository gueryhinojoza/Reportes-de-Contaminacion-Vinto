"""Siembra la base de datos: 1 admin, 1 funcionario, 1 vecino, 3 cuadrillas y 15 incidentes.

Uso:  python seed_data.py            (no hace nada si ya hay datos)
      python seed_data.py --reset    (borra la base SQLite y vuelve a sembrar)
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

from composition_root import resolver_db_url
from domain.entities import Cuadrilla, Usuario
from domain.factory import IncidenteFactory
from domain.value_objects import EstadoIncidente as E
from domain.value_objects import Rol
from infrastructure.password_hasher import BcryptHasheador
from infrastructure.repositorios import (SqlCuadrillaRepository, SqlIncidenteRepository, SqlUsuarioRepository,
                                         crear_engine, crear_tablas)

USUARIOS = [
    ("Administrador Vinto", "admin@vinto.gob.bo", "Admin123!", Rol.ADMIN),
    ("María Funcionaria", "funcionario@vinto.gob.bo", "Func123!", Rol.FUNCIONARIO),
    ("Carlos Vecino", "vecino@vinto.gob.bo", "Vecino123!", Rol.VECINO),
]
CUADRILLAS = [("Cuadrilla Limpieza Norte", "Juan Pérez"), ("Cuadrilla Control de Quemas", "Rosa Mamani"),
              ("Cuadrilla Recursos Hídricos", "Luis Quispe")]

# (categoría, descripción, referencia, lat, lon, días atrás, estado final, índice de cuadrilla)
INCIDENTES = [
    ("BASURA", "Acumulación de bolsas de basura en la esquina de la plaza principal", "Frente a la plaza de Vinto", -17.3925, -66.3130, 40, E.CERRADO, 0),
    ("BASURA", "Botadero clandestino con escombros y residuos domiciliarios", "Camino a Chilimarca", -17.3710, -66.3290, 25, E.ATENDIDO, 0),
    ("VERTIDO_ILEGAL", "Vertido de aceite usado en la acequia por un taller mecánico", "Detrás del taller Los Pinos", -17.4140, -66.3430, 33, E.CERRADO, 2),
    ("VERTIDO_ILEGAL", "Descarga de aguas residuales de color oscuro al canal de riego", "Canal Linde, altura puente", -17.4160, -66.3470, 12, E.EN_ATENCION, 2),
    ("QUEMA", "Quema de llantas y plásticos en un terreno baldío, humo denso", "Terreno junto a la cancha", -17.3890, -66.2860, 18, E.ATENDIDO, 1),
    ("QUEMA", "Quema de residuos agrícolas que afecta a las viviendas cercanas", "Zona agrícola Pairumani", -17.3910, -66.2840, 6, E.EN_REVISION, None),
    ("CONTAMINACION_RIOS", "Espuma blanca y mal olor en el río, posible descarga industrial", "Río Rocha, puente de Vinto", -17.4100, -66.3050, 21, E.EN_ATENCION, 2),
    ("CONTAMINACION_RIOS", "Animales muertos y basura flotando en el río", "Ribera del Río Rocha, sector sur", -17.4120, -66.3070, 3, E.REPORTADO, None),
    ("BASURA", "Contenedor desbordado hace una semana, malos olores", "Mercado de Lacma", -17.4300, -66.3260, 9, E.EN_REVISION, None),
    ("BASURA", "Residuos de construcción dejados en la vereda", "Avenida principal de Chilimarca", -17.3690, -66.3310, 2, E.REPORTADO, None),
    ("OTRO", "Polvo excesivo y ruido de una cantera sin control ambiental", "Cantera camino a Linde", -17.4180, -66.3400, 28, E.EN_ATENCION, 0),
    ("QUEMA", "Quema de pastizales cerca de la escuela, riesgo para los niños", "Escuela de Lacma", -17.4290, -66.3230, 1, E.REPORTADO, None),
    ("VERTIDO_ILEGAL", "Vertido de residuos químicos de una lavandería industrial", "Calle 6 de Agosto, Vinto Centro", -17.3940, -66.3150, 15, E.EN_REVISION, None),
    ("BASURA", "Basura acumulada bajo el puente peatonal", "Puente peatonal Vinto Centro", -17.3915, -66.3110, 5, E.REPORTADO, None),
    ("CONTAMINACION_RIOS", "Cambio de color del agua del río tras las lluvias, sospecha de vertido", "Río en Pairumani", -17.3880, -66.2880, 10, E.ATENDIDO, 2),
]
HORAS_ENTRE_ESTADOS = {E.EN_REVISION: 6, E.EN_ATENCION: 30, E.ATENDIDO: 72, E.CERRADO: 24}


def sembrar() -> None:
    db_url = resolver_db_url()
    if "--reset" in sys.argv and db_url.startswith("sqlite:///"):
        Path(db_url.replace("sqlite:///", "")).unlink(missing_ok=True)
    Path("data").mkdir(exist_ok=True)
    engine = crear_engine(db_url)
    crear_tablas(engine)
    usuarios, cuadrillas, incidentes = (SqlUsuarioRepository(engine), SqlCuadrillaRepository(engine),
                                        SqlIncidenteRepository(engine))
    if usuarios.obtener_por_email(USUARIOS[0][1]):
        print("La base ya contiene datos de ejemplo. Use `python seed_data.py --reset` para recrearla.")
        return

    hasher = BcryptHasheador()
    creados = {rol: usuarios.agregar(Usuario(n, e, hasher.hashear(p), rol)) for n, e, p, rol in USUARIOS}
    funcionario, vecino = creados[Rol.FUNCIONARIO], creados[Rol.VECINO]
    equipos = [cuadrillas.agregar(Cuadrilla(n, r)) for n, r in CUADRILLAS]

    ahora = datetime.now().replace(microsecond=0)
    factory = IncidenteFactory()
    for i, (cat, desc, ref, lat, lon, dias, final, idx_cuad) in enumerate(INCIDENTES):
        hecho = ahora - timedelta(days=dias, hours=3)
        registro = hecho + timedelta(hours=2)
        autor = vecino if i % 3 != 2 else funcionario
        inc = factory.crear(categoria=cat, descripcion=desc, latitud=lat, longitud=lon, referencia=ref,
                            fecha_hora=hecho, reportado_por=autor.id, ahora=registro)
        inc.registrar_creacion(autor.id, autor.nombre, registro)
        fecha = registro
        for estado in (E.EN_REVISION, E.EN_ATENCION, E.ATENDIDO, E.CERRADO):
            if list(E).index(estado) > list(E).index(final):
                break
            fecha = min(fecha + timedelta(hours=HORAS_ENTRE_ESTADOS[estado]), ahora)
            inc.avanzar_estado(estado, funcionario.id, funcionario.nombre, fecha, "Cambio de estado (datos de ejemplo)")
        if idx_cuad is not None:
            inc.asignar(equipos[idx_cuad].id, equipos[idx_cuad].responsable)
        incidentes.agregar(inc)

    print("Base de datos sembrada correctamente:")
    print(f"  - {len(USUARIOS)} usuarios, {len(CUADRILLAS)} cuadrillas, {len(INCIDENTES)} incidentes")
    for nombre, email, clave, rol in USUARIOS:
        print(f"  - {rol.etiqueta:<13} {email:<28} contraseña: {clave}")


if __name__ == "__main__":
    sembrar()
