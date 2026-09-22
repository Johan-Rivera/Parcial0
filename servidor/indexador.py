from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import random
import socket
import threading
import time

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

ip = socket.gethostbyname(socket.gethostname())
puerto = 8000
print(f"Indexador escuchando en {ip}:{puerto}")

nodos = []

def registrarse(ip_cliente, puerto_cliente):

    for n in nodos[:]:
        if n['ip'] == ip_cliente:
            nodos.remove(n)

    nuevo = {
        "ip": ip_cliente,
        "puerto": puerto_cliente
    }

    nodos.append(nuevo)
    print(f"Cliente {ip_cliente}:{puerto_cliente} registrado. Total: {len(nodos)}")

    notificar(ip_cliente, "notificar_nuevo_cliente", nuevo)

    return {
        "estado": "ok",
        "nodos": nodos
    }

def desconectarse(ip_cliente):

    for n in nodos[:]:
        if n['ip'] == ip_cliente:
            nodos.remove(n)

    print(f"Cliente {ip_cliente} se ha desconectado. Total: {len(nodos)}")

    notificar(ip_cliente, "notificar_cliente_desconectado", ip_cliente, nodos)

    return {
        "estado": "ok"
    }

def escuchar():
    with SimpleXMLRPCServer((ip, puerto), requestHandler=RequestHandler) as server:
        server.register_function(registrarse)
        server.register_function(desconectarse)

        server.serve_forever()

def notificar(ip_emisor, metodo, *args):
    for n in nodos:
        if n['ip'] != ip_emisor:
            try:
                cliente = ServerProxy(f"http://{n['ip']}:{n['puerto']}/RPC2")

                if metodo == 'notificar_nuevo_cliente':
                    cliente.notificar_nuevo_cliente(*args)
                elif metodo == 'notificar_cliente_desconectado':
                    cliente.notificar_cliente_desconectado(*args)
            except Exception as e:
                print(f"No se pudo notificar a {n['ip']}: {e}")

def repartir_numeros():

    if not nodos:
        print("No hay clientes registrados en la red.")
        return

    for n in nodos:
        numeros = [random.randint(0, 10) for _ in range(11)]
        try:
            cliente = ServerProxy(f"http://{n['ip']}:{n['puerto']}/RPC2")
            cliente.recibir_numeros(numeros)
            print(f"Numeros repartidos a {n['ip']}: {numeros}")
        except Exception as e:
            print(f"No se pudo repartir a {n['ip']}: {e}")

    print("Reparto de numeros completado.")

def chat():
    while True:
        comando = input("> ").strip()

        if comando == "repartir":
            repartir_numeros()
        elif comando == "clear":
            print("\033[2J\033[H", end="")
        elif comando == "salir":
            print("Indexador apagado.")
            break
        else:
            print("Comando desconocido.")

if __name__ == '__main__':
    threading.Thread(target=escuchar, daemon=True).start()
    threading.Thread(target=chat, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Indexador apagado.")