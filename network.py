import time
import threading

class State:
    def __init__(self):
        self.send_join = True
        self.send_collector = False
        self.send_ping = False
        self.purge = False

class Network(State):
    def __init__(self, timeout=15, ip='0.0.0.0', port=0, bootstraps=None):
        super().__init__()
        self.self_addr = None
        self.bootstraps = bootstraps # lista de boostraps publicos activos
        self.peers_in_room = []
        self.peers_life = {}
        self._lock = threading.Lock()
        self.timeout = timeout

    def add_self_addr(self, public_addr: list) -> None:
        with self._lock:
            self.self_addr = public_addr
            self.add_peer(self.self_addr)

    def add_peer(self, peer_addr: list) -> None:
        ''' add peer to the list: peer_addr = ['127.0.0.1', 5000, 0]'''
        with self._lock:
            if peer_addr not in self.peers_in_room:
                self.peers_in_room.append(peer_addr)
                self.peers_life[peer_addr[2]] = time.time()
        
    def remove_peer(self, peer_addr: list) -> None:
        ''' remove peer from the list: peer_addr = ['127.0.0.1', 5000, 0]'''
        with self._lock:
            if peer_addr in self.peers_in_room:
                self.peers_in_room.remove(peer_addr)
                del self.peers_life[peer_addr[2]]

    def get_peers_list(self) -> list:
        ''' get the list of peers in the room: return [peer1,peer2,peer3,...]'''
        with self._lock:
            return self.peers_in_room

    def get_other_peers(self) -> list:
        ''' get the list of other peers in the room'''
        with self._lock:
            if self.self_addr is None:
                return []
            return [peer for peer in self.peers_in_room if peer[:2] != self.self_addr[:2]]

    def min_id(self) -> bool:
        ''' check if self_addr has the minimum id'''
        with self._lock:
            if not self.peers_in_room:
                return False
            min_id = min(peer[2] for peer in self.peers_in_room)
            return self.self_addr[2] == min_id

    def delete_inactive(self) -> None:
        with self._lock:
            current_time = time.time()
            
            for peer_id, last_seen in list(self.peers_life.items()):
                if current_time - last_seen > self.timeout:
                    # Buscar el peer completo por su ID
                    peer_addr = next((peer for peer in self.peers_in_room if peer[2] == peer_id), None)
                    if peer_addr:
                        self.remove_peer(peer_addr)

    def update_ts(self, peer_addr: list) -> None:
        with self._lock:
            self.peers_life[peer_addr[2]] = time.time()

    def evaluate_state(self) -> None:
        with self._lock:
            # Calcular others directamente sin llamar a get_other_peers() para evitar deadlock
            if self.self_addr is None:
                others = []
            else:
                others = [peer for peer in self.peers_in_room if peer[:2] != self.self_addr[:2]]
            has_others = len(others) > 0  # ✅ Criterio correcto
            
            # Si hay OTROS peers (no solo yo)
            if has_others:
                self.purge = True
                self.send_ping = True
                self.send_join = False
                
                # Solo si soy el peer con menor ID, enviar COLLECTOR al bootstrap
                # Calcular min_id directamente sin llamar al método para evitar deadlock
                if not self.peers_in_room or self.self_addr is None:
                    is_min_id = False
                else:
                    min_id = min(peer[2] for peer in self.peers_in_room)
                    is_min_id = self.self_addr[2] == min_id
                
                if is_min_id:
                    self.send_collector = True
                else:
                    self.send_collector = False
            
            # Si estoy solo
            else:
                self.send_join = True
                self.send_ping = False
                self.send_collector = False
                self.purge = False
                
    def get_state(self) -> dict:
        return { 
            'send_collector': self.send_collector, 
            'send_join': self.send_join, 
            'send_ping': self.send_ping, 
            'purge': self.purge 
            }