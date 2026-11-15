"""Registro de incidentes (RF-01 a RF-04)."""
from __future__ import annotations

import base64
from datetime import datetime

from nicegui import ui

from application.incidentes import DatosIncidente
from composition_root import Contenedor
from domain.errors import ValidacionError
from domain.permisos import Permiso
from domain.reglas_imagen import EXTENSIONES_PERMITIDAS, TAMANO_MAXIMO_BYTES, validar_imagen
from domain.value_objects import Categoria
from ui.comun import seguro
from ui.layout import marco
from ui.mapa_adapter import LeafletMapaAdapter
from ui.sesion import exigir_pagina

_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def registrar(c: Contenedor) -> None:
    @ui.page("/incidentes/nuevo")
    def nuevo() -> None:
        usuario = exigir_pagina(c, Permiso.REGISTRAR_INCIDENTE)
        if not usuario:
            return
        centro = c.geo.centro_inicial()
        imagen = {"nombre": None, "contenido": None}

        with marco(c, usuario, "Reportar incidente", "Complete el formulario y marque la ubicación en el mapa"):
            with ui.row().classes("w-full gap-4 items-start no-wrap max-md:flex-wrap"):
                with ui.card().classes("tarjeta q-pa-md gap-3 grow basis-1/2 w-full"):
                    categoria = ui.select({cat.value: cat.etiqueta for cat in Categoria}, label="Categoría *") \
                        .props("outlined").classes("w-full")
                    descripcion = ui.textarea("Descripción *").props("outlined counter maxlength=1000").classes("w-full")
                    referencia = ui.input("Referencias del lugar (ej. frente a la escuela, río Rocha)") \
                        .props("outlined").classes("w-full")
                    fecha = ui.input("Fecha y hora del incidente *", value=datetime.now().strftime("%Y-%m-%dT%H:%M")) \
                        .props("outlined type=datetime-local").classes("w-full")
                    ui.label("Evidencia fotográfica (JPG, PNG o WEBP, máx. 5 MB)").classes("text-sm text-gray-600")

                    miniatura = ui.image().classes("w-48 rounded").set_visibility(False)

                    async def al_subir(e) -> None:
                        try:
                            nombre = e.file.name
                            contenido = await e.file.read()
                            ext = validar_imagen(nombre, contenido)
                        except ValidacionError as exc:
                            ui.notify(str(exc), type="warning")
                            subida.reset()
                            return
                        except Exception:  # noqa: BLE001
                            ui.notify("No se pudo leer el archivo.", type="negative")
                            subida.reset()
                            return
                        imagen["nombre"], imagen["contenido"] = nombre, contenido
                        b64 = base64.b64encode(contenido).decode()
                        miniatura.set_source(f"data:{_MIME[ext]};base64,{b64}")
                        miniatura.set_visibility(True)
                        ui.notify("Imagen cargada.", type="positive")

                    def al_rechazar() -> None:
                        ui.notify("Archivo rechazado: use JPG, PNG o WEBP de hasta 5 MB.", type="warning")

                    subida = ui.upload(on_upload=al_subir, on_rejected=al_rechazar, auto_upload=True,
                                       max_file_size=TAMANO_MAXIMO_BYTES, label="Seleccionar imagen") \
                        .props(f'accept="{",".join(sorted(EXTENSIONES_PERMITIDAS))}" flat bordered').classes("w-full")

                    def quitar() -> None:
                        imagen["nombre"] = imagen["contenido"] = None
                        miniatura.set_visibility(False)
                        subida.reset()

                    ui.button("Quitar imagen", icon="delete", on_click=quitar).props("flat dense no-caps color=negative")

                with ui.card().classes("tarjeta q-pa-md gap-3 grow basis-1/2 w-full"):
                    ui.label("Ubicación *").classes("font-bold")
                    ui.label("Haga clic en el mapa para fijar el punto o edite las coordenadas.").classes("text-sm text-gray-600")
                    mapa = LeafletMapaAdapter((centro.latitud, centro.longitud), zoom=13)
                    mapa.dibujar("w-full h-80")
                    with ui.row().classes("w-full no-wrap"):
                        lat = ui.number("Latitud", value=None, format="%.6f", step=0.0001).props("outlined dense").classes("w-1/2")
                        lon = ui.number("Longitud", value=None, format="%.6f", step=0.0001).props("outlined dense").classes("w-1/2")

                    def clic(la: float, lo: float) -> None:
                        lat.set_value(round(la, 6))
                        lon.set_value(round(lo, 6))

                    def coordenadas_editadas() -> None:
                        if lat.value is not None and lon.value is not None and -90 <= lat.value <= 90 \
                                and -180 <= lon.value <= 180:
                            mapa.fijar_punto(lat.value, lon.value, centrar=True)

                    mapa.al_hacer_clic(clic)
                    lat.on_value_change(coordenadas_editadas)
                    lon.on_value_change(coordenadas_editadas)

            def enviar() -> None:
                try:
                    f = datetime.fromisoformat(fecha.value) if fecha.value else None
                except ValueError:
                    ui.notify("La fecha y hora no tienen un formato válido.", type="warning")
                    return
                datos = DatosIncidente(
                    categoria=categoria.value, descripcion=descripcion.value, latitud=lat.value,
                    longitud=lon.value, referencia=referencia.value, fecha_hora=f,
                    imagen_nombre=imagen["nombre"], imagen_contenido=imagen["contenido"])
                incidente = seguro(lambda: c.registrar_incidente.ejecutar(usuario, datos),
                                   "Incidente registrado correctamente.")
                if incidente:
                    ui.navigate.to(f"/incidentes/{incidente.id}")

            ui.button("Enviar reporte", icon="send", on_click=enviar).classes("self-end")
