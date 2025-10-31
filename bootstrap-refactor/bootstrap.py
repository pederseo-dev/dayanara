from peer import Peer
from olaf import Olaf
from config import *
import sys
import signal


class Bootstrap():
    def __init__(self, ip, port, timeout=5, room_size=10):
        self.peer = Peer()
        self.binary = Olaf()
        self.room_list = {} # {room_name: {"entry": [ip, port, id], "next_id": int}, ...}
        self.timeout = timeout
        self.room_size = room_size

    def start(self):

        signal.signal(signal.SIGINT, self.signal_handler)

        self.connect()

    def signal_handler(self, sig, frame):
        self.sock.close()
        sys.exit(0)

    def connect(self):
        while True:
            try:
                # extraer mensajes de la cola
                data, public_addr = self.sock.recvfrom(1024)
                msg_type, self_addr, peers, payload = Olaf.decode_msg(data)
                public_addr = [public_addr[0], public_addr[1]]

                if msg_type == JOIN_B: self.join_res(public_addr,payload)

                elif msg_type == ENTRY_PEER: self.entry_res(public_addr,payload)

                else: continue
                
            except KeyboardInterrupt: break

    def join_res(self,public_addr, payload):
        if payload not in self.room_list:
            # Verificar límite de salas antes de crear nueva
            if len(self.room_list) >= self.room_size:
                # Límite alcanzado, rechazar
                error_msg = Olaf.encode_msg(ROOM_FULL, public_addr, [], "")
                self.sock.sendto(error_msg, (public_addr[0], public_addr[1]))
                print(f"Rechazado peer {public_addr} - límite de salas alcanzado")
                
            else:
                # Primera vez: este peer es el entry (ID 1)
                ip_port_id = [public_addr[0], public_addr[1], 1]
                self.room_list[payload] = {"entry": ip_port_id, "next_id": 2}
                print(f"Enviando BOOTSTRAP_R con self_addr: {ip_port_id}")
                message_data = Olaf.encode_msg(BOOTSTRAP_R, ip_port_id, [ip_port_id], payload)
                print(f"Mensaje codificado: {message_data}")
                self.sock.sendto(message_data, (public_addr[0], public_addr[1]))
                print(f"Nueva sala '{payload}' creada por {public_addr} (ID 1)")

        else: # Sala existe: asignar nuevo ID y enviar entry actual
            room_data = self.room_list[payload]
            entry_peer = room_data["entry"]
            new_id = room_data["next_id"]
            
            # Actualizar contador
            room_data["next_id"] += 1
            
            # Crear dirección del nuevo peer
            publi_addr_id = [public_addr[0], public_addr[1], new_id]
            
            print(f"Enviando BOOTSTRAP_R con self_addr: {publi_addr_id}")
            message_data = Olaf.encode_msg(BOOTSTRAP_R, publi_addr_id, [entry_peer], payload)
            print(f"Mensaje codificado: {message_data}")
            self.sock.sendto(message_data, (public_addr[0], public_addr[1]))

    def entry_res(self,public_addr, payload):
                #reemplazar el peer de entrada
        print(f"Recibido ENTRY_PEER de {public_addr} para sala '{payload}'")
        if payload in self.room_list:
            room_data = self.room_list[payload]
            # Mantener el ID original del entry peer (no cambiar el ID)
            room_data["entry"] = [public_addr[0], public_addr[1], room_data["entry"][2]]
            print(f"Peer {public_addr} reemplazado como entrada en sala '{payload}' con ID {room_data['entry'][2]}")
        else:
            print(f"ERROR: Sala '{payload}' no encontrada para ENTRY_PEER")