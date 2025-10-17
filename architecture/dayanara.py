from peer import UDP_socket
from state import State
from conn_handler import Conn_handler
import threading
from olaf import Olaf
from config import *
import sys
import signal

class Dayanara(State):
    def __init__(self):
        self.udp_socket = UDP_socket()
        self.binary = Olaf()
        super().__init__()

    def join(self, room):
        ''' Metodo para crear peer y conecatrse a una sala'''
        if not room: print('error')

        # handler para cerrar el socket
        # signal.signal(signal.SIGINT, self.signal_handler)

        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        listener = threading.Thread(target=self.handle_input_data, daemon=True)
        listener.start()

        # reintentos básicos de send_join_bootstrap en segundo plano
        retry_thread = threading.Thread(target=self.heart_beat, args=(room,), daemon=True)
        retry_thread.start()

    def send(self, data):
        if not data: print('error')
        self.send_all(data)

    def receiv(self):
        data, address = self.udp_socket.receive()
        return self.binary.decode_msg(data), address
    
    def send_one(self, message, type, target):
        message = self.binary.encode_msg(type, self.self_addr, self.peers_in_room, '')
        self.udp_socket.send(message, (target[0],target[1]))

    def send_to_all(self, message='', type=PING):
        other_peers = [peer for peer in self.peers_in_room if peer[:2] != self.self_addr[:2]]
        for peer in other_peers:
            self.send_one(message, type, peer)

    def handle_input_data(self):
        while True:
            try:
                data, address = self.udp_socket.receive()
                message = self.binary.decode_msg(data)

                msg_type, self_addr, peers, payload = message
                addr = list(address)
                
                # Filtrar por tipo de mensaje
                if msg_type == APP_R:
                    # Mensajes de aplicación van a app_queue
                    self.app_queue.put((message, addr))  # payload + dirección

                elif msg_type == BOOTSTRAP_R:
                    print(f"BOOTSTRAP_R recibido: {message}")
                    
                    # Actualizar mi dirección con la que me asignó el bootstrap
                    self.self_addr = self_addr
                    
                    # Comparar con la dirección original, no con la actualizada
                    for peer in peers:
                        if peer not in self.peers_in_room:
                            self.peers_in_room.append(peer)
                    
                elif msg_type == ROOM_FULL:
                    # logica para cambiar de bootstrap si la sala esta llena
                    continue

                elif msg_type == PING:
                    print(f"Recibido PING de {self_addr} con payload: {payload}")
                    if payload == b'bye':
                        # Peer se desconectó, remover de la lista
                        if self_addr in self.peers_in_room:
                            self.peers_in_room.remove(self_addr)
                    else:
                        # PING normal - solo agregar si no está en la lista
                        if self_addr not in self.peers_in_room:
                            self.peers_in_room.append(self_addr)
                else:
                    continue

            except Exception as e:
                pass