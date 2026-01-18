from .core import Core
import signal
import threading
import time

class Dayanara(Core):
    def __init__(self, bootstraps=[['127.0.0.1', 5000], ['127.0.0.1', 5001]], debug=False):
        super().__init__(bootstraps, debug)

    def join(self, room):
        # ✅ Mover signal handler aquí (se ejecuta en thread principal)
        # signal.signal(signal.SIGINT, self.signal_handler)
        
        threading.Thread(target=self.connect, daemon=True).start()
        threading.Thread(target=self.heart, args=(room,), daemon=True).start()

        # # Mantener el programa vivo
        # try:
        #     while True:
        #         time.sleep(1)
        # except KeyboardInterrupt:
        #     print("Cerrando...")


    def send(self, data):
        self.app_send(data)

    def receive(self):
        return self.app_receive()
    
    def peers_list(self):
        return self.network.get_peers_list()