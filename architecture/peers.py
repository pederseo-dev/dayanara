import time
class Peers:
    def __init__(self, timeout=15):
        self.peers_in_room = []
        self.peers_life = {}
        self.timeout = timeout

    def add_peer(self, peer_addr):
        self.peers_in_room.append(peer_addr)
        self.peers_life[peer_addr] = time.time()

    def remove_peer(self, peer_addr):
        self.peers_in_room.remove(peer_addr)
        del self.peers_life[peer_addr]

    def get_list(self):
        return self.peers_in_room

    def get_others(self, peer_addr):
        return [peer for peer in self.peers_in_room if peer[:2] != peer_addr[:2]]
        
    def delete_inactive(self):
        current_time = time.time()
        
        for peer_addr, last_seen in list(self.peers_life.items()):
            if current_time - last_seen > self.timeout:
                del self.peers_in_room[peer_addr]
                del self.peers_life[peer_addr]

    def update_ts(self, peer_addr):
        self.peers_life[peer_addr] = time.time()
                
