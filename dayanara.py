import socket
import queue
import threading
import time
from olaf import Olaf
from config import *
import sys
import signal

class Dayanara:
    def __init__(self, timeout=5, size=100, ip='0.0.0.0', port=0):
    # --- PARA CUANDO ACTÚA COMO HOST ---
        self.app_queue = queue.Queue()
        self.sock = self.create_udp_socket(ip, port)
        self.bootstraps = [['127.0.0.1', 5000],['127.0.0.1', 5001]] # lista de boostraps publicos activos
        self.peers_in_room = []
        self.self_addr =  [ip, port, 0]
        self.peer_life = {} # id peer : time_last_ping
        self.state = {"joined": False, "entry_peer":False, "peers_in_room":False}

#----------------------------------------------APP functions
    def join(self, room):
        ''' Metodo para crear peer y conecatrse a una sala'''
        if not room: print('error')

        # handler para cerrar el socket
        signal.signal(signal.SIGINT, self.signal_handler)

        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        listener = threading.Thread(target=self.handle_input_data, daemon=True)
        listener.start()

        # reintentos básicos de send_join_bootstrap en segundo plano
        retry_thread = threading.Thread(target=self.heart_beat, args=(room,), daemon=True)
        retry_thread.start()

    def send(self, data):
        ''' Metodo para enviar data a todos los peers'''
        if not data: print('error')
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
#---------------------------------------------Core functions--------------------------------------------------------#

    def heart_beat(self, room):
        while True:
            # evaluar estado del peer
            self.state_eval()

            # 1. Si hay otros peers, enviar PINGs
            if self.state["peers_in_room"]: self.send_ping()

            # 2. Si no hay otros peers pero hay peers_in_room (solo yo), validar entry UNA VEZ
            if self.state["entry_peer"]: self.send_entry_ping()

            # 3. Si no hay nadie y no me he unido, intentar JOIN_B
            if self.state["joined"] == False: self.send_join_bootstrap(room)

            # heartbeat time
            time.sleep(0.5)

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

# -----------------------------------------------auxiliar functions
    def state_eval(self):
        if self.self_addr == ['0.0.0.0', 0, 0]:
            self.state["joined"] = False
        else:
            self.state["joined"] = True

        if self.peers_in_room:
            min_id = min(peer[2] for peer in self.peers_in_room)    
            self.state["entry_peer"] = self.self_addr[2] == min_id
            self.state["peers_in_room"] = True
        else:
            # Si no hay peers, soy el único = entry peer automáticamente
            self.state["entry_peer"] = True
            self.state["peers_in_room"] = False

# (msg_type=1, self_addr=["127.0.0.1", 12345], peers_addr=[["127.0.0.2", 23456], ["192.168.0.5", 34567]], payload="hola mundo")
    def create_udp_socket(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((ip, port))
        return sock

    def signal_handler(self, sig, frame):
        try:
            other_peers = [peer for peer in self.peers_in_room 
                        if peer[:2] != self.self_addr[:2]]
            for peer in other_peers:
                message = Olaf.encode_msg(PING, self.self_addr, [], 'bye')
                self.sock.sendto(message, (peer[0],peer[1]))
        except:
            pass
        self.sock.close()
        sys.exit(0)

    def send_ping(self):
        for peer in self.peers_in_room:
            if self.self_addr != peer:
                message = Olaf.encode_msg(PING, self.self_addr, [peer], '')
                self.sock.sendto(message, (peer[0],peer[1]))

    def send_entry_ping(self):
        message = Olaf.encode_msg(ENTRY_PEER, self.self_addr, [], '')
        self.sock.sendto(message, tuple(self.bootstraps[0]))
  
    def send_join_bootstrap(self, room):
        message = Olaf.encode_msg(JOIN_B, [], [], room)
        self.sock.sendto(message, tuple(self.bootstraps[0]))

