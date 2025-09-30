import socket
from olaf import Olaf
from config import *
# luego estara en otro archivo


# (msg_type=1, self_addr=["127.0.0.1", 12345], peers_addr=[["127.0.0.2", 23456], ["192.168.0.5", 34567]], payload="hola mundo")
def create_udp_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    return sock

class Bootstrap:
    def __init__(self, timeout=5, room_size=10, ip='', port=0):
    # --- PARA CUANDO ACTÚA COMO HOST ---
        self.room_list = {}  # {"gaming": ["192.168.1.100:5000", "10.0.0.5:6000"], "chat": ["1.2.3.4:7000"]}
        self.timeout = timeout # no se usa aun
        self.room_size = room_size
        self.sock = create_udp_socket(ip, port)

    # ------ METHODS ----- #
    def start(self):
        ''' Metodo que maneja los join peers que quieren conectarse a una sala'''
        # hilo para manejar mensajes de protocolo
        print('iniciando bootstrap')

        while True:
            # extraer mensajes de la cola
            data, publi_addr = self.sock.recvfrom(1024)
            message = Olaf.decode_msg(data)
            publi_addr = list(publi_addr)
            room_name = message[3]

            print(message, publi_addr)
            # msg[0]=comand, msg[1]=self_peer, msg[2]=peers_in_room, msg[3]=pyload

            if message[0] == JOIN_B:

                if room_name not in self.room_list:
                    # Verificar límite de salas antes de crear nueva
                    if len(self.room_list) >= self.room_size:
                        # Límite alcanzado, rechazar
                        error_msg = Olaf.encode_msg(ROOM_FULL, publi_addr, [], "")
                        self.sock.sendto(error_msg, (publi_addr[0], publi_addr[1]))
                        print(f"Rechazado peer {publi_addr} - límite de salas alcanzado")
                    else:
                        # se crea la room con el peer que se une
                        self.room_list[room_name] = publi_addr
                        message_data = Olaf.encode_msg(BOOTSTRAP_R, publi_addr, [self.room_list[room_name]], room_name)
                        self.sock.sendto(message_data, (publi_addr[0],publi_addr[1]))
                        print(f"Nueva sala '{room_name}' creada por {publi_addr}")

                # si la room existe
                else:
                    # Enviar al peer de entrada
                    entry_peer = self.room_list[room_name]
                    message_data = Olaf.encode_msg(BOOTSTRAP_R, publi_addr, [entry_peer], room_name)
                    self.sock.sendto(message_data, (publi_addr[0],publi_addr[1]))
                    print(f"Peer {publi_addr} dirigido a entrada {entry_peer} en sala '{room_name}'")
            elif message[0] == ENTRY_PEER:
                #reemplazar el peer de entrada
                self.room_list[room_name] = publi_addr
                print(f"Peer {publi_addr} reemplazado como entrada en sala '{message[3]}'")
            else:
                continue


