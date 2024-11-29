# http server

Pequeña implementación de un servidor HTTP 1.1


### Dependencias
- Se requiere de Python 3.9 o versiones posteriores


### Uso
Para ejecutar el programa:

<pre>
# Ingresar al directorio del proyecto 
$ cd http_server

# Ejecutar el programa
$ python3 main.py

# Ejecutar el servidor (Microsoft Windows)
$ python main.py
</pre>

Para realizar pruebas se utilizó [Postman](https://www.postman.com/).

### Historial de versiones

#### v0.0.5
- Preprocesamiento de la petición _terminada_
  - Se hace conversión del mensaje completo a UTF-8
  - Es posible seguir procesando el cuerpo de la solicitud
  - No se valida el tamaño del cuerpo con lo reportado por el 
    cliente
  - No se realizan validaciones para algunos campos como `Accept`
  - No se permiten multiples campos `Content-Type`
    - No se verifica la duplicidad de distintos headers

#### v0.0.4
- Se realiza un procesamiento preliminar de la petición,
  de detectarse algún error en la petición se devuelve un código
  distinto a `200 OK`

#### v0.0.3
- Ahora el usuario puede seleccionar la IP host del servidor
- El usuario puede definir las rutas del servidor y que métodos
  HTTP están permitidos en la ruta **[WIP]**

#### v0.0.2
- Ahora el usuario puede definir el puerto y cantidad de usuarios
  permitidos

#### v0.0.1
- Programa inicial
