# Reporte de Incidentes Medio Ambientales — Municipio de Vinto

MVP para la materia **Taller de Programación**. Permite a los vecinos reportar incidentes ambientales
(basura, vertidos ilegales, quemas, contaminación de ríos, otros) con ubicación en mapa y foto, y a los
funcionarios gestionarlos (estados, asignación de cuadrillas, dashboard).

**Stack:** Python 3.11+, NiceGUI (UI + backend), SQLModel + SQLite, bcrypt, PyTest.
**Arquitectura:** hexagonal / Clean Architecture con SOLID (`domain` → `application` → `infrastructure` / `ui`).

📄 **Documento de entrega completo:** [ENTREGA.md](ENTREGA.md) (estructura, código clave, SOLID, modelo de datos, roles y trazabilidad de RF).

## Docker (recomendado)

Requisitos: Docker con el plugin Compose.

```bash
docker compose up --build
```

La aplicación queda disponible en **http://localhost:8080**.

- En el primer arranque, `entrypoint.sh` ejecuta `seed_data.py` automáticamente porque la base de datos no existe; en los siguientes arranques la reutiliza.
- Los datos persisten en volúmenes de Docker: `data` (SQLite en `/app/data`) y `uploads` (imágenes en `/app/uploads`). No se pierden al reiniciar ni al recrear el contenedor.
- Variables de entorno (ver `docker-compose.yml`): `VINTO_DB_URL`, `VINTO_UPLOADS` y `STORAGE_SECRET` (cámbielo en producción).
- Para borrar también los datos: `docker compose down -v`.
- Para volver a sembrar la base: `docker compose run --rm --entrypoint python web seed_data.py --reset`.

## Instalación local (sin Docker)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python seed_data.py              # crea la base con datos de ejemplo
python main.py                   # abre http://localhost:8080
```

- Para recrear los datos desde cero: `python seed_data.py --reset`
- El puerto queda fijo en `8080` (configurable editando `ui.run` en `main.py`).
- El mapa usa teselas de OpenStreetMap, por lo que requiere conexión a internet.
- En producción, defina `STORAGE_SECRET` (secreto de la sesión) como variable de entorno.
- Las rutas de la base y de las imágenes se leen de `VINTO_DB_URL` y `VINTO_UPLOADS`.


## Pruebas

```bash
pytest
```

Las pruebas usan repositorios y almacenamiento en memoria (`tests/fakes.py`), sin tocar la base real.

## Usuarios de prueba

| Rol           | Correo                     | Contraseña   |
|---------------|----------------------------|--------------|
| Administrador | admin@vinto.gob.bo         | Admin123!    |
| Funcionario   | funcionario@vinto.gob.bo   | Func123!     |
| Vecino        | vecino@vinto.gob.bo        | Vecino123!   |

## Permisos por rol (RBAC)

| Funcionalidad                          | Vecino | Funcionario | Admin |
|----------------------------------------|:------:|:-----------:|:-----:|
| Mapa público                           |   ✔    |      ✔      |   ✔   |
| Registrar incidentes                   |   ✔    |      ✔      |   ✔   |
| Ver incidentes                         | solo propios | todos | todos |
| Cambiar estado / asignar responsable   |        |      ✔      |   ✔   |
| Dashboard                              |        |      ✔      |   ✔   |
| Gestión de usuarios y cuadrillas       |        |             |   ✔   |

Los permisos se verifican en la UI (`exigir_pagina`) **y** dentro de cada caso de uso (`domain/permisos.py`).

## Estructura

```
domain/          entidades, objetos de valor, reglas, factory, puertos
application/     casos de uso
infrastructure/  SQLModel/SQLite, imágenes en disco, bcrypt, geolocalización
ui/              layout, adaptador de mapa, páginas NiceGUI
composition_root.py   inyección de dependencias manual
main.py          solo arranca la app
seed_data.py     datos de ejemplo
tests/           suite PyTest
```

## Notas

- Las coordenadas de las zonas de Vinto (`domain/zonas.py`) son **referenciales/aproximadas**; ajústelas
  con datos oficiales del municipio si se requiere precisión.
- Las fotos se guardan en `uploads/` y se sirven en `/uploads/...`.
- El tiempo medio de respuesta se calcula como REPORTADO → EN_ATENCION a partir del historial de estados.
