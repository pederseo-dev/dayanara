import socket
import json
import queue
import threading
import time

# cadena de custodia/confirmación:
# los peers nuevos se encargan de la limpieza del boostrap

def create_udp_socket(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((ip, port))
    return sock

def send_message(sock, message, address):
    if isinstance(address, list): # convertir lista a tupla para el socket UDP
        address = tuple(address)
    data = json.dumps(message).encode() # convertir a binario
    sock.sendto(data, address)


def receive_message(sock):
    data, address = sock.recvfrom(1024)
    message = json.loads(data.decode()) # convertir a texto
    return message, list(address) # convertir a lista para usar mismo formato

def listen_messages(sock, listen_queue):
    while True:
        try:
            message, address = receive_message(sock)
            listen_queue.put((message, address))
            print(message)
                
        except Exception as e:
            return e

def find_peers(sock, room, peers_in_room, bootstraps):
    while True:
        peers = peers_in_room.get(room, [])
        if peers:
            return
        try:
            send_message(sock, {'type': 'join_bootstrap', 'room': room}, bootstraps[0])
        except Exception:
            pass
        time.sleep(1)

# ____________________________________________________________________________________________________________
class Dayanara:
    def __init__(self, timeout=5, size=10, ip='', port=0):
    # --- PARA CUANDO ACTÚA COMO HOST ---
        self.room_list = {}  # {"gaming": ["192.168.1.100:5000", "10.0.0.5:6000"], "chat": ["1.2.3.4:7000"]}
        self.timeout = timeout # no se usa aun
        self.size = size # tamano de la lista (no se usa aun)
        self.listen_queue = queue.Queue()
        self.app_queue = queue.Queue()
        
    # --- PARA CUANDO ACTÚA COMO CLIENTE ---
        self.bootstraps = [['127.0.0.1', 5000]] # lista de boostraps publicos activos
        self.peers_in_room = {}
        self.own_public_addr = {}
        self.sock = create_udp_socket(ip, port)
        
    # ------ METHODS ----- #
    def host(self):
        ''' Metodo que maneja los join peers que quieren conectarse a una sala'''
        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        print('escuchando peers')
        listener = threading.Thread(target=listen_messages,args=(self.sock,self.listen_queue), daemon=True)
        listener.start()
        
        # si bootstrap responde exist
        self.handle_messages()

    
    def join(self, room):
        ''' Metodo para crear peer y conecatrse a una sala'''
        if not room:
            print('error')

        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        print('esperando mensajes entrantes')
        listener = threading.Thread(target=listen_messages,args=(self.sock,self.listen_queue), daemon=True)
        listener.start()
        # reintentos básicos de join_bootstrap en segundo plano
        retry_thread = threading.Thread(target=find_peers, args=(self.sock ,room, self.peers_in_room, self.bootstraps), daemon=True)
        retry_thread.start()

        self.handle_messages()

    def handle_messages(self):
        while True:
            # extraer mensajes de la cola
            message, addr = self.listen_queue.get()
            print('mensaje recibido', message)

            # si el boostrap recibe join_boostrap responde si existe o no la sala
            if message.get('type') == 'join_bootstrap':
                peer_room = message.get('room')

                # si no no existe la sala manda false y agrega sala a room_list
                if peer_room not in self.room_list:
                    self.room_list[peer_room] = [addr]
                    message_data = {'type': 'bootstrap_response', 'room': peer_room, 'exist': False, 'peers': [], 'public_addr': addr}
                    
                # si existe la sala pasa la lista con los peer
                else:
                    other_peers = [p for p in self.room_list[peer_room] if p != addr]
                    if addr not in self.room_list[peer_room]:
                        self.room_list[peer_room].append(addr)
                        message_data = {'type': 'bootstrap_response', 'room': peer_room, 'exist': True, 'peers': other_peers, 'public_addr': addr}

                send_message(self.sock, message_data, addr)

            # si el peer recibe la respuesta del bootstrap:
            elif message.get('type') == 'bootstrap_response':
                room = message.get('room')
                # si la sala a la que intentamos unirnos esta vacia
                if room is not None:
                    self.peers_in_room[room] = message.get('peers', [])
                    self.own_public_addr[room] = message.get('public_addr', [])

            elif message.get('type') == 'clean_room':
                continue

            elif message.get('type') == 'join_room':
                continue

            elif message.get('type') == 'keep_alive':
                send_message(self.sock, {'type': 'pong'}, addr)

            elif message.get('type') == 'peer_response':
                continue

            
















    # def send(self, message):

    #     if not self.sock:
    #         raise RuntimeError("Socket no inicializado. Llama a join() primero.")
    #     for addresses in self.peers_in_room.values():
    #         for address in addresses:
    #             send_message(self.sock, message, tuple(address))

    # def receive(self):
    #     message = receive_message(self.sock)
    #     return message