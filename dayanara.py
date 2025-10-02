import socket
import queue
import threading
import time
from olaf import Olaf
from config import *
# luego estara en otro archivo

# (msg_type=1, self_addr=["127.0.0.1", 12345], peers_addr=[["127.0.0.2", 23456], ["192.168.0.5", 34567]], payload="hola mundo")
def create_udp_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    return sock

class Dayanara:
    def __init__(self, timeout=5, size=100, ip='0.0.0.0', port=0):
    # --- PARA CUANDO ACTÚA COMO HOST ---
        self.peer_info = {"entry": False, "id": 0}
        self.app_queue = queue.Queue()
        self.bootstraps = [['127.0.0.1', 5000],['127.0.0.1', 5001]] # lista de boostraps publicos activos
        self.peers_in_room = []
        self.self_addr =  [ip, port]
        self.sock = create_udp_socket(ip, port)
    
    def join(self, room):
        ''' Metodo para crear peer y conecatrse a una sala'''
        if not room:
            print('error')

        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        listener = threading.Thread(target=self.handle_input_data, daemon=True)
        listener.start()
        # reintentos básicos de join_bootstrap en segundo plano
        retry_thread = threading.Thread(target=self.handle_connection, args=(room,), daemon=True)
        retry_thread.start()

    def send(self, data):
        ''' Metodo para enviar data a todos los peers'''
        if not data:
            print('error')
        other_peers = [peer for peer in self.peers_in_room if peer != self.self_addr]
        for peer in other_peers:
            message = Olaf.encode_msg(APP_R, self.self_addr, [], data)
            self.sock.sendto(message, tuple(peer))
    
    def receive(self):
        try:
            data = self.app_queue.get_nowait()
            print(data)
            message, addr = data  # Desempaquetar la tupla
            return message    # Acceder al payload del mensaje
        except queue.Empty:
            return None

    def handle_connection(self, room):
        while True:
            other_peers = [peer for peer in self.peers_in_room if peer != self.self_addr]
            
            if other_peers:
                # Hay otros peers, enviar PING solo a ellos (ya no al bootstrap)
                for peer in other_peers:
                    message = Olaf.encode_msg(PING, self.self_addr, self.peers_in_room, '')
                    self.sock.sendto(message, tuple(peer))
            
                if self.is_entry_peer:
                    # Peer de entrada solo: mantener keep-alive con bootstrap
                    message = Olaf.encode_msg(ENTRY_PEER, [], [], room)
                    self.sock.sendto(message, tuple(self.bootstraps[0]))
            
            else:
                # Peer normal solo: enviar JOIN_B al bootstrap
                message = Olaf.encode_msg(JOIN_B, self.self_addr, self.peers_in_room, room)
                self.sock.sendto(message, tuple(self.bootstraps[0]))
            
            time.sleep(3)

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
                    print('mensaje cargado a cola')

                elif msg_type == BOOTSTRAP_R:
                    if payload is not None:
                        # Actualizar mi dirección con la que me asignó el bootstrap
                        self.self_addr = message[1]
                        
                        # Actualizar lista de peers (excluyendo mi dirección)
                        self.peers_in_room.clear()
                        self.peers_in_room.extend(peers)
                        
                        # 
                        if message[2] == [self.self_addr]:
                            
                            self.is_entry_peer = True
                        else:
                            self.is_entry_peer = False
                    
                elif msg_type == ROOM_FULL:
                    # logica para cambiar de bootstrap si la sala esta llena
                    continue

                elif msg_type == PING:  
                    # NUEVO: Verificar si el peer que envía ping está registrado
                    if addr not in self.peers_in_room:
                        self.peers_in_room.append(addr)

                else:
                    continue
                    
                # print(message)  # Comentado para no mostrar mensajes de protocolo
                    
            except Exception as e:
                pass

            