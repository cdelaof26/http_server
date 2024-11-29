from util.config import HTTPMethod, ROUTES
from datetime import datetime
from enum import Enum
import re


PAGE_TITLE = "PAGE_TITLE"
BODY_DATA = "BODY_DATA"
BASE_HTML = f"""<!DOCTYPE HTML>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{PAGE_TITLE}</title>
</head>
<body>
{BODY_DATA}
</body>
</html>
"""


class HTTPStatusCode(Enum):
    c200 = 0  # OK: The request was successful.
    c400 = 1  # Bad Request: The request was invalid or cannot be processed.
    c404 = 2  # Not Found: The requested resource was not found.
    c500 = 3  # Internal Server Error: An internal error occurred while processing the request.
    c501 = 4  # Not Implemented: The requested method is not supported by the server.
    c503 = 5  # Service Unavailable: The server is currently unavailable or overloaded.
    c201 = 6  # Created: The request was successful and a new resource was created.
    c204 = 7  # No Content: The request was successful, but there is no content to return.
    c301 = 8  # Moved Permanently: The requested resource has been permanently moved to a new location.
    c302 = 9  # Found: The requested resource has been temporarily moved to a new location.


def status_code_as_int(code: HTTPStatusCode) -> str:
    return code.name.replace("c", "")


class _HTTPStatusMessage(Enum):
    OK = 0
    BAD_REQUEST = 1
    NOT_FOUND = 2
    INTERNAL_SERVER_ERROR = 3
    NOT_IMPLEMENTED = 4
    SERVICE_UNAVAILABLE = 5
    CREATED = 6
    NO_CONTENT = 7
    MOVED_PERMANENTLY = 8
    FOUND = 9


def status_code_as_msg(code: HTTPStatusCode) -> str:
    mensaje = _HTTPStatusMessage(code.value).name
    if "_" not in mensaje:
        return mensaje

    mensaje = " ".join([m.capitalize() for m in mensaje.split("_")])
    return mensaje


class HTTPRequestData(Enum):
    STATUS = 0
    URI = 1
    METHOD = 2
    PROTOCOL = 3
    QUERY = 4
    PATH = 5
    HEADERS = 6
    BODY = 7
    ERROR = 8


class HTTPConnection(Enum):
    # Puede tomar más valores como 'upgrade', 'HTTP/X', 'no-transform', 'no-cache' o 'no-store'
    # Pero no se implementan
    KEEP_ALIVE = 0
    CLOSE = 1


def separar_mensaje(solicitud: str) -> tuple[str, str]:
    request_line = re.sub(r"\r\n[\w\W]+", "", solicitud)
    headers = solicitud.replace(request_line, "")
    return request_line.replace("\r\n", ""), headers


def uri_valida(uri: str) -> bool:
    # Las URI pueden contener "_.?&/=" y letras/números
    return re.sub(r"/[\w_.&?/=]*", "", uri) == ""


def separar_query_params(request: dict):
    if HTTPRequestData.URI not in request:
        return

    uri: str = request[HTTPRequestData.URI]
    question_marks = uri.count("?")
    if question_marks == 0 and "&" not in uri and "=" not in uri:
        request[HTTPRequestData.PATH] = uri
        return

    if question_marks > 1 or question_marks == 0 and ("&" in uri or "=" in uri):
        # No puede haber más de un '?' o algún '&'/'=' y no '?'
        request[HTTPRequestData.STATUS] = HTTPStatusCode.c400
        request[HTTPRequestData.ERROR] = "Malformed query"
        return

    ruta, _query_params = uri.split("?")
    request[HTTPRequestData.PATH] = ruta

    query_params = dict()
    for query in _query_params.split("&"):
        if query.count("=") != 1:
            request[HTTPRequestData.STATUS] = HTTPStatusCode.c400
            request[HTTPRequestData.ERROR] = "Malformed query"
            return
        key, valor = query.split("=")
        query_params[key] = valor

    request[HTTPRequestData.QUERY] = query_params


def procesar_request_line(request_line: str) -> dict:
    # De acuerdo con el documento del HTTP/1.1, las líneas request_line con las que inician las solicitudes
    # llevan un formato como el siguiente:
    #     PUT /users/ HTTP/1.1
    #     MÉTODO URI PROTOCOLO
    # La URI puede incluir parámetros de query:
    #    DELETE /users?data=0192 HTTP/1.1
    datos = dict()
    if request_line.count(" ") != 2:
        datos[HTTPRequestData.STATUS] = HTTPStatusCode.c400
        datos[HTTPRequestData.ERROR] = "Malformed request line"
        return datos

    metodo, uri, protocolo = request_line.split(" ")
    m = None
    try:
        m = HTTPMethod[metodo]
        metodo_invalido = False
    except KeyError:
        metodo_invalido = True
    no_es_http11 = protocolo != "HTTP/1.1"
    uri_invalida = not uri_valida(uri)

    if metodo_invalido or no_es_http11 or uri_invalida:
        datos[HTTPRequestData.STATUS] = HTTPStatusCode.c501 if metodo_invalido \
            else HTTPStatusCode.c400 if no_es_http11 else HTTPStatusCode.c404
        datos[HTTPRequestData.ERROR] = "Method not implemented" if metodo_invalido \
            else "Unsupported protocol" if no_es_http11 else "Resource not found"

        return datos

    datos[HTTPRequestData.STATUS] = HTTPStatusCode.c200
    datos[HTTPRequestData.METHOD] = m
    datos[HTTPRequestData.URI] = uri
    datos[HTTPRequestData.PROTOCOL] = protocolo

    return datos


def parse_headers(str_headers: str, response: dict):
    headers = dict()

    # Para simplificar la implementación, solo se soporta un Content-Type por solicitud
    boundary = ""
    str_headers = str_headers.replace("\r\n\r\n", "\r\n--data--\r\n", 1)
    lineas = str_headers.split("\r\n")
    while "" in lineas:
        lineas.remove("")

    i = 0

    for i, linea in enumerate(lineas):
        if linea == boundary or linea == "--data--":
            break

        if "boundary=--" in linea:
            boundary = re.findall(r"-+\d+", linea)[0]
            linea = linea.replace(f"; boundary={boundary}", "")
            boundary = re.sub("-+", "", boundary)

        key, valor = linea.split(": ")
        if key == "Content-Type" and key in headers:
            response[HTTPRequestData.STATUS] = HTTPStatusCode.c400
            response[HTTPRequestData.ERROR] = "Multiple definitions of Content-Type are not allowed"

        headers[key] = valor

    i += 1
    if "Content-Length" in headers:
        body = "\n".join(lineas[i:])
        response[HTTPRequestData.BODY] = re.sub("-+" + boundary + "-?-?", "", body) if boundary else body

    response[HTTPRequestData.HEADERS] = headers


def procesar_solicitud(solicitud: str) -> dict:
    request_line, headers = separar_mensaje(solicitud)
    response = procesar_request_line(request_line)
    separar_query_params(response)
    parse_headers(headers, response)

    return response


def obtener_fecha() -> str:
    return datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")


def generar_html(status: str, solicitud: dict) -> str:
    global BASE_HTML, PAGE_TITLE, BODY_DATA

    html = BASE_HTML
    html = re.sub(PAGE_TITLE, "Error" if status != "200" else "Página", html)

    titulo = solicitud[HTTPRequestData.ERROR] if HTTPRequestData.ERROR in solicitud else "Hola Mundo"
    cuerpo = f"<h1>{titulo} - {status} {'OK' if status == HTTPStatusCode.c200 else ''}</h1>\n"

    if HTTPRequestData.PATH in solicitud:
        cuerpo += f"<b><p>Página para la ruta {solicitud[HTTPRequestData.PATH]}</p></b>\n"
    if HTTPRequestData.METHOD in solicitud:
        cuerpo += f"<p>Método: {solicitud[HTTPRequestData.METHOD].name}</p>\n"
    if HTTPRequestData.QUERY in solicitud:
        cuerpo += f"<p>Datos de query: {solicitud[HTTPRequestData.QUERY]}</p>\n"
    if HTTPRequestData.BODY in solicitud:
        cuerpo += f"<p>Body: {solicitud[HTTPRequestData.BODY]}</p>\n"

    return re.sub(BODY_DATA, cuerpo, html)


def verificar_ruta(solicitud: dict):
    if solicitud[HTTPRequestData.STATUS] != HTTPStatusCode.c200 or HTTPRequestData.PATH not in solicitud:
        return

    ruta: str = solicitud[HTTPRequestData.PATH]
    if ruta[-1] != "/":
        ruta += "/"

    if ruta not in ROUTES:
        ruta = ruta[:-1]
        if ruta not in ROUTES:
            solicitud[HTTPRequestData.STATUS] = HTTPStatusCode.c404
            solicitud[HTTPRequestData.ERROR] = "Resource not found"
            return

    if solicitud[HTTPRequestData.METHOD] not in ROUTES[ruta]:
        solicitud[HTTPRequestData.STATUS] = HTTPStatusCode.c501
        solicitud[HTTPRequestData.ERROR] = "Method not implemented"


INTERNAL_ERROR = {
    HTTPRequestData.STATUS: HTTPStatusCode.c500,
    HTTPRequestData.ERROR: "An internal error occurred while processing the request"
}


def crear_respuesta(solicitud: dict) -> str:
    verificar_ruta(solicitud)

    respuesta = ""

    estado = solicitud[HTTPRequestData.STATUS]
    status = status_code_as_int(estado)
    status_msg = status_code_as_msg(estado)

    cuerpo = generar_html(status, solicitud)

    respuesta += f"HTTP/1.1 {status} {status_msg}\r\n"
    respuesta += f"Server: Python3 http_server\r\n"
    respuesta += f"Date: {obtener_fecha()}\r\n"
    respuesta += f"Content-type: text/html; charset=utf-8\r\n\r\n"

    # Por alguna razón Postman tiene problemas procesando la respuesta con Content-Length
    # respuesta += f"Content-Length: {len(cuerpo)}\r\n\r\n"
    respuesta += cuerpo
    # HTML es una posible respuesta, pero con la única con la que se responde
    # independientemente del MIME (Accept) que indica el cliente; TODO: Implementar

    return respuesta


def estado_de_conexion(solicitud: dict) -> HTTPConnection:
    # Por defecto se cierra la conexión si no existen los headers
    if HTTPRequestData.HEADERS not in solicitud:
        return HTTPConnection.CLOSE

    headers = solicitud[HTTPRequestData.HEADERS]
    conexion: str = headers["Connection"].replace("-", "_").upper()
    try:
        return HTTPConnection[conexion]
    except KeyError:
        return HTTPConnection.CLOSE
