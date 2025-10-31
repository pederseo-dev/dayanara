import socket

class Peer:
    def __init__(self, ip='0.0.0.0', port=0):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))

    def socket_send(self, message, target_addr):
        self.sock.sendto(message, (target_addr[0], target_addr[1]))

    def socket_receive(self):
        return self.sock.recvfrom(1024)

    def socket_close(self):
        self.sock.close()

