class State:
    def __init__(self):
        self.state = {"joined": False, "entry_peer":False, "peers_in_room":False}
        self.peers_in_room = []
        self.self_addr = ["0.0.0.0", 0, 0]
        self.peers_life = {}