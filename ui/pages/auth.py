"""Páginas de login y registro."""
from nicegui import ui

from composition_root import Contenedor
from ui.comun import seguro
from ui.layout import marco
from ui.sesion import iniciar_sesion, usuario_actual


def registrar(c: Contenedor) -> None:
    @ui.page("/login")
    def login() -> None:
        if usuario_actual(c):
            ui.navigate.to("/")
            return
        with marco(c, None, "Ingresar", "Sistema de reporte de incidentes medio ambientales"):
            with ui.card().classes("tarjeta w-full max-w-md mx-auto q-pa-lg gap-3"):
                email = ui.input("Correo electrónico").props("outlined type=email autofocus").classes("w-full")
                clave = ui.input("Contraseña", password=True, password_toggle_button=True).props("outlined").classes("w-full")

                def entrar() -> None:
                    usuario = seguro(lambda: c.autenticar.ejecutar(email.value, clave.value))
                    if usuario:
                        iniciar_sesion(usuario)
                        ui.notify(f"Bienvenido/a, {usuario.nombre}", type="positive")
                        ui.navigate.to("/")

                clave.on("keydown.enter", entrar)
                ui.button("Ingresar", icon="login", on_click=entrar).classes("w-full")
                ui.link("¿No tiene cuenta? Regístrese", "/registro")

    @ui.page("/registro")
    def registro() -> None:
        if usuario_actual(c):
            ui.navigate.to("/")
            return
        with marco(c, None, "Crear cuenta", "Las cuentas nuevas tienen el rol de Vecino"):
            with ui.card().classes("tarjeta w-full max-w-md mx-auto q-pa-lg gap-3"):
                nombre = ui.input("Nombre completo").props("outlined").classes("w-full")
                email = ui.input("Correo electrónico").props("outlined type=email").classes("w-full")
                clave = ui.input("Contraseña (mínimo 8 caracteres)", password=True,
                                 password_toggle_button=True).props("outlined").classes("w-full")
                clave2 = ui.input("Repita la contraseña", password=True).props("outlined").classes("w-full")

                def crear() -> None:
                    if clave.value != clave2.value:
                        ui.notify("Las contraseñas no coinciden.", type="warning")
                        return
                    usuario = seguro(lambda: c.registrar_usuario.ejecutar(nombre.value, email.value, clave.value))
                    if usuario:
                        iniciar_sesion(usuario)
                        ui.notify("Cuenta creada correctamente.", type="positive")
                        ui.navigate.to("/")

                ui.button("Registrarme", icon="person_add", on_click=crear).classes("w-full")
                ui.link("¿Ya tiene cuenta? Ingrese", "/login")
