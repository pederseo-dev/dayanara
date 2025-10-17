from olaf import Olaf
from config import *

class Conn_handler:
    def __init__(self):
        self.binary = Olaf()
          

    def handle_input_data(self):
        while True:
            try:
                data, address = self.sock.recvfrom(1024)
                message = Olaf.decode_msg(data)

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