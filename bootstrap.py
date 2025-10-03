import socket
from turtle import pu
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
        self.room_list = {}  # {"gaming": ["192.168.1.100:5000",1], "chat": ["1.2.3.4:7000",2]}
        self.timeout = timeout # no se usa aun
        self.room_size = room_size
        self.sock = create_udp_socket(ip, port)

    # ------ METHODS ----- #
    def start(self):
        ''' Metodo que maneja los join peers que quieren conectarse a una sala'''
        # hilo para manejar mensajes de protocolo
        while True:
            try:
                # extraer mensajes de la cola
                data, publi_addr = self.sock.recvfrom(1024)
                message = Olaf.decode_msg(data)
                publi_addr = list(publi_addr)

                # peer data
                msg_type, self_addr, peers, payload = message
                payload = payload.decode('utf-8')

                print(message, publi_addr)
                # msg[0]=comand, msg[1]=self_peer, msg[2]=peers_in_room, msg[3]=pyload

                if msg_type == JOIN_B:
                    if payload not in self.room_list:
                        # Verificar límite de salas antes de crear nueva
                        if len(self.room_list) >= self.room_size:
                            # Límite alcanzado, rechazar
                            error_msg = Olaf.encode_msg(ROOM_FULL, publi_addr, [], "")
                            self.sock.sendto(error_msg, (publi_addr[0], publi_addr[1]))
                            print(f"Rechazado peer {publi_addr} - límite de salas alcanzado")
                            
                        else:
                            # Primera vez: este peer es el entry (ID 1)
                            ip_port_id = [publi_addr[0], publi_addr[1], 1]
                            self.room_list[payload] = {"entry": ip_port_id, "next_id": 2}
                            message_data = Olaf.encode_msg(BOOTSTRAP_R, ip_port_id, [ip_port_id], payload)
                            self.sock.sendto(message_data, (publi_addr[0], publi_addr[1]))
                            print(f"Nueva sala '{payload}' creada por {publi_addr} (ID 1)")

                    else: # Sala existe: asignar nuevo ID y enviar entry actual
                        room_data = self.room_list[payload]
                        entry_peer = room_data["entry"]
                        new_id = room_data["next_id"]
                        
                        # Actualizar contador
                        room_data["next_id"] += 1
                        
                        # Crear dirección del nuevo peer
                        publi_addr_id = [publi_addr[0], publi_addr[1], new_id]
                        
                        message_data = Olaf.encode_msg(BOOTSTRAP_R, publi_addr_id, [entry_peer], payload)
                        self.sock.sendto(message_data, (publi_addr[0], publi_addr[1]))

                elif msg_type == ENTRY_PEER:
                    #reemplazar el peer de entrada
                    print(f"Recibido ENTRY_PEER de {publi_addr} para sala '{payload}'")
                    if payload in self.room_list:
                        room_data = self.room_list[payload]
                        # Mantener el ID original del entry peer (no cambiar el ID)
                        room_data["entry"] = [publi_addr[0], publi_addr[1], room_data["entry"][2]]
                        print(f"Peer {publi_addr} reemplazado como entrada en sala '{payload}' con ID {room_data['entry'][2]}")
                    else:
                        print(f"ERROR: Sala '{payload}' no encontrada para ENTRY_PEER")
                    
                else:
                    continue
                
            except KeyboardInterrupt:
                break