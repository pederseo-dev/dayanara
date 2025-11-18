from peer import Peer
from olaf import Olaf
from config import *
from network import Network
import queue
import time
import sys
import ast

class Core:
    def __init__(self, bootstraps=[['127.0.0.1', 5000], ['127.0.0.1', 5001]]):
        self.bootstraps = bootstraps
        self.app_queue = queue.Queue()
        print(f"[DEBUG Core.__init__] Bootstraps recibidos: {bootstraps}")
        self.network = Network(bootstraps=bootstraps)
        print(f"[DEBUG Core.__init__] Network.bootstraps configurado: {self.network.bootstraps}")
        self.binary = Olaf()        
        self.peer = Peer()
        self.b_count = 0


    def connect(self):
        """Thread que recibe mensajes"""
        print(f"[DEBUG connect] Thread connect() iniciado")
        while True:
            try:
                message, addr = self.peer.socket_receive()
                msg_type = message[0]
                print(f"Mensaje recibido: {message}")
                
                if msg_type == APP_R: 
                    self.app_queue.put((message, addr))

                elif msg_type == BOOTSTRAP_R: 
                    self.bootstrap_res(message, addr)

                elif msg_type == PING: 
                    self.ping_res(message, addr)

                elif msg_type == ROOM_FULL: 
                    self.room_full(message, addr)

                else: 
                    print(f"Tipo de mensaje desconocido: {msg_type}")
            
            except Exception as e:
                print(f"Error procesando mensaje: {e}")
                continue

    def heart(self, room):
        print(f"[DEBUG heart] Thread heart() iniciado para room: {room}")
        iteration = 0
        while True:
            try:
                iteration += 1
                print(f"[DEBUG heart] Iteración #{iteration} - Antes de evaluate_state()")
                self.network.evaluate_state()
                print(f"[DEBUG heart] Iteración #{iteration} - Después de evaluate_state()")
                state = self.network.get_state()
                print(f"[DEBUG heart] Iteración #{iteration} - Estado evaluado: {state}, room: {room}")

                if self.network.purge: 
                    print(f"[DEBUG heart] Iteración #{iteration} - Ejecutando purge")
                    self.network.delete_inactive()

                if self.network.send_ping: 
                    print(f"[DEBUG heart] Iteración #{iteration} - Enviando PING")
                    self.peer.socket_send_all(
                        type=PING, 
                        peers=self.network.get_other_peers(), 
                        payload=''
                    )

                if self.network.send_collector:
                    if self.network.bootstraps is None or len(self.network.bootstraps) == 0:
                        print(f"[DEBUG heart] ERROR: No hay bootstraps configurados para enviar COLLECTOR")
                    else:
                        target = self.network.bootstraps[self.b_count]
                        print(f"[DEBUG heart] Iteración #{iteration} - Enviando PEER_COLLECTOR a bootstrap: {target}")
                        self.peer.socket_send(
                            type=PEER_COLLECTOR,
                            payload=room, 
                            target_addr=target
                        )

                if self.network.send_join:
                    print(f"[DEBUG heart] Iteración #{iteration} - send_join es True")
                    if self.network.bootstraps is None or len(self.network.bootstraps) == 0:
                        print(f"[DEBUG heart] ERROR: No hay bootstraps configurados para enviar JOIN_B")
                    else:
                        peers = []
                        if self.network.self_addr != None:
                            peers = [self.network.self_addr]
                        target = self.network.bootstraps[self.b_count]
                        print(f"[DEBUG heart] Iteración #{iteration} - Enviando JOIN_B a bootstrap: {target}, room: {room}, peers: {peers}")
                        try:
                            self.peer.socket_send(
                                type=JOIN_B, 
                                peers=peers,
                                payload=room,
                                target_addr=target
                            )
                            print(f"[DEBUG heart] Iteración #{iteration} - JOIN_B enviado exitosamente")
                        except Exception as e:
                            print(f"[DEBUG heart] ERROR al enviar JOIN_B: {e}")
                else:
                    print(f"[DEBUG heart] Iteración #{iteration} - send_join es False")

                print(f"[DEBUG heart] Iteración #{iteration} - Esperando 3 segundos...")
                time.sleep(3)
                print(f"[DEBUG heart] Iteración #{iteration} - Despertado, continuando loop")
            except Exception as e:
                print(f"[DEBUG heart] ERROR en iteración #{iteration}: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(3)

    def app_send(self, data):
        if data is None:
            raise ValueError("Data is required")
        self.peer.socket_send_all(type=APP_R, peers=self.network.get_other_peers(), payload=data)

    def app_receive(self):
        message, addr = self.app_queue.get()
        if message is None:
            return ''
        msg_type, peers, payload = message
        return payload

    def signal_handler(self, sig, frame):
        try:
            self.peer.socket_send_all(type=PING, peers=self.network.get_other_peers(), payload='bye')
        except Exception as e:
            print(f"Error al enviar despedida: {e}")
        
        self.peer.socket_close()
        sys.exit(0)

    def bootstrap_res(self, message, addr):
        _ , peers, payload = message
        print(f"[DEBUG bootstrap_res] BOOTSTRAP_R recibido de {addr}, peers: {peers}, payload raw: {payload}")
        # formatear payload b'[ip, port, id]' como lista
        payload = self.decode_payload(payload)
        print(f"[DEBUG bootstrap_res] Payload decodificado: {payload}")
        
        # Actualizar mi dirección con la que me asignó el bootstrap
        if self.network.self_addr is None:
            print(f"[DEBUG bootstrap_res] Asignando self_addr: {payload}")
            self.network.add_self_addr(payload)
        else:
            print(f"[DEBUG bootstrap_res] self_addr ya existe: {self.network.self_addr}")

        for peer in peers:
            self.network.add_peer(peer)
            print(f"[DEBUG bootstrap_res] Peer agregado: {peer}")


    def ping_res(self, message, addr):
        msg_type, peers, payload = message
        print(f"Recibido PING de {addr} con payload: {payload}")

        if payload == b'bye':
            peer_to_remove = None
            for peer in self.network.get_peers_list():
                if peer[0] == addr[0] and peer[1] == addr[1]:
                    peer_to_remove = peer
                    break
            
            if peer_to_remove:
                self.network.remove_peer(peer_to_remove)
                print(f"Peer {peer_to_remove[2]} removido")
        else:
            # Actualizar/agregar peers
            for peer in peers:
                self.network.add_peer(peer)
                self.network.update_ts(peer)


    def room_full(self, message, addr):
        print(message)

    def decode_payload(self, payload: bytes) -> list:
        # Decodificar el byte string a string normal
        text = payload.decode('utf-8')

        # Convertir el string a lista usando literal_eval
        print('payload decodificado:', ast.literal_eval(text))
        return ast.literal_eval(text)