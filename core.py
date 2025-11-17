from peer import Peer
from olaf import Olaf
from config import *
from network import Network
import queue
import time
import sys
import ast

class Core:
    def __init__(self, bootstraps=None):
        self.bootstraps = bootstraps
        self.app_queue = queue.Queue()
        self.network = Network(bootstraps)
        self.binary = Olaf()        
        self.peer = Peer()
        self.b_count = 0


    def connect(self):
        """Thread que recibe mensajes"""
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
        while True:
            self.network.evaluate_state()

            if self.network.purge: 
                self.network.delete_inactive()

            if self.network.send_ping: 
                self.peer.socket_send_all(
                    type=PING, 
                    peers=self.network.get_other_peers(), 
                    payload=''
                )

            if self.network.send_collector:
                self.peer.socket_send(
                    type=PEER_COLLECTOR,
                    payload=room, 
                    target_addr=self.network.bootstraps[self.b_count]
                )

            if self.network.send_join:
                peers = []
                if self.network.self_addr != None:
                    peers = [self.network.self_addr]
                self.peer.socket_send(
                    type=JOIN_B, 
                    peers=peers,
                    payload=room,
                    target_addr=self.network.bootstraps[self.b_count]
                )

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
        print(f"BOOTSTRAP_R recibido: con peers: {peers}")
        # formatear payload b'[ip, port, id]' como lista
        payload = self.decode_payload(payload)
        
        # Actualizar mi dirección con la que me asignó el bootstrap
        if self.network.self_addr is None:
            self.network.add_self_addr(payload)

        for peer in peers:
            self.network.add_peer(peer)
            print(f"Peer agregado: {peer}")


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
        return ast.literal_eval(text)