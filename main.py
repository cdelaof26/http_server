from util import utilidades, config
from typing import Optional
import logging
import socket


BUFFER_SIZE = 1024


def setup_server(_host = None, _puerto = None, _usuarios = None) -> Optional[dict[str, any]]:
    try:
        if _host is None:
            _host = utilidades.seleccionar_ip("  Server Setup\nSelecciona la IP host")

        if _puerto is None:
            _puerto = utilidades.obtener_puerto()

        if _usuarios is None:
            _usuarios = utilidades.obtener_numero_natural("Ingresa el número de usuarios máximos", 1)
    except KeyboardInterrupt:
        return None

    logging.info("Levantando servidor...")
    _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _server_socket.bind((_host, _puerto))  # No debería arrojar error a menos que se definan los parámetros en código
    _server_socket.listen(_usuarios)

    return {"host": _host, "puerto": _puerto, "usuarios": _usuarios, "socket": _server_socket}


def aceptar_peticiones(_datos: dict[str, any]):
    global BUFFER_SIZE
    server_socket: socket.socket = _datos["socket"]

    while True:
        cliente, ip_puerto = server_socket.accept()
        logging.info(f"Se ha conectado el cliente {ip_puerto}")

        solicitud = cliente.recv(BUFFER_SIZE).decode()
        logging.info(f"Petición recibida: {solicitud}")

        respuesta = "HTTP/1.1 200 OK\r\n\r\nHola Mundo"
        cliente.send(respuesta.encode())

        cliente.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if not config.cargar_rutas():
        logging.critical("  Ocurrió un error al procesar la linea anterior")
        exit(1)

    # datos = setup_server("localhost", 80, 10)  # Debug
    datos = setup_server()
    if not datos:
        print()
        logging.critical("No se han proporcionado todos los datos requeridos!")
        exit(1)

    utilidades.limpiar_pantalla()
    logging.info(f"Servidor en escuchando en {datos['host']}:{datos['puerto']}")
    logging.info(f"Se ha definido {datos['usuarios']} como cantidad de usuarios máximo")
    try:
        aceptar_peticiones(datos)
    except KeyboardInterrupt:
        logging.warning("Cerrando servidor...")
        datos["socket"].close()
