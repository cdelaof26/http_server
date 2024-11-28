# Utilidades de redes

from util import config
import subprocess
import re


def es_mascara(ip: str) -> bool:
    # Cuando se realiza ipconfig en Windows, es común que aparezcan las máscaras de red
    # 255.255.255.0 (24 bits), esta función es para detectarlas,
    # TODO: agregar soporte para más máscaras
    # TODO: filtrar gateway y otras IPs no deseadas
    return ip == "255.255.255.0"


def obtener_ip() -> list:
    es_windows = config.PLATAFORMA == "nt"
    ip_comando = "ipconfig" if es_windows else "ifconfig"

    proceso = subprocess.Popen(ip_comando, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    stdout, _ = proceso.communicate()
    salida = stdout.decode()

    if "not found" in salida and not es_windows:  # En caso de que no exista ifconfig
        proceso = subprocess.Popen("ip a", shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        stdout, _ = proceso.communicate()
        salida = stdout.decode()

    assert "not found" not in salida

    _ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", salida)
    ips = list()
    for _ip in _ips:
        if es_mascara(_ip) or _ip in ips:
            continue
        ips.append(_ip)

    return ips
