from core import Core
import signal
import threading
import time

class Dayanara(Core):
    def __init__(self, bootstraps=[['127.0.0.1', 5000], ['127.0.0.1', 5001]]):
        super().__init__(bootstraps)

    def join(self, room):

        signal.signal(signal.SIGINT, self.signal_handler)

        threading.Thread(target=self.connect, daemon=True).start()

        threading.Thread(target=self.heart, args=(room,), daemon=True).start()

    def send(self, data):
        self.app_send(data)

    def receive(self):
        return self.app_receive()



# use test
#d = Dayanara(bootstraps=[['127.0.0.1', 5000]])
#d.join('sala')

#while True:
#    data = d.receive()
#    print(data)
#    time.sleep(1)
