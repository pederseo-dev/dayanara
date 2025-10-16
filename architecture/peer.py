import socket
class UDP_socket:
    def __init__(self, ip='0.0.0.0', port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))

    def send(self, message, target_addr):
        self.sock.sendto(message, (target_addr[0], target_addr[1]))

    def receive(self):
        data, addr = self.sock.recvfrom(1024)
        return data, addr

