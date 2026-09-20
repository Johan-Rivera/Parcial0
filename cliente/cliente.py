from xmlrpc.client import ServerProxy
from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.server import SimpleXMLRPCServer
import random
import socket
import threading
import time

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

index = ServerProxy("http://172.17.0.2:8000/RPC2")

ip = socket.gethostbyname(socket.gethostname())
puerto = 8000

nodos = []
lista_numeros = []
coleccion = []
repetidos = []
faltantes = []
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

def recibir_numeros(numeros):
    global lista_numeros
    with lock:
        lista_numeros = numeros
        actualizar_derivadas()
        print(f"\nEl indexador me repartio los numeros: {lista_numeros}")
        mostrar_numeros()
    return True

def escuchar():
    with SimpleXMLRPCServer((ip, puerto), requestHandler=RequestHandler, allow_none= True) as servidor:
        servidor.register_function(notificar_nuevo_cliente)
        servidor.register_function(notificar_cliente_desconectado)
        servidor.register_function(recibir_numeros)
        servidor.register_function(negociar_numeros)
        servidor.serve_forever()

def actualizar_derivadas():
    global coleccion, repetidos, faltantes
    coleccion = sorted(set(lista_numeros))
    repetidos = [n for n in set(lista_numeros) if lista_numeros.count(n) > 1]
    faltantes = [n for n in range(0, 11) if n not in coleccion]

def mostrar_numeros():
    print("Lista:", lista_numeros)
    print("Colección (ordenada):", coleccion)
    print("Repetidos:", repetidos)
    print("Faltantes:", faltantes)

def negociar_numeros(faltantes_solicitante, repetidos_solicitante):
    global lista_numeros
    with lock:
        actualizar_derivadas()

        puedo_dar = [n for n in repetidos if n in faltantes_solicitante]
        quiero = [n for n in faltantes if n in repetidos_solicitante]

        if not puedo_dar or not quiero:
            return {
                "estado": "ok",
                "recibir": None,
                "entregar": None
            }

        dar = random.choice(puedo_dar)
        recibir = random.choice(quiero)

        lista_numeros.remove(dar)
        lista_numeros.append(recibir)
        actualizar_derivadas()

        print(f"\nIntercambio: di {dar} al solicitante, recibi {recibir}.")
        mostrar_numeros()

        return {
            "estado": "ok",
            "recibir": dar,
            "entregar": recibir
        }

def negociar():
    if not nodos:
        print("No hay clientes en la red para negociar.")
        return

    print(f"Negociando con {len(nodos)} clientes en la red...")

    for n in nodos:
        try:
            cliente = ServerProxy(f"http://{n['ip']}:{n['puerto']}/RPC2")

            with lock:
                actualizar_derivadas()
                respuesta = cliente.negociar_numeros(faltantes, repetidos)

            if respuesta["estado"] == "ok" and respuesta["recibir"] is not None:
                with lock:
                    lista_numeros.append(respuesta["recibir"])
                    if lista_numeros.count(respuesta["entregar"]) > 1:
                        lista_numeros.remove(respuesta["entregar"])
                    actualizar_derivadas()
                print(f"\nIntercambio con {n['ip']}: recibi {respuesta['recibir']}, entregue {respuesta['entregar']}.")
                mostrar_numeros()
            else:
                print(f"\nSin intercambio posible con {n['ip']}.")
        except Exception as e:
            print(f"Error negociando con {n['ip']}: {e}")

    if not faltantes:
        print("Colección completa!")
    else:
        print("Aun faltan:", faltantes)                    


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
        comando = input("> ").strip()

        if comando == "negociar":
            negociar()
        else:
            print("Comando desconocido.")

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