import socket
from olaf import Olaf

class Peer:
    def __init__(self, ip='0.0.0.0', port=0):
        self.self_addr = [ip, port, 0]
        self.binary = Olaf()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))

    def socket_send(self, message, target_addr):
        message = self.binary.encode_msg(message)
        self.sock.sendto(message, (target_addr[0], target_addr[1]))

    def socket_receive(self):
        data, addr = self.sock.recvfrom(1024)
        return self.binary.decode_msg(data), list(addr)

    def socket_close(self):
        self.sock.close()

