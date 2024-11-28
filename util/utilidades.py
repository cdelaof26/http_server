# Utilidades varias

import subprocess
import socket
import re


CANCELAR = "\n  Presiona enter para continuar y control + c para cancelar "
try:
    from os import uname
    PLATAFORMA = uname()[0].lower()  # macOS: darwin
except ImportError:
    PLATAFORMA = "nt"


def limpiar_pantalla():
    global PLATAFORMA
    subprocess.call("cls" if PLATAFORMA == "nt" else "clear")


def validar_puerto(puerto: int) -> str:
    valido = 1 <= puerto <= 65535
    if not valido:
        return "Dato fuera del rango [1, 65535]"

    _socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _socket.bind(("localhost", puerto))
        return ""
    except PermissionError:
        return f"El puerto {puerto} requiere permisos de administrador para ser utilizado"
    except OSError:
        return f"El puerto {puerto} ya esta en uso"
    finally:
        _socket.close()


def obtener_puerto(info: str = "Ingresa el puerto") -> int:
    _puerto = ""
    while not _puerto:
        limpiar_pantalla()
        print(info)
        _puerto = input("> ")
        if re.sub(r"\d+", "", _puerto):
            input(f"El dato ingresado no es un número {CANCELAR}")
            _puerto = ""
            continue

        puerto = int(_puerto)
        estado = validar_puerto(puerto)
        if estado:
            input(estado + CANCELAR)
            _puerto = ""
            continue

        return puerto


def obtener_numero_natural(info: str, limite_inferior: int = 0, limite_superior: int = -1) -> int:
    assert limite_inferior >= 0 and (limite_superior == -1 or limite_superior >= limite_inferior)

    _numero = ""
    while not _numero:
        limpiar_pantalla()
        print(info)
        _numero = input("> ")
        if re.sub(r"\d+", "", _numero):
            input(f"El dato ingresado no es un número {CANCELAR}")
            _numero = ""
            continue

        numero = int(_numero)
        if limite_superior == -1 and numero >= limite_inferior:
            return numero
        if limite_inferior <= numero <= limite_superior:
            return numero

        input(f"Dato fuera del rango [{limite_inferior}, {limite_superior if limite_superior != -1 else 'inf'}] "
              f"{CANCELAR}")
        _numero = ""
