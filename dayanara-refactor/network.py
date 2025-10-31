import time

class State:
    def __init__(self):
        self.send_join = True
        self.send_entry = False
        self.send_ping = False
        self.purge = False

class Network(State):
    def __init__(self, timeout=15, ip='0.0.0.0', port=0):
        super().__init__()
        self.self_addr = [ip, port, 0]
        self.peers_in_room = []
        self.peers_life = {}
        self.timeout = timeout

    def add_peer(self, peer_addr):
        self.peers_in_room.append(peer_addr)
        self.peers_life[peer_addr] = time.time()

    def remove_peer(self, peer_addr):
        if peer_addr in self.peers_in_room:
            self.peers_in_room.remove(peer_addr)
            del self.peers_life[peer_addr]

    def get_list(self):
        return self.peers_in_room

    def get_others(self):
        """Retorna lista de otros peers (sin modificar estado)"""
        return [peer for peer in self.peers_in_room if peer[:2] != self.self_addr[:2]]

    def min_id(self):
        """Retorna True si peer_addr tiene el ID más bajo (sin modificar estado)"""
        if not self.peers_in_room:
            return False
        min_id = min(peer[2] for peer in self.peers_in_room)
        return self.self_addr[2] == min_id

    def delete_inactive(self):
        current_time = time.time()
        
        for peer_addr, last_seen in list(self.peers_life.items()):
            if current_time - last_seen > self.timeout:
                self.peers_in_room.remove(peer_addr)
                del self.peers_life[peer_addr]

    def update_ts(self, peer_addr):
        self.peers_life[peer_addr] = time.time()

    def evaluate_state(self):
        has_peers = len(self.peers_in_room) > 0
        others = self.get_others()
        
        # Si hay peers en la lista
        if has_peers:
            self.purge = True
            self.send_ping = True
            self.send_join = False
            
            # Solo si soy el peer con menor ID, enviar ENTRY al bootstrap
            if self.min_id():
                self.send_entry = True
            else:
                self.send_entry = False
                
        # Primera conexión - no hay peers en la lista
        else:
            self.send_join = True
            self.send_ping = False
            self.send_entry = False
            self.purge = False
                
