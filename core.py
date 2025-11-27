from peer import Peer
from olaf import Olaf
from network import Network
from msg_types import *
import queue
import time
import sys
import socket

class Core:
    def __init__(self, bootstraps=[['127.0.0.1', 5000], ['127.0.0.1', 5001]]):
        self.bootstraps = bootstraps
        self.app_queue = queue.Queue()
        self.network = Network(bootstraps=bootstraps)
        self.binary = Olaf()        
        self.peer = Peer()
        self.b_count = 0


    def connect(self):
        """Thread que recibe mensajes"""
        while True:
            try:
                message, addr = self.peer.socket_receive()
                msg_type = message[0]
                print(f"Mensaje recibido: {message}")
                
                if msg_type == APP_R: 
                    self.app_queue.put((message, addr))

                elif msg_type == BOOTSTRAP_R: 
                    self.bootstrap_res(message, addr)

                elif msg_type == PING: 
                    self.ping_res(message, addr)

                elif msg_type == ROOM_FULL: # falta implementar logica de room full
                    self.room_full(message, addr)

                else: continue
            
            except socket.timeout:
                # Ignorar timeouts silenciosamente
                continue
            except Exception as e:
                # agregar logging luego
                continue

    def heart(self, room):
        while True:
            self.network.evaluate_state()
            print(self.network.get_state())

            if self.network.purge: 
                print('purgando')
                self.network.delete_inactive()

            if self.network.send_ping: 
                print('enviando ping')
                self.peer.socket_send_all(
                    type=PING, 
                    peers=self.network.get_other_peers(), 
                    payload=''
                )

            if self.network.send_collector:
                print('enviando collector')
                target = self.network.bootstraps[self.b_count]
                self.peer.socket_send(
                    type=PEER_COLLECTOR,
                    payload=room, 
                    target_addr=target
                )

            if self.network.send_join:
                print('enviando join')
                peers = []
                if self.network.self_addr != None:
                    peers = [self.network.self_addr]
                target = self.network.bootstraps[self.b_count]
                self.peer.socket_send(
                    type=JOIN_B, 
                    peers=peers,
                    payload=room,
                    target_addr=target
                )
            time.sleep(3)

    def app_send(self, data):
        if data is None:
            raise ValueError("Data is required")
        self.peer.socket_send_all(type=APP_R, peers=self.network.get_other_peers(), payload=data)

    def app_receive(self):
        message, addr = self.app_queue.get()
        if message is None:
            return ''
        msg_type, peers, payload = message
        return payload

    def signal_handler(self, sig, frame):
        try:
            self.peer.socket_send_all(type=PING, peers=self.network.get_other_peers(), payload='bye')
        except Exception as e:
            print(f"Error al enviar despedida: {e}")
        
        self.peer.socket_close()
        sys.exit(0)

    def bootstrap_res(self, message, addr):
        _ , peers, payload = message
        
        # revisar si se codifica bien el payload
        if self.network.self_addr is None:
            self.network.add_self_addr(payload)

        for peer in peers:
            self.network.add_peer(peer)


    def ping_res(self, message, addr):
        msg_type, peers, payload = message

        if payload == b'bye':
            peer_to_remove = None
            for peer in self.network.get_peers_list():
                if peer[0] == addr[0] and peer[1] == addr[1]:
                    peer_to_remove = peer
                    break
            
            if peer_to_remove:
                self.network.remove_peer(peer_to_remove)
                print(f"Peer {peer_to_remove[2]} removido")
        else:
            # Actualizar/agregar peers
            for peer in peers:
                self.network.add_peer(peer)
                self.network.update_ts(peer)

    def room_full(self, message, addr):
        print(message)

