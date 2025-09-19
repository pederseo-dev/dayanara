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

def listen_messages(sock, listen_queue, app_queue):
    while True:
        try:
            data, address = sock.recvfrom(1024)
            message = Olaf.decode_msg(data)
            addr = list(address)
            
            # Filtrar por tipo de mensaje
            if message[0] == APP_R:
                # Mensajes de aplicación van a app_queue
                app_queue.put((message[3], addr))  # payload + dirección
            else:
                # Mensajes de protocolo van a listen_queue
                listen_queue.put((message, addr))
                
            print(message)
                
        except Exception as e:
            print(e)

def handle_peers(sock, room, peers_in_room, bootstraps):
    while True:
        if peers_in_room:  # Ahora será [] (falsy) o [peer1, peer2] (truthy)
            # si hay peers_in_room mandar ping a todos los peer
            for peer in peers_in_room:
                message = Olaf.encode_msg(PING, ["0.0.0.0", 0], [], '')
                sock.sendto(message, tuple(peer))
        else:
            # de lo contrario mandar join_bootstrap hasta que haya peers_in_room
            message = Olaf.encode_msg(JOIN_B, ["0.0.0.0", 0], [], room)
            sock.sendto(message, tuple(bootstraps[0]))
        
        time.sleep(5)

class Dayanara:
    def __init__(self, timeout=5, size=10, ip='', port=0):
    # --- PARA CUANDO ACTÚA COMO HOST ---
        self.room_list = {}  # {"gaming": ["192.168.1.100:5000", "10.0.0.5:6000"], "chat": ["1.2.3.4:7000"]}
        self.timeout = timeout # no se usa aun
        self.size = size # tamano de la lista (no se usa aun)
        self.listen_queue = queue.Queue()
        self.app_queue = queue.Queue() # no se usa aun
        
    # --- PARA CUANDO ACTÚA COMO CLIENTE ---
        self.bootstraps = [['127.0.0.1', 5000]] # lista de boostraps publicos activos
        self.peers_in_room = []
        self.own_public_addr = []
        self.sock = create_udp_socket(ip, port)
        
    # ------ METHODS ----- #
    def host(self):
        ''' Metodo que maneja los join peers que quieren conectarse a una sala'''
        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        print('escuchando peers')
        listener = threading.Thread(target=listen_messages,args=(self.sock,self.listen_queue, self.app_queue), daemon=True)
        listener.start()
        
        # si bootstrap responde exist
        self.handle_messages()

    
    def join(self, room):
        ''' Metodo para crear peer y conecatrse a una sala'''
        if not room:
            print('error')

        # hilo que escucha y guarda en cola todos los mensaje esntrantes
        print('esperando mensajes entrantes')
        listener = threading.Thread(target=listen_messages,args=(self.sock,self.listen_queue,self.app_queue), daemon=True)
        listener.start()
        # reintentos básicos de join_bootstrap en segundo plano
        retry_thread = threading.Thread(target=handle_peers, args=(self.sock ,room, self.peers_in_room, self.bootstraps), daemon=True)
        retry_thread.start()

        self.handle_messages()

    def send(self, data):
        ''' Metodo para enviar data a todos los peers'''
        for peer in self.peers_in_room:
            message = Olaf.encode_msg(APP_R, ["0.0.0.0", 0], [], data)
            self.sock.sendto(message, tuple(peer))
    
    def receive(self):
        data = self.app_queue.get()
        return data

    def handle_messages(self):
        while True:
            # extraer mensajes de la cola
            message, addr = self.listen_queue.get()
            print('mensaje recibido', message)

    

#-------------------------------------HOST--------------------------------------------#
            if message[0] == JOIN_B:
                peer_room = message[3]

                if peer_room not in self.room_list:
                    # Primera vez que alguien se une a esta room
                    self.room_list[peer_room] = [addr]
                    message_data = Olaf.encode_msg(BOOTSTRAP_R, addr, [], peer_room)

                else:
                    # Ya existe la room
                    other_peers = [p for p in self.room_list[peer_room] if p != addr]  # Sin el que se está uniendo

                    # Agregar el nuevo peer a la lista completa del bootstrap
                    if addr not in self.room_list[peer_room]:
                        self.room_list[peer_room].append(addr)

                    # Enviar solo los "otros peers" al que se está uniendo
                    message_data = Olaf.encode_msg(BOOTSTRAP_R, addr, other_peers, peer_room)

                self.sock.sendto(message_data, (addr[0],addr[1]))

#-------------------------------------JOIN--------------------------------------------#
            elif message[0] == BOOTSTRAP_R:
                room = message[3]
                if room is not None:
                    # En lugar de: self.peers_in_room = message.get('peers', [])
                    self.peers_in_room.clear()  # Limpiar la lista existente
                    self.peers_in_room.extend(message[2])  # Agregar los nuevos peers
                    self.own_public_addr = message[1]

            elif message[0] == PING:  
                # NUEVO: Verificar si el peer que envía ping está registrado
                if addr not in self.peers_in_room:
                    print(f'Peer desconocido {addr} se agregó automáticamente')
                    self.peers_in_room.append(addr)
