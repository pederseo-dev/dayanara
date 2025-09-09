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

def handle_peers(sock, room, peers_in_room, bootstraps):
    while True:
        if peers_in_room:  # Ahora será [] (falsy) o [peer1, peer2] (truthy)
            # si hay peers_in_room mandar ping a todos los peer
            for peer in peers_in_room:
                send_message(sock, {'type': 'ping'}, peer)
        else:
            # de lo contrario mandar join_bootstrap hasta que haya peers_in_room  
            send_message(sock, {'type': 'join_bootstrap', 'room': room}, bootstraps[0])
        
        time.sleep(5)

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
        self.peers_in_room = []
        self.own_public_addr = []
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
        retry_thread = threading.Thread(target=handle_peers, args=(self.sock ,room, self.peers_in_room, self.bootstraps), daemon=True)
        retry_thread.start()

        self.handle_messages()

    def handle_messages(self):
        while True:
            # extraer mensajes de la cola
            message, addr = self.listen_queue.get()
            print('mensaje recibido', message)

#-------------------------------------HOST--------------------------------------------#
            if message.get('type') == 'join_bootstrap':
                peer_room = message.get('room')

                if peer_room not in self.room_list:
                    # Primera vez que alguien se une a esta room
                    self.room_list[peer_room] = [addr]
                    message_data = {'type': 'bootstrap_response', 'room': peer_room, 'peers': [], 'public_addr': addr}
                else:
                    # Ya existe la room
                    other_peers = [p for p in self.room_list[peer_room] if p != addr]  # Sin el que se está uniendo
                    
                    # Agregar el nuevo peer a la lista completa del bootstrap
                    if addr not in self.room_list[peer_room]:
                        self.room_list[peer_room].append(addr)
                    
                    # Enviar solo los "otros peers" al que se está uniendo
                    message_data = {'type': 'bootstrap_response', 'room': peer_room, 'peers': other_peers, 'public_addr': addr}

                send_message(self.sock, message_data, addr)

#-------------------------------------JOIN--------------------------------------------#
            elif message.get('type') == 'bootstrap_response':
                room = message.get('room')
                if room is not None:
                    # En lugar de: self.peers_in_room = message.get('peers', [])
                    self.peers_in_room.clear()  # Limpiar la lista existente
                    self.peers_in_room.extend(message.get('peers'))  # Agregar los nuevos peers
                    self.own_public_addr = message.get('public_addr')

            elif message.get('type') == 'clean_room':
                continue

            elif message.get('type') == 'join_room':
                continue

            elif message.get('type') == 'ping':
                print('ping recibido de', addr)
                
                # NUEVO: Verificar si el peer que envía ping está registrado
                if addr not in self.peers_in_room:
                    print(f'Peer desconocido {addr} se agregó automáticamente')
                    self.peers_in_room.append(addr)

            elif message.get('type') == 'peer_response':
                continue

# serializar mensajes antes de enviar
# para que la funcion solo mande bytes            
# ver si es necesario mandar room:peer_room
# modificar funciones send y receiv para manejar datos crudos


# def send_message(sock, message, address):
#     sock.sendto(message, (address[0],address[1]))

# def receive_message(sock):
#     data, address = sock.recvfrom(1024)
#     return data, address