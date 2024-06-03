# server.py
import socket
import threading

class ChatServer:
    def __init__(self, host='127.0.0.1', port=7001):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((host, port))
        self.server.listen()
        self.clients = []

    def start(self):
        print("Server started, waiting for connections...")
        while True:
            client_socket, client_address = self.server.accept()
            print(f"Connection from {client_address}")
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()

    def handle_client(self, client_socket):
        rsa_public_key = client_socket.recv(4096)
        self.clients.append((client_socket, rsa_public_key))

        while True:
            try:
                message = client_socket.recv(4096)
                if message:
                    self.broadcast(message, client_socket)
                else:
                    self.clients.remove((client_socket, rsa_public_key))
                    client_socket.close()
                    break
            except Exception as e:
                print(f"Error handling client: {e}")
                self.clients.remove((client_socket, rsa_public_key))
                client_socket.close()
                break

    def broadcast(self, message, from_socket):
        for client_socket, _ in self.clients:
            if client_socket != from_socket:
                client_socket.sendall(message)

if __name__ == "__main__":
    server = ChatServer()
    server.start()
