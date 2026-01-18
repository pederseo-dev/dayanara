import time
import queue
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

        # Registro de nodos
        self.peers_in_room = []
        self.peers_life = {}

        self.write_queue = queue.Queue()
        self.timeout = timeout

        self._writer_thread = threading.Thread(
            target=self.write_thread,
            daemon=True
        ).start()

# ------------------------------------------------threading pipeline------------------------------------------
    def write_thread(self):
        while True:
            
            cmd, peer = self.write_queue.get()

            if cmd == 'add_self_addr':
                self.self_addr = peer
                if peer not in self.peers_in_room:
                    self.peers_in_room.append(peer)
                    self.peers_life[peer[2]] = time.time()

            elif cmd == 'add_peer':
                if peer not in self.peers_in_room:
                    self.peers_in_room.append(peer)
                    self.peers_life[peer[2]] = time.time()

            elif cmd == 'remove_peer':
                if peer in self.peers_in_room:
                    self.peers_in_room.remove(peer)
                    del self.peers_life[peer[2]]

            elif cmd == 'delete_inactive':
                current_time = time.time()
                
                for peer_id, last_seen in list(self.peers_life.items()):
                    if current_time - last_seen > self.timeout:
                        # Buscar el peer completo por su ID
                        peer_addr = next((peer for peer in self.peers_in_room if peer[2] == peer_id), None)
                        if peer_addr:
                            self.peers_in_room.remove(peer_addr)
                            del self.peers_life[peer_addr[2]]

            elif cmd == 'update_ts':
                if peer and peer[2] in self.peers_life:
                    self.peers_life[peer[2]] = time.time()

            else: continue # ignora silenciosamente

# ---------------------------------------------------WRITE-------------------------------------------------

    def add_self_addr(self, public_addr: list) -> None:
        self.write_queue.put(('add_self_addr', public_addr))

    def add_peer(self, peer_addr: list) -> None:
        self.write_queue.put(('add_peer', peer_addr))
        
    def remove_peer(self, peer_addr: list) -> None:
        self.write_queue.put(('remove_peer', peer_addr))

    def delete_inactive(self) -> None:
        self.write_queue.put(('delete_inactive', None))

    def update_ts(self, peer_addr: list) -> None:
        self.write_queue.put(('update_ts', peer_addr))

# ---------------------------------------------- READ-------------------------------------------------------

    def get_peers_list(self) -> list: # Read
        ''' get the list of peers in the room: return [peer1,peer2,peer3,...]'''
        return self.peers_in_room.copy()

    def get_other_peers(self) -> list: # Read
        ''' get the list of other peers in the room'''
        p_i_r_copy = self.peers_in_room.copy()

        if self.self_addr is None:
            return []
        return [peer for peer in p_i_r_copy if peer[:2] != self.self_addr[:2]]

    def min_id(self) -> bool: # Read
        ''' check if self_addr has the minimum id'''
        p_i_r_copy = self.peers_in_room.copy()
 
        if not p_i_r_copy:
            return False
        min_id = min(peer[2] for peer in p_i_r_copy)
        return self.self_addr[2] == min_id


# ---------------------------------------------STATUS-----------------------------------------------
    def evaluate_state(self) -> None:
        p_i_r_copy = self.peers_in_room.copy()
        # Calcular others directamente sin llamar a get_other_peers() para evitar deadlock
        if self.self_addr is None:
            others = []
        else:
            others = [peer for peer in p_i_r_copy if peer[:2] != self.self_addr[:2]]
        has_others = len(others) > 0  # ✅ Criterio correcto
            
        # Si hay OTROS peers (no solo yo)
        if has_others:
            self.purge = True
            self.send_ping = True
            self.send_join = False
                
            # Solo si soy el peer con menor ID, enviar COLLECTOR al bootstrap
            # Calcular min_id directamente sin llamar al método para evitar deadlock
            if not p_i_r_copy or self.self_addr is None:
                is_min_id = False
            else:
                min_id = min(peer[2] for peer in p_i_r_copy)
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