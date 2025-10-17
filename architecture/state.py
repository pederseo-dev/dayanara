import queue

class State:
    def __init__(self):
        self.state = {"joined": False, "entry_peer":False, "peers_in_room":False}
        self.app_queue = queue.Queue()
        self.peers_in_room = []
        self.self_addr = ["0.0.0.0", 0, 0]
        self.bootstraps = [['127.0.0.1', 5000],['127.0.0.1', 5001]] # lista de boostraps publicos activos
        self.peers_life = {}