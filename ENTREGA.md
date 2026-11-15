# Documento de entrega — Reporte de Incidentes Ambientales (Vinto)

Este documento reúne lo necesario para la defensa del proyecto: estructura, código clave, modelo de
datos, roles y ejecución. Complementa al [README](README.md).

**Stack:** Python 3.11+, NiceGUI, SQLModel/SQLite, bcrypt, PyTest, Docker.
**Arquitectura:** hexagonal (puertos y adaptadores) con dependencias hacia el dominio.

---

## 1. Estructura de carpetas

Salida de `tree` (sin `.venv`, `__pycache__`, `data/` ni `uploads/`):

```text
vinto_incidentes/
├── application/              # Casos de uso (orquestan dominio + puertos)
│   ├── __init__.py
│   ├── autenticacion.py
│   ├── estadisticas.py
│   └── incidentes.py
├── domain/                   # Reglas de negocio puras (sin NiceGUI ni SQL)
│   ├── __init__.py
│   ├── entities.py
│   ├── errors.py
│   ├── factory.py
│   ├── permisos.py
│   ├── ports.py
│   ├── reglas_imagen.py
│   ├── value_objects.py
│   └── zonas.py
├── infrastructure/           # Adaptadores concretos (SQLite, disco, bcrypt, geo)
│   ├── __init__.py
│   ├── almacen_imagenes.py
│   ├── db_models.py
│   ├── geolocalizacion.py
│   ├── password_hasher.py
│   └── repositorios.py
├── ui/                       # Adaptador de entrada (NiceGUI)
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── detalle.py
│   │   ├── lista.py
│   │   ├── mapa.py
│   │   └── nuevo_incidente.py
│   ├── __init__.py
│   ├── comun.py
│   ├── estilos.py
│   ├── layout.py
│   ├── mapa_adapter.py
│   ├── paginas.py
│   └── sesion.py
├── tests/                    # Pruebas con dobles en memoria (sin tocar SQLite)
│   ├── __init__.py
│   ├── conftest.py
│   ├── fakes.py
│   ├── test_asignar_responsable.py
│   ├── test_autenticacion_y_permisos.py
│   ├── test_cambiar_estado.py
│   ├── test_estadisticas.py
│   ├── test_factory.py
│   └── test_registrar_incidente.py
├── .dockerignore
├── composition_root.py       # Único lugar que arma las implementaciones
├── docker-compose.yml
├── Dockerfile
├── entrypoint.sh
├── main.py                   # Solo arranca la app
├── nicegui_compat.py         # Parche de compatibilidad NiceGUI/OneDrive
├── pytest.ini
├── README.md
├── requirements.txt
└── seed_data.py              # Datos de ejemplo
```

**Flujo de dependencias:** `ui` → `application` → `domain` ← `infrastructure`.
El dominio no importa nada de las otras capas; la infraestructura implementa las interfaces del dominio.

---

## 2. Código clave, SOLID y patrones

### 2.1 Entidad `Incidente` — `domain/entities.py`

Entidad **rica**: no es un saco de datos, protege sus reglas (RF-06, RF-07 y cálculo de tiempos).

```python
@dataclass
class Incidente:
    categoria: Categoria
    descripcion: str
    coordenada: Coordenada
    referencia: str
    fecha_hora: datetime
    zona: str
    reportado_por: int
    fecha_registro: datetime
    imagen: Optional[str] = None
    estado: EstadoIncidente = EstadoIncidente.REPORTADO
    cuadrilla_id: Optional[int] = None
    responsable: Optional[str] = None
    historial: list[CambioEstado] = field(default_factory=list)
    id: Optional[int] = None

    def registrar_creacion(self, usuario_id: Optional[int], usuario_nombre: str, fecha: datetime) -> None:
        self.historial.append(
            CambioEstado(None, EstadoIncidente.REPORTADO, fecha, usuario_id, usuario_nombre, "Incidente reportado")
        )

    def avanzar_estado(self, nuevo: EstadoIncidente, usuario_id: Optional[int], usuario_nombre: str,
                       fecha: datetime, comentario: str = "") -> None:
        """Regla RF-06: solo se avanza al siguiente estado, sin saltos ni retrocesos."""
        if not self.estado.puede_pasar_a(nuevo):
            permitido = self.estado.siguiente()
            detalle = (f"El siguiente estado permitido es «{permitido.etiqueta}»."
                       if permitido else "El incidente ya está en el estado final.")
            raise TransicionInvalidaError(
                f"No se puede pasar de «{self.estado.etiqueta}» a «{nuevo.etiqueta}». {detalle}"
            )
        self.historial.append(CambioEstado(self.estado, nuevo, fecha, usuario_id, usuario_nombre, comentario))
        self.estado = nuevo

    def asignar(self, cuadrilla_id: Optional[int], responsable: Optional[str]) -> None:
        self.cuadrilla_id = cuadrilla_id
        self.responsable = responsable

    def _fecha_de(self, estado: EstadoIncidente) -> Optional[datetime]:
        for cambio in self.historial:
            if cambio.estado_nuevo == estado:
                return cambio.fecha
        return None

    def tiempo_de_respuesta(self) -> Optional[timedelta]:
        """Tiempo entre REPORTADO y EN_ATENCION (None si aún no está en atención)."""
        inicio = self._fecha_de(EstadoIncidente.REPORTADO) or self.fecha_registro
        atencion = self._fecha_de(EstadoIncidente.EN_ATENCION)
        if atencion is None:
            return None
        return max(atencion - inicio, timedelta(0))
```

### 2.2 `IncidenteFactory` — `domain/factory.py`

**Patrón Factory** + **Strategy** (`ReglaCategoria`): la validación cambia según la categoría sin
modificar la fábrica (OCP). La fábrica recibe la función `zona_de` (inyección de dependencia) para
resolver la zona desde una coordenada.

```python
class ReglaCategoria(ABC):
    """Validaciones específicas de un tipo de incidente."""

    categoria: Categoria

    @abstractmethod
    def validar(self, descripcion: str, referencia: str) -> None: ...

    @staticmethod
    def _minimo(descripcion: str, minimo: int, nombre: str) -> None:
        if len(descripcion) < minimo:
            raise ValidacionError(f"Para «{nombre}» la descripción debe tener al menos {minimo} caracteres.")


class ReglaVertidoIlegal(ReglaCategoria):
    categoria = Categoria.VERTIDO_ILEGAL

    def validar(self, descripcion: str, referencia: str) -> None:
        self._minimo(descripcion, 15, "Vertido Ilegal")
        if not referencia:
            raise ValidacionError("Un vertido ilegal requiere una referencia del lugar u origen del vertido.")


class IncidenteFactory:
    """Crea la entidad Incidente aplicando validaciones comunes y las propias de cada tipo."""

    def __init__(self, zona_de: Callable[[Coordenada], str] = zona_mas_cercana,
                 reglas: Optional[list[ReglaCategoria]] = None) -> None:
        self._zona_de = zona_de
        lista = reglas or [ReglaBasura(), ReglaVertidoIlegal(), ReglaQuema(),
                           ReglaContaminacionRios(), ReglaOtro()]
        self._reglas = {r.categoria: r for r in lista}

    def crear(self, *, categoria: object, descripcion: Optional[str], latitud: object, longitud: object,
              referencia: Optional[str], fecha_hora: Optional[datetime], reportado_por: int,
              ahora: datetime, imagen: Optional[str] = None) -> Incidente:
        cat = Categoria.desde_texto(categoria)
        descripcion = (descripcion or "").strip()
        referencia = (referencia or "").strip()
        if not descripcion:
            raise ValidacionError("La descripción es obligatoria.")
        if len(descripcion) > MAX_DESCRIPCION:
            raise ValidacionError(f"La descripción no puede superar {MAX_DESCRIPCION} caracteres.")
        if latitud in (None, "") or longitud in (None, ""):
            raise ValidacionError("Debe indicar la ubicación (latitud y longitud).")
        coordenada = Coordenada(latitud, longitud)
        if fecha_hora is None:
            raise ValidacionError("La fecha y hora son obligatorias.")
        if fecha_hora > ahora + timedelta(minutes=5):
            raise ValidacionError("La fecha y hora del incidente no pueden estar en el futuro.")
        self._reglas[cat].validar(descripcion, referencia)
        return Incidente(
            categoria=cat, descripcion=descripcion, coordenada=coordenada, referencia=referencia,
            fecha_hora=fecha_hora, zona=self._zona_de(coordenada), reportado_por=reportado_por,
            fecha_registro=ahora, imagen=imagen,
        )
```

### 2.3 Adaptador — `infrastructure/almacen_imagenes.py`

**Patrón Adapter**: implementa el puerto `AlmacenImagenes` del dominio usando disco. El caso de uso no
sabe si las imágenes van a disco, S3 o memoria (en las pruebas se usa un doble en memoria).

```python
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
```

Otro adaptador destacable: `ui/mapa_adapter.py` (`LeafletMapaAdapter`) implementa `MapaPort`, de modo
que las páginas no dependen de la librería de mapas concreta.

### 2.4 Caso de uso — `application/incidentes.py`

**Patrón Command** (casos de uso como objetos con `ejecutar`) + **DTO** (`DatosIncidente`) +
**Dependency Injection** por constructor. `RegistrarIncidente` coordina permisos, fábrica, imágenes y
repositorio, y compensa si falla el guardado.

```python
@dataclass
class DatosIncidente:
    categoria: object
    descripcion: Optional[str]
    latitud: object
    longitud: object
    referencia: Optional[str] = ""
    fecha_hora: Optional[datetime] = None
    imagen_nombre: Optional[str] = None
    imagen_contenido: Optional[bytes] = None


class RegistrarIncidente:
    def __init__(self, incidentes: IncidenteRepository, almacen: AlmacenImagenes,
                 factory: IncidenteFactory, reloj: Reloj = datetime.now) -> None:
        self._incidentes = incidentes
        self._almacen = almacen
        self._factory = factory
        self._reloj = reloj

    def ejecutar(self, actor: Usuario, datos: DatosIncidente) -> Incidente:
        exigir(actor, Permiso.REGISTRAR_INCIDENTE)
        ahora = self._reloj()
        tiene_imagen = datos.imagen_contenido is not None or datos.imagen_nombre
        if tiene_imagen:
            validar_imagen(datos.imagen_nombre or "", datos.imagen_contenido or b"")
        incidente = self._factory.crear(
            categoria=datos.categoria, descripcion=datos.descripcion, latitud=datos.latitud,
            longitud=datos.longitud, referencia=datos.referencia, fecha_hora=datos.fecha_hora,
            reportado_por=actor.id, ahora=ahora,
        )
        nombre_imagen: Optional[str] = None
        if tiene_imagen:
            nombre_imagen = self._almacen.guardar(datos.imagen_nombre, datos.imagen_contenido)
            incidente.imagen = nombre_imagen
        incidente.registrar_creacion(actor.id, actor.nombre, ahora)
        try:
            return self._incidentes.agregar(incidente)
        except Exception:
            if nombre_imagen:
                self._almacen.eliminar(nombre_imagen)
            raise
```

### 2.5 `composition_root.py` — inyección de dependencias manual

Único punto que conoce las implementaciones concretas (DIP). Cambiar SQLite por otro motor o el
almacenamiento de imágenes solo afecta a este archivo.

```python
"""Composition Root: única clase que conoce las implementaciones concretas (DIP + inyección manual)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from application.autenticacion import Autenticar, GestionarUsuarios, RegistrarUsuario
from application.estadisticas import ObtenerEstadisticas
from application.incidentes import (AsignarResponsable, CambiarEstado, GestionarCuadrillas, ListarIncidentes,
                                    ListarIncidentesPublicos, ObtenerIncidente, RegistrarIncidente)
from domain.factory import IncidenteFactory
from domain.ports import AlmacenImagenes, HasheadorPassword, ServicioGeolocalizacion
from infrastructure.almacen_imagenes import AlmacenImagenesEnDisco
from infrastructure.geolocalizacion import GeolocalizacionVinto
from infrastructure.password_hasher import BcryptHasheador
from infrastructure.repositorios import (SqlCuadrillaRepository, SqlIncidenteRepository, SqlUsuarioRepository,
                                         crear_engine, crear_tablas)

BASE_DIR = Path(__file__).resolve().parent


@dataclass
class Contenedor:
    autenticar: Autenticar
    registrar_usuario: RegistrarUsuario
    usuarios: GestionarUsuarios
    cuadrillas: GestionarCuadrillas
    registrar_incidente: RegistrarIncidente
    listar_incidentes: ListarIncidentes
    listar_publicos: ListarIncidentesPublicos
    obtener_incidente: ObtenerIncidente
    cambiar_estado: CambiarEstado
    asignar_responsable: AsignarResponsable
    estadisticas: ObtenerEstadisticas
    almacen: AlmacenImagenes
    geo: ServicioGeolocalizacion
    hasheador: HasheadorPassword
    factory: IncidenteFactory
    directorio_uploads: Path


def resolver_db_url() -> str:
    return os.environ.get("VINTO_DB_URL") or f"sqlite:///{BASE_DIR / 'data' / 'vinto.db'}"


def resolver_uploads_dir() -> Path:
    return Path(os.environ.get("VINTO_UPLOADS") or BASE_DIR / "uploads")


def construir_contenedor(db_url: str | None = None, uploads_dir: str | os.PathLike | None = None) -> Contenedor:
    db_url = db_url or resolver_db_url()
    uploads_dir = Path(uploads_dir) if uploads_dir else resolver_uploads_dir()
    (BASE_DIR / "data").mkdir(exist_ok=True)

    engine = crear_engine(db_url)
    crear_tablas(engine)

    repo_usuarios = SqlUsuarioRepository(engine)
    repo_cuadrillas = SqlCuadrillaRepository(engine)
    repo_incidentes = SqlIncidenteRepository(engine)
    hasheador = BcryptHasheador()
    almacen = AlmacenImagenesEnDisco(uploads_dir)
    geo = GeolocalizacionVinto()
    factory = IncidenteFactory(zona_de=geo.zona_de)

    return Contenedor(
        autenticar=Autenticar(repo_usuarios, hasheador),
        registrar_usuario=RegistrarUsuario(repo_usuarios, hasheador),
        usuarios=GestionarUsuarios(repo_usuarios),
        cuadrillas=GestionarCuadrillas(repo_cuadrillas),
        registrar_incidente=RegistrarIncidente(repo_incidentes, almacen, factory),
        listar_incidentes=ListarIncidentes(repo_incidentes),
        listar_publicos=ListarIncidentesPublicos(repo_incidentes),
        obtener_incidente=ObtenerIncidente(repo_incidentes),
        cambiar_estado=CambiarEstado(repo_incidentes),
        asignar_responsable=AsignarResponsable(repo_incidentes, repo_cuadrillas),
        estadisticas=ObtenerEstadisticas(repo_incidentes),
        almacen=almacen, geo=geo, hasheador=hasheador, factory=factory, directorio_uploads=Path(uploads_dir),
    )
```

### 2.6 Dónde se aplicó SOLID

| Principio | Dónde | Cómo |
|---|---|---|
| **S** — Responsabilidad única | `domain`, `application`, `infrastructure`, `ui` | Cada capa/archivo tiene una responsabilidad: reglas, casos de uso, persistencia y presentación. `main.py` solo arranca. |
| **O** — Abierto/cerrado | `ReglaCategoria` + `IncidenteFactory` | Agregar una categoría = nueva clase de regla, sin tocar la fábrica. |
| **L** — Sustitución de Liskov | `domain/ports.py` | `SqlIncidenteRepository` y `IncidenteRepoMemoria` (tests) son intercambiables donde se espera `IncidenteRepository`. Igual con `AlmacenImagenes`. |
| **I** — Segregación de interfaces | `ports.py` | Puertos pequeños y específicos (`IncidenteRepository`, `UsuarioRepository`, `AlmacenImagenes`, `HasheadorPassword`, `ServicioGeolocalizacion`). |
| **D** — Inversión de dependencias | `composition_root.py` | Casos de uso dependen de abstracciones; solo el composition root instancia SQLite, bcrypt y disco. |

Patrones usados: **Factory** (`IncidenteFactory`), **Strategy** (`ReglaCategoria`), **Adapter**
(`AlmacenImagenesEnDisco`, `LeafletMapaAdapter`), **Repository** (`Sql*Repository`), **Ports &
Adapters**, **Command** (casos de uso con `ejecutar`), **DTO** (`DatosIncidente`, `FiltroIncidentes`),
**Value Object** (`Coordenada`, `Categoria`, `EstadoIncidente`, `Rol`), **Dependency Injection** manual.

---

## 3. Base de datos (SQLModel)

