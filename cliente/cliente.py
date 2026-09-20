from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.server import SimpleXMLRPCServer
import socket
import threading
import time

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

index = ServerProxy("http://172.17.0.2:8000/RPC2")

ip = socket.gethostbyname(socket.gethostname())
puerto = 8000

nodos = []
lock = threading.Lock()

def notificar_nuevo_cliente(nodo):
    global nodos
    with lock:
        nodos = [n for n in nodos if n["ip"] != nodo["ip"]]
        if nodo["ip"] != ip:
            nodos.append(nodo)
            print(f"\nUn cliente en {nodo['ip']}:{nodo['puerto']} ha ingresado en la red.")
            print("Nodos:", nodos)
    return True

def notificar_cliente_desconectado(ip_saliente, lista_nodos):
    global nodos
    with lock:
        nodos = [n for n in lista_nodos if n["ip"] != ip]
        print(f"\nUn cliente en {ip_saliente} se ha salido de la red.")
        print("Nodos:", nodos)
    return True

def escuchar():
    with SimpleXMLRPCServer((ip, puerto), requestHandler=RequestHandler) as servidor:
        servidor.register_function(notificar_nuevo_cliente)
        servidor.register_function(notificar_cliente_desconectado)
        servidor.serve_forever()

def registrarse():
    global nodos
    respuesta = index.registrarse(ip, puerto)

    if respuesta["estado"] == "ok":
        with lock:
            nodos = [n for n in respuesta["nodos"] if n["ip"] != ip]
            print(f"Cliente {ip}:{puerto} registrado en la red.")
            print("Nodos:", nodos)

def desconectarse():
    try:
        index.desconectarse(ip)
    except Exception as e:
        print(f"Error al desconectarse: {e}")

def chat():
    while True:
        _ = input("> ").strip()

if __name__ == "__main__":
    threading.Thread(target=escuchar, daemon=True).start()
    threading.Thread(target=chat, daemon=True).start()
    registrarse()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        desconectarse()
        print("Cliente desconectado de la red.")