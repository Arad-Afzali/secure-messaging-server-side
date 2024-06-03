# server.py
import socket
import threading

class ChatServer:
    def __init__(self, host='192.168.1.204', port=7001):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = []

    def broadcast(self, message, client_socket):
        for client in self.clients:
            if client != client_socket:
                try:
                    client.sendall(message)
                except Exception as e:
                    print(f"Error broadcasting message: {e}")
                    client.close()
                    self.clients.remove(client)

    def handle_client(self, client_socket):
        try:
            # Exchange public keys
            peer_public_key = client_socket.recv(4096)
            print(f"Received public key from client: {peer_public_key[:30]}...")
            for client in self.clients:
                if client != client_socket:
                    client.sendall(peer_public_key)

            self.clients.append(client_socket)

            while True:
                message = client_socket.recv(4096)
                if not message:
                    break
                print(f"Received message from client: {message[:30]}...")
                self.broadcast(message, client_socket)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
            self.clients.remove(client_socket)

    def start(self):
        print("Server started...")
        while True:
            client_socket, addr = self.server.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    server = ChatServer()
    server.start()
