from xmlrpc.server import SimpleXMLRPCRequestHandler
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import socket

class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

ip = socket.gethostbyname(socket.gethostname())
puerto = 8000
print(f"Indexador escuchando en {ip}:{puerto}")

with SimpleXMLRPCServer((ip, puerto), requestHandler=RequestHandler) as server:

    nodos = []

    def notificar(ip_emisor, metodo, *args):
        for n in nodos:
            if n['ip'] != ip_emisor:
                try:
                    cliente = ServerProxy(f"http://{n['ip']}:{n['puerto']}/RPC2")
                    getattr(cliente, metodo)(*args)
                except Exception as e:
                    print(f"No se pudo notificar a {n['ip']}: {e}")

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

    server.register_function(registrarse)
    server.register_function(desconectarse)

    server.serve_forever()