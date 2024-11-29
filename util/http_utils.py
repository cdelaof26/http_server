from enum import Enum
import re


class HTTPMethod(Enum):
    GET = 1
    POST = 2
    PUT = 3
    PATCH = 4
    DELETE = 5


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


def status_code_to_status_message(code: HTTPStatusCode) -> str:
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
    try:
        _ = HTTPMethod[metodo]
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
    datos[HTTPRequestData.METHOD] = metodo
    datos[HTTPRequestData.URI] = uri
    datos[HTTPRequestData.PROTOCOL] = protocolo

    return datos


def parse_headers(str_headers: str, response: dict):
    headers = dict()

    # Para simplificar la implementación, solo se soporta un Content-Type por solicitud
    boundary = ""
    lineas = str_headers.split("\r\n")
    while "" in lineas:
        lineas.remove("")

    i = 0

    for i, linea in enumerate(lineas):
        if linea == boundary:
            break

        if "boundary" in linea:
            boundary = re.findall(r"-+\d+", linea)[0]
            linea = linea.replace(f"; boundary={boundary}", "")

        key, valor = linea.split(": ")
        if key == "Content-Type" and key in headers:
            response[HTTPRequestData.STATUS] = HTTPStatusCode.c400
            response[HTTPRequestData.ERROR] = "Redefinition of Content-Type is not allowed"

        headers[key] = valor
        if key == "Content-Length":
            break

    i += 1
    if "Content-Length" in headers:
        body = "\n".join(lineas[i:])
        response[HTTPRequestData.BODY] = re.sub(boundary, "", body) if boundary else body

    response[HTTPRequestData.HEADERS] = headers


def procesar_solicitud(solicitud: str) -> dict:
    request_line, headers = separar_mensaje(solicitud)
    response = procesar_request_line(request_line)
    separar_query_params(response)
    parse_headers(headers, response)

    return response