Archivo: `infrastructure/db_models.py`. Los modelos de tabla están **separados** de las entidades del
dominio (mapeo explícito en `infrastructure/repositorios.py`).

```python
class UsuarioDB(SQLModel, table=True):
    __tablename__ = "usuarios"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    rol: str
    activo: bool = True


class CuadrillaDB(SQLModel, table=True):
    __tablename__ = "cuadrillas"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    responsable: str
    activa: bool = True


class IncidenteDB(SQLModel, table=True):
    __tablename__ = "incidentes"
    id: Optional[int] = Field(default=None, primary_key=True)
    categoria: str = Field(index=True)
    descripcion: str
    latitud: float
    longitud: float
    referencia: str = ""
    fecha_hora: NaiveDatetime = Field(index=True)
    fecha_registro: NaiveDatetime
    zona: str = Field(index=True)
    imagen: Optional[str] = None
    estado: str = Field(index=True)
    reportado_por: int = Field(index=True)
    cuadrilla_id: Optional[int] = None
    responsable: Optional[str] = None


class CambioEstadoDB(SQLModel, table=True):
    __tablename__ = "historial_estados"
    id: Optional[int] = Field(default=None, primary_key=True)
    incidente_id: int = Field(index=True)
    estado_anterior: Optional[str] = None
    estado_nuevo: str
    fecha: NaiveDatetime
    usuario_id: Optional[int] = None
    usuario_nombre: str = ""
    comentario: str = ""
```

| Tabla | Propósito | Relación |
|---|---|---|
| `usuarios` | Cuentas con rol y hash bcrypt | `incidentes.reportado_por` → `usuarios.id` |
| `cuadrillas` | Equipos de atención | `incidentes.cuadrilla_id` → `cuadrillas.id` |
| `incidentes` | Reporte ambiental y su estado actual | `id` referenciado por el historial |
| `historial_estados` | Trazabilidad de cada transición (RF-06) y cálculo de tiempos | `incidente_id` → `incidentes.id` |

- Los índices están en `email`, `categoria`, `fecha_hora`, `zona`, `estado`, `reportado_por` e
  `incidente_id` para acelerar los filtros de RF-05 y las estadísticas de RF-09.
- SQLite en `data/vinto.db` en local; en Docker, `/app/data/vinto.db` dentro de un volumen.
- Las relaciones se mantienen por clave (sin `ForeignKey` de SQLAlchemy) y el repositorio arma la
  entidad completa, incluido su historial, en una sola consulta adicional.

---

## 4. Roles, permisos y usuarios de prueba

RBAC centralizado en `domain/permisos.py`; se verifica **en la UI** (`ui/sesion.py`,
`exigir_pagina`) y **dentro de cada caso de uso** (`exigir(actor, Permiso...)`).

| Permiso | Vecino | Funcionario | Admin |
|---|:--:|:--:|:--:|
| Registrar incidentes | ✔ | ✔ | ✔ |
| Ver incidentes propios | ✔ | ✔ | ✔ |
| Ver todos los incidentes | — | ✔ | ✔ |
| Cambiar estado | — | ✔ | ✔ |
| Asignar cuadrilla/responsable | — | ✔ | ✔ |
| Ver dashboard | — | ✔ | ✔ |
| Gestionar usuarios | — | — | ✔ |
| Gestionar cuadrillas | — | — | ✔ |

**Qué hace cada rol**
- **Vecino (ciudadano):** se registra/inicia sesión, reporta incidentes con foto y ubicación en el mapa,
  y consulta **solo sus** reportes y su estado.
- **Funcionario municipal:** ve todos los incidentes, aplica filtros, avanza estados en el flujo
  REPORTADO → EN REVISIÓN → EN ATENCIÓN → ATENDIDO → CERRADO, asigna cuadrillas y usa el dashboard.
- **Administrador:** todo lo del funcionario más la gestión de usuarios (alta/activación/rol) y de
  cuadrillas (crear/activar/desactivar).

**Credenciales de demo** (creadas por `seed_data.py`)

| Rol | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@vinto.gob.bo` | `Admin123!` |
| Funcionario | `funcionario@vinto.gob.bo` | `Func123!` |
| Vecino | `vecino@vinto.gob.bo` | `Vecino123!` |

> También puede registrarse un vecino nuevo desde la pantalla de registro.

---

## 5. Cómo ejecutarla

### 5.1 Con Docker (recomendado)

```bash
docker compose up --build
```

Abrir **http://localhost:8080**.

**`Dockerfile`** (python:3.11-slim, usuario no root, sin caché de pip):

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --create-home --shell /bin/bash app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/uploads && chown -R app:app /app

USER app

EXPOSE 8080

ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
```

**`docker-compose.yml`** (puerto 8080 y volúmenes para BD e imágenes):

```yaml
services:
  web:
    build: .
    container_name: vinto_incidentes
    ports:
      - "8080:8080"
    environment:
      VINTO_DB_URL: sqlite:////app/data/vinto.db
      VINTO_UPLOADS: /app/uploads
      STORAGE_SECRET: ${STORAGE_SECRET:-cambiar}
    volumes:
      - data:/app/data
      - uploads:/app/uploads
    restart: unless-stopped

volumes:
  data:
  uploads:
```

**`entrypoint.sh`** siembra solo la primera vez:

```sh
#!/bin/sh
set -eu

export VINTO_DB_URL="${VINTO_DB_URL:-sqlite:////app/data/vinto.db}"
export VINTO_UPLOADS="${VINTO_UPLOADS:-/app/uploads}"
export STORAGE_SECRET="${STORAGE_SECRET:-cambiar}"

case "$VINTO_DB_URL" in
    sqlite:///*) DB_PATH="${VINTO_DB_URL#sqlite:///}" ;;
    *)           DB_PATH="" ;;
esac

mkdir -p "$VINTO_UPLOADS"
if [ -n "$DB_PATH" ]; then
    mkdir -p "$(dirname "$DB_PATH")"
fi

if [ -n "$DB_PATH" ] && [ -f "$DB_PATH" ]; then
    echo "[entrypoint] Base de datos encontrada en $DB_PATH; no se siembra de nuevo."
else
    echo "[entrypoint] No existe la base de datos; ejecutando seed_data.py..."
    python seed_data.py
fi

exec python main.py
```

Comandos útiles:

| Acción | Comando |
|---|---|
| Construir y levantar | `docker compose up --build` |
| Levantar en segundo plano | `docker compose up -d --build` |
| Ver logs | `docker compose logs -f` |
| Detener (conserva datos) | `docker compose down` |
| Detener y borrar volúmenes | `docker compose down -v` |
| Re-sembrar la base | `docker compose run --rm --entrypoint python web seed_data.py --reset` |

### 5.2 Local (sin Docker)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py
python main.py                   # http://localhost:8080
```

Pruebas: `pytest` → **67 pruebas** (repositorios y almacenamiento en memoria).

---

## 6. Trazabilidad de requisitos

| RF | Requisito | Dónde se implementa |
|---|---|---|
| RF-01 | Registro de incidentes | `ui/pages/nuevo_incidente.py`, `RegistrarIncidente`, `IncidenteFactory` |
| RF-02 | Categorización dinámica | `Categoria` (value object) y reglas por categoría en `domain/factory.py` |
| RF-03 | Geolocalización | `Coordenada`, `LeafletMapaAdapter.fijar_punto`, `GeolocalizacionVinto.zona_de` |
| RF-04 | Evidencia fotográfica | `domain/reglas_imagen.py`, `AlmacenImagenesEnDisco`, `ui.upload` en el formulario |
| RF-05 | Consulta y filtrado | `ListarIncidentes`, `FiltroIncidentes`, `SqlIncidenteRepository.listar`, `ui/pages/lista.py` |
| RF-06 | Gestión de estados | `Incidente.avanzar_estado`, `EstadoIncidente.puede_pasar_a`, `CambiarEstado`, `ui/pages/detalle.py` |
| RF-07 | Asignación de responsables | `AsignarResponsable`, `Cuadrilla`, `ui/pages/detalle.py`, `ui/pages/admin.py` |
| RF-08 | Mapa interactivo | `ui/pages/mapa.py`, `LeafletMapaAdapter`, `ListarIncidentesPublicos` |
| RF-09 | Dashboard y estadísticas | `ObtenerEstadisticas`, `ui/pages/dashboard.py` (tarjetas + gráficos `ui.echart`) |
| RF-10 | Control de acceso y roles | `domain/permisos.py` (RBAC), `ui/sesion.py`, verificación en cada caso de uso |
