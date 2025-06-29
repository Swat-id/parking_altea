import socket

def send_packet(host: str, port: int, packet: bytes, timeout=5):
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(packet)
        try:
            response = sock.recv(1024)
            return response
        except socket.timeout:
            return None
