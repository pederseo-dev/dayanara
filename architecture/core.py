from .peer import Peer
from .olaf import Olaf
from .state import State
from .peers import Peers
from config import *
import queue
import time
import sys

class Core():
    def __init__(self):
        super().__init__()
        self.app_queue = queue.Queue()
        self.state = State()
        self.peer = Peer()
        self.peers = Peers()
        self.binary = Olaf()
        self.bootstraps = [['127.0.0.1', 5000],['127.0.0.1', 5001]] # lista de boostraps publicos activos
    

    def connect(self):
        while True:
            try:
                message, addr = self.peer.socket_receive()
                msg_type, public_addr, peers, payload = message
                
                # Filtrar por tipo de mensaje
                if msg_type == APP_R: self.app_queue.put((message, addr))

                elif msg_type == BOOTSTRAP_R: self.bootstrap_response(public_addr, peers)

                elif msg_type == PING: self.ping_response(peers, payload)

                elif msg_type == ROOM_FULL: continue

                else: continue

            except Exception as e: pass

    def heart(self, room):
        while True:
            # evaluar estado del peer
            if self.state.peers_handle: self.peers.delete_inactive()

            # 1. Si hay otros peers, enviar PINGs
            if self.state.send_ping: self.send_to_all(type=PING, payload='')

            # 2. Si no hay otros peers pero hay peers_in_room (solo yo), validar entry UNA VEZ
            if self.state.send_entry: self.send_one(type=ENTRY_PEER, payload='', target=self.bootstraps[0])

            # 3. Si no hay nadie y no me he unido, intentar JOIN_B
            if self.state.send_join: self.send_one(type=JOIN_B, payload=room, target=self.bootstraps[0])

            # heartbeat time
            time.sleep(0.5)
    
    def receive_data(self):
        return self.peer.socket_receive()

    def send_one(self, payload=None, type=None, target=None):
        data = self.binary.encode_msg(type, self.self_addr, self.peers_in_room, payload)
        self.peer.socket_send(data, target)


    def send_to_all(self, payload=None, type=APP_R):
        other_peers = [peer for peer in self.peers_in_room if peer[:2] != self.self_addr[:2]]
        for peer in other_peers:
            self.send_one(payload, type, peer)


    def signal_handler(self, sig, frame):
        try:
            self.send_to_all(data='bye', type=PING)
        except:
            pass
        self.peer.socket_close()
        sys.exit(0)


    def bootstrap_response(self, public_addr, peers):
        print(f"BOOTSTRAP_R recibido: {public_addr} con peers: {peers}")
        
        # Actualizar mi dirección con la que me asignó el bootstrap
        self.peer.self_addr = public_addr
        self.state.joined = False
        
        # Comparar con la dirección original, no con la actualizada
        for peer in peers:
            if peer not in self.peers.get_list():
                self.peers.add_peer(peer)


    def ping_response(self, addr, payload):
        print(f"Recibido PING de {addr} con payload: {payload}")
        if payload == b'bye':
            # Peer se desconectó, remover de la lista
            if addr in self.peers.get_list():
                self.peers.remove_peer(addr)
        else:
            # PING normal - solo agregar si no está en la lista
            if addr not in self.peers.get_list():
                self.peers.add_peer(addr)
                            