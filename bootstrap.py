import socket
import queue
import threading
import time
from olaf import Olaf

# luego estara en otro archivo
PING = 0
JOIN_B = 1
BOOTSTRAP_R = 2
APP_R = 3

# (msg_type=1, self_addr=["127.0.0.1", 12345], peers_addr=[["127.0.0.2", 23456], ["192.168.0.5", 34567]], payload="hola mundo")
def create_udp_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    return sock

class Bootstrap:
    def __init__(self, timeout=5, size=10, ip='', port=0):
    # --- PARA CUANDO ACTÚA COMO HOST ---
        self.room_list = {}  # {"gaming": ["192.168.1.100:5000", "10.0.0.5:6000"], "chat": ["1.2.3.4:7000"]}
        self.timeout = timeout # no se usa aun
        self.size = size # tamano de la lista (no se usa aun)
        self.sock = create_udp_socket(ip, port)
        
    # ------ METHODS ----- #
    def host(self):
        ''' Metodo que maneja los join peers que quieren conectarse a una sala'''
        # hilo para manejar mensajes de protocolo
        handler_thread = threading.Thread(target=self.handle_messages, daemon=True)
        handler_thread.start()


    def handle_messages(self):
        while True:
            # extraer mensajes de la cola
            data, addr = self.sock.recvfrom(1024)
            message = Olaf.decode_msg(data)
            addr = list(addr)

            print(message, addr)
            # msg[0]=comand, msg[1]=self_peer, msg[2]=peers_in_room, msg[3]=pyload

            if message[0] == JOIN_B:
                peer_room = message[3]
                

                if peer_room not in self.room_list:
                    # Verificar límite de salas antes de crear nueva
                    if len(self.room_list) >= self.size:
                        # Límite alcanzado, rechazar
                        error_msg = Olaf.encode_msg(BOOTSTRAP_R, addr, [], f"ERROR: Límite de salas alcanzado ({self.size})")
                        self.sock.sendto(error_msg, (addr[0], addr[1]))
                        print(f"Rechazado peer {addr} - límite de salas alcanzado")
                    else:
                        # Primera vez que alguien se une a esta room
                        self.room_list[peer_room] = [addr]
                        message_data = Olaf.encode_msg(BOOTSTRAP_R, addr, [], peer_room)
                        self.sock.sendto(message_data, (addr[0],addr[1]))
                        print(f"Nueva sala '{peer_room}' creada por {addr}")

                else:
                    # Ya existe la room
                    other_peers = [p for p in self.room_list[peer_room] if p != addr]  # Sin el que se está uniendo

                    # Agregar el nuevo peer a la lista completa del bootstrap
                    if addr not in self.room_list[peer_room]:
                        self.room_list[peer_room].append(addr)

                    # Enviar solo los "otros peers" al que se está uniendo
                    message_data = Olaf.encode_msg(BOOTSTRAP_R, addr, other_peers, peer_room)
                    self.sock.sendto(message_data, (addr[0],addr[1]))
                    print(f"Peer {addr} agregado a sala '{peer_room}'")

            else:
                continue


