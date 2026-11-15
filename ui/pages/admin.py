"""Gestión de usuarios y cuadrillas (solo administrador)."""
from nicegui import ui

from composition_root import Contenedor
from domain.permisos import Permiso
from domain.value_objects import Rol
from ui.comun import seguro
from ui.layout import marco
from ui.sesion import exigir_pagina


def registrar(c: Contenedor) -> None:
    @ui.page("/admin/usuarios")
    def usuarios() -> None:
        admin = exigir_pagina(c, Permiso.GESTIONAR_USUARIOS)
        if not admin:
            return
        with marco(c, admin, "Gestión de usuarios", "Cree usuarios, cambie roles o desactive cuentas"):
            with ui.card().classes("tarjeta q-pa-md w-full"):
                ui.label("Nuevo usuario").classes("font-bold")
                with ui.row().classes("w-full items-end gap-3"):
                    nombre = ui.input("Nombre").props("outlined dense")
                    email = ui.input("Correo").props("outlined dense type=email")
                    clave = ui.input("Contraseña", password=True, password_toggle_button=True).props("outlined dense")
                    rol = ui.select({r.value: r.etiqueta for r in Rol}, value=Rol.FUNCIONARIO.value, label="Rol") \
                        .props("outlined dense").classes("min-w-[160px]")

                    def crear() -> None:
                        u = seguro(lambda: c.registrar_usuario.ejecutar(nombre.value, email.value, clave.value,
                                                                        Rol(rol.value), actor=admin),
                                   "Usuario creado correctamente.")
                        if u:
                            nombre.set_value("")
                            email.set_value("")
                            clave.set_value("")
                            lista.refresh()
                    ui.button("Crear", icon="person_add", on_click=crear)

            @ui.refreshable
            def lista() -> None:
                todos = seguro(lambda: c.usuarios.listar(admin)) or []
                with ui.card().classes("tarjeta q-pa-md w-full gap-2"):
                    for u in todos:
                        with ui.row().classes("w-full items-center justify-between gap-3 border-b q-pb-sm"):
                            with ui.column().classes("gap-0 min-w-[200px]"):
                                ui.label(u.nombre).classes("font-bold")
                                ui.label(u.email).classes("text-sm text-gray-600")
                            with ui.row().classes("items-center gap-3"):
                                def cambiar_rol(e, uid=u.id) -> None:
                                    if seguro(lambda: c.usuarios.cambiar_rol(admin, uid, Rol(e.value)), "Rol actualizado."):
                                        return
                                    lista.refresh()

                                def cambiar_activo(e, uid=u.id) -> None:
                                    if seguro(lambda: c.usuarios.cambiar_activo(admin, uid, e.value),
                                              "Estado de la cuenta actualizado."):
                                        return
                                    lista.refresh()
                                ui.select({r.value: r.etiqueta for r in Rol}, value=u.rol.value,
                                          on_change=cambiar_rol).props("outlined dense").classes("min-w-[150px]")
                                ui.switch("Activo", value=u.activo, on_change=cambiar_activo)
            lista()

    @ui.page("/admin/cuadrillas")
    def cuadrillas() -> None:
        admin = exigir_pagina(c, Permiso.GESTIONAR_CUADRILLAS)
        if not admin:
            return
        with marco(c, admin, "Gestión de cuadrillas", "Equipos disponibles para atender incidentes"):
            with ui.card().classes("tarjeta q-pa-md w-full"):
                ui.label("Nueva cuadrilla").classes("font-bold")
                with ui.row().classes("w-full items-end gap-3"):
                    nombre = ui.input("Nombre de la cuadrilla").props("outlined dense")
                    resp = ui.input("Responsable").props("outlined dense")

                    def crear() -> None:
                        if seguro(lambda: c.cuadrillas.crear(admin, nombre.value, resp.value), "Cuadrilla creada."):
                            nombre.set_value("")
                            resp.set_value("")
                            lista.refresh()
                    ui.button("Crear", icon="add", on_click=crear)

            @ui.refreshable
            def lista() -> None:
                todas = seguro(lambda: c.cuadrillas.listar(admin)) or []
                with ui.card().classes("tarjeta q-pa-md w-full gap-2"):
                    if not todas:
                        ui.label("No hay cuadrillas registradas.").classes("text-gray-600")
                    for q in todas:
                        with ui.row().classes("w-full items-center justify-between border-b q-pb-sm"):
                            with ui.column().classes("gap-0"):
                                ui.label(q.nombre).classes("font-bold")
                                ui.label(f"Responsable: {q.responsable}").classes("text-sm text-gray-600")

                            def cambiar(e, qid=q.id) -> None:
                                if seguro(lambda: c.cuadrillas.cambiar_activa(admin, qid, e.value), "Cuadrilla actualizada."):
                                    return
                                lista.refresh()
                            ui.switch("Activa", value=q.activa, on_change=cambiar)
            lista()
