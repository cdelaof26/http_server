# Utilidades varias

from util import net_utils, config
from typing import Optional
import subprocess
import socket
import re


CANCELAR = "\n  Presiona enter para continuar y control + c para cancelar "


def limpiar_pantalla():
    subprocess.call("cls" if config.PLATAFORMA == "nt" else "clear")


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


def seleccionar(opciones: list[str], valores: Optional[list] = None):
    seleccion = ""
    while not seleccion:
        seleccion = input("> ").upper()
        if seleccion not in opciones:
            input(f"El valor ingresado no es válido {CANCELAR}")
            seleccion = ""

    if valores is not None:
        return valores[opciones.index(seleccion)]
    return seleccion


def seleccionar_ip(info: str = "Selecciona la IP host") -> str:
    ip = net_utils.obtener_ip()
    opciones = []

    print(info)
    for _, _ip in zip(range(len(ip)), ip):
        op = f"{_ + 1}"
        print(f"{op}. {_ip}")
        opciones.append(op)

    return seleccionar(opciones, ip)


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


def presentar_dict(datos: dict) -> str:
    _datos = str(datos)
    for f in re.findall(r"\W, ", _datos):
        _datos = re.sub(f, f.replace(" ", "\n"), _datos, 1)

    _datos = _datos.replace("{", "{\n")
    _datos = _datos.replace("}", "\n}")
    _dict = ""
    _indent = "    "
    indent = 0
    for linea in _datos.split("\n"):
        if linea == "{":
            indent += 1
            _dict += linea + "\n"
            continue

        if linea == "}":
            indent -= 1
            _dict += f"{_indent * indent}{linea}\n"
            continue

        if ": {" in linea:
            _dict += f"{_indent * indent}{linea}\n"
            indent += 1
            continue

        _dict += f"{_indent * indent}{linea}\n"

    return _dict
