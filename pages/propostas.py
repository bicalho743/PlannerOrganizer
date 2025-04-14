import reflex as rx

def propostas():
    return rx.center(
        rx.vstack(
            rx.heading("Propostas", size="8"),
            rx.text("Bem-vindo à página de propostas."),
        ),
        height="100vh"
    )

page = rx.page(route="/propostas")(propostas)