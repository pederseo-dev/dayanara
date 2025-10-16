from peer import UDP_socket
from state import State

class Dayanara(State):
    def __init__(self):
        self.udp_socket = UDP_socket()
        super().__init__()

    def join(self, room):
        if not room:
            print("Error: Room is required")
            return
        
        self.state["joined"] = True
        self.state["entry_peer"] = True
        self.state["peers_in_room"] = True