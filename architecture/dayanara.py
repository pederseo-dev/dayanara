from .core import Core
import threading
import signal

class Dayanara(Core):
    def __init__(self):
        super().__init__()

    def join(self, room):
        ''' Metodo para crear peer y conecatrse a una sala'''
        # validar que la sala no sea None
        if not room: print('Room is required')

        # handler para cerrar el socket
        signal.signal(signal.SIGINT, self.signal_handler)

        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        listener = threading.Thread(target=self.connect, daemon=True)
        listener.start()

        # mantiene la conexion entre los peers
        retry_thread = threading.Thread(target=self.heart, args=(room,), daemon=True)
        retry_thread.start()

    def send(self, data):
        if not data: print('Data is required')
        self.send_to_all(payload=data)

    def receive(self):
        data, address = self.receive_data()
        return data, address
