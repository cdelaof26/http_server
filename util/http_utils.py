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
        return

    ruta, _query_params = uri.split("?")
    request[HTTPRequestData.PATH] = ruta

    query_params = dict()
    for query in _query_params.split("&"):
        if query.count("=") != 1:
            request[HTTPRequestData.STATUS] = HTTPStatusCode.c400
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
        return datos

    metodo, uri, protocolo = request_line.split(" ")
    try:
        _ = HTTPMethod[metodo]
        metodo_valido = True
    except KeyError:
        metodo_valido = False

    if not metodo_valido or protocolo != "HTTP/1.1" or not uri_valida(uri):
        datos[HTTPRequestData.STATUS] = HTTPStatusCode.c400
        return datos

    datos[HTTPRequestData.STATUS] = HTTPStatusCode.c200
    datos[HTTPRequestData.METHOD] = metodo
    datos[HTTPRequestData.URI] = uri
    datos[HTTPRequestData.PROTOCOL] = protocolo

    return datos


def procesar_solicitud(solicitud: str) -> dict:
    request_line, headers = separar_mensaje(solicitud)
    response = procesar_request_line(request_line)
    separar_query_params(response)

    return response
