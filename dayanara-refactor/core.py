from .peer import Peer
from .olaf import Olaf
from .network import Network
from config import *
import queue
import time
import sys

class Core():
    def __init__(self):
        super().__init__()
        self.app_queue = queue.Queue()
        self.peer = Peer()
        self.network = Network()
        self.binary = Olaf()
        self.bootstraps = [['127.0.0.1', 5000],['127.0.0.1', 5001]] # lista de boostraps publicos activos
    

    def connect(self):
        while True:
            try:
                message, addr = self.peer.socket_receive()
                msg_type = message[0]
                
                # Filtrar por tipo de mensaje
                if msg_type == APP_R: self.app_queue.put((message, addr))

                elif msg_type == BOOTSTRAP_R: self.bootstrap_res(message, addr)

                elif msg_type == PING: self.ping_res(message, addr)

                elif msg_type == ROOM_FULL: continue

                else: continue

            except Exception as e: pass


    def heart(self, room):
        while True:
            # Evaluar estado de la red y actualizar flags
            self.network.evaluate_state()

            # eliminar peers inactivos
            if self.network.purge: self.network.delete_inactive()

            # 1. Si hay otros peers, enviar PINGs
            if self.network.send_ping: self.send_to_all(type=PING, payload='')

            # 2. Si soy min_id, validar entry al bootstrap
            if self.network.send_entry: self.send_one(type=ENTRY_PEER, payload='', target=self.bootstraps[0])

            # 3. Si no hay nadie y no me he unido, intentar JOIN_B
            if self.network.send_join: self.send_one(type=JOIN_B, payload=room, target=self.bootstraps[0])

            # heartbeat time
            time.sleep(3)
    

    def receive_data(self):
        data, addr = self.peer.socket_receive()
        return self.binary.decode_msg(data), list(addr)


    def send_one(self,type=None, payload='',public_addr=[], peers=[], target=None):
        data = self.binary.encode_msg(type, public_addr, peers, payload)
        self.peer.socket_send(data, target)


    def send_to_all(self, payload=None, type=APP_R):
        other_peers = self.network.get_others()
        for peer in other_peers:
            self.send_one(payload=payload, type=type)


    def signal_handler(self, sig, frame):
        try:
            self.send_to_all(data='bye', type=PING)
        except:
            pass
        self.peer.socket_close()
        sys.exit(0)


    def bootstrap_res(self, message, addr):
        msg_type, public_addr, peers, payload = message
        print(f"BOOTSTRAP_R recibido: {addr} con peers: {peers}")
        
        # Actualizar mi dirección con la que me asignó el bootstrap
        self.network.self_addr = addr
        
        # Comparar con la dirección original, no con la actualizada
        for peer in peers:
            if peer not in self.network.get_list():
                self.network.add_peer(peer)


    def ping_res(self, message, addr):
        msg_type, public_addr, peers, payload = message
        print(f"Recibido PING con payload: {payload}")
        if payload == b'bye':
            # Peer se desconectó, remover de la lista
            if addr in self.network.get_list():
                self.network.remove_peer(addr)
        else:
            # PING normal - solo agregar si no está en la lista
            for peer in peers:
                if peer not in self.network.get_list():
                    self.network.add_peer(peer)


