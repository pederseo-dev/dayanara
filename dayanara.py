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
        self.app_queue = queue.Queue()
        self.bootstraps = [['127.0.0.1', 5000],['127.0.0.1', 5001]] # lista de boostraps publicos activos
        self.peers_in_room = []
        self.self_addr =  [ip, port, 0]
        self.sock = create_udp_socket(ip, port)
    # def detect_disconnections(self):

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
        # Excluir a sí mismo comparando solo IP y puerto (ignorar ID que puede diferir)
        other_peers = [peer for peer in self.peers_in_room 
                      if peer[:2] != self.self_addr[:2]]
        for peer in other_peers:
            message = Olaf.encode_msg(APP_R, self.self_addr, [], data)
            self.sock.sendto(message, (peer[0],peer[1]))
    
    def receive(self):
        try:
            data = self.app_queue.get_nowait()
            print(data)
            message, addr = data  # Desempaquetar la tupla
            return message, addr    # Acceder al payload del mensaje
        except queue.Empty:
            return None
#-----------------------------------------------------------------------------------------------------#

    def handle_connection(self, room):

        while True:
            other_peers = [peer for peer in self.peers_in_room 
                          if peer[:2] != self.self_addr[:2]]
            
            # Enviar PINGs a otros peers si existen  
            if other_peers:
                for peer in other_peers:
                    message = Olaf.encode_msg(PING, self.self_addr, self.peers_in_room, '')
                    self.sock.sendto(message, (peer[0],peer[1]))
            
            # Evaluar en cada latido si soy el entry peer (ID más bajo)
            if self.peers_in_room:
                min_id = min(peer[2] for peer in self.peers_in_room)

                if self.self_addr[2] == min_id:
                    message = Olaf.encode_msg(ENTRY_PEER, self.self_addr, [], room)
                    self.sock.sendto(message, tuple(self.bootstraps[0]))
            else:
                # Peer normal: enviar JOIN_B solo si no hay otros peers
                if not other_peers:
                    message = Olaf.encode_msg(JOIN_B, [], [], room)
                    self.sock.sendto(message, tuple(self.bootstraps[0]))

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
                    # Actualizar mi dirección con la que me asignó el bootstrap
                    self.self_addr = self_addr
                    
                    # Solo agregar el entry peer si no está en la lista y no soy yo mismo
                    for peer in peers:
                        if peer not in self.peers_in_room and peer != self.self_addr:
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
                            print(f"Peer {self_addr} se desconectó - removido de la lista")
                            print(f"Peers restantes: {self.peers_in_room}")
                        else:
                            print(f"Peer {self_addr} envió 'bye' pero no estaba en la lista")
                    else:
                        # PING normal - solo agregar si no está en la lista
                        if self_addr not in self.peers_in_room:
                            self.peers_in_room.append(self_addr)
                            print(f"Peer {self_addr} agregado a la lista")

                else:
                    continue
                    
                # print(message)  # Comentado para no mostrar mensajes de protocolo
                    
            except Exception as e:
                pass

    def notify_disconnection(self):
        """Notificar a otros peers que nos desconectamos"""
        other_peers = [peer for peer in self.peers_in_room 
                      if peer[:2] != self.self_addr[:2]]
        
        print(f"Notificando desconexión a {len(other_peers)} peers: {other_peers}")
        for peer in other_peers:
            message = Olaf.encode_msg(PING, self.self_addr, [], "bye")
            self.sock.sendto(message, (peer[0], peer[1]))
            print(f"Enviado 'bye' a {peer}")
