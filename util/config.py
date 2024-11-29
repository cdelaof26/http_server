# Utilidades para leer los archivos de configuración

from util.http_utils import HTTPMethod
from pathlib import Path
import logging
import re

try:
    from os import uname
    PLATAFORMA = uname()[0].lower()  # macOS: darwin
except ImportError:
    PLATAFORMA = "nt"

# El archivo de configuración, donde se definen que rutas existen y que métodos aceptan, tiene la siguiente estructura:
#
#   /ruta/completa/ GET, PUT, PATCH
#
# Cualquier cadena después de '#' se tomará como comentario
ROUTES_CONFIG_FILE = Path("route_config")
DEFAULTS = """# Archivo de configuración de http_server
#     Métodos admitidos: GET, POST, PUT, PATCH, DELETE
#     Para agregar una nueva ruta utiliza: /ruta/completa/ MÉTODOS_ADMITIDOS
#     Por ejemplo: /usuarios/ GET, DELETE 

/ GET
"""
ROUTES: dict[str, list[HTTPMethod]] = {"/": [HTTPMethod.GET]}


def ruta_valida(ruta: str) -> bool:
    return re.sub(r"/[\w/_]*/?", "", ruta) == ""


def convertir_metodos(_metodos: str) -> list:
    metodos = []
    _metodos = _metodos.replace(" ", "")
    for metodo in _metodos.split(","):
        try:
            metodos.append(HTTPMethod[metodo])
        except KeyError:
            return []

    return metodos


def cargar_rutas() -> bool:
    global ROUTES_CONFIG_FILE
    if not ROUTES_CONFIG_FILE.exists():
        with open(ROUTES_CONFIG_FILE, "w") as fichero:
            fichero.write(DEFAULTS)
        return True

    logging.warning("Importando rutas definidas en archivo de configuración...")

    with open(ROUTES_CONFIG_FILE, "r") as fichero:
        datos = fichero.read()

    datos = re.sub("#.+", "", datos)  # Elimina los comentarios
    lineas = datos.split("\n")
    for linea in lineas:
        if not linea:
            continue

        logging.info(f"Procesando linea %a" % linea)
        _metodos = re.sub("^.*?(?= )", "", linea)
        ruta = linea.replace(_metodos, "")
        metodos = convertir_metodos(_metodos)

        try:
            assert ruta_valida(ruta)
            assert len(metodos) != 0
        except AssertionError:
            return False

        ROUTES[ruta] = metodos

    return True
