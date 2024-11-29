from util import utilidades, config, http_utils
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
    except AssertionError:
        logging.critical("Este programa requiere de 'ipconfig', 'ifconfig' o 'ip' instalado y configurado en PATH")
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

        try:
            # Parece que no se recomienda utilizar Unicode (UTF-8)
            # como interpretación por defecto para los mensajes en HTTP/1.1,
            # pero manejar los mensajes como flujo de bytes complicaría las cosas...
            _solicitud = cliente.recv(BUFFER_SIZE).decode()
        except UnicodeError:
            # Es posible que el usuario envie un archivo binario que no pueda decodificado como UTF-8
            cliente.close()
            continue

        solicitud = http_utils.procesar_solicitud(_solicitud)
        respuesta = http_utils.crear_respuesta(solicitud)

        logging.info(f"Petición recibida: {_solicitud}")
        logging.info(f"Petición procesada: {solicitud}")
        logging.info(f"Respuesta: {respuesta}")

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
