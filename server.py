import socket
import threading

class ChatServer:
    def __init__(self, host='192.168.1.204', port=7001):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.clients = {}
        self.public_keys = {}
        self.lock = threading.Lock()

    def handle_client(self, client_socket, addr):
        try:
            while True:
                message = client_socket.recv(4096)
                if not message:
                    break

                if message.startswith(b'KEY:'):
                    with self.lock:
                        self.public_keys[addr] = message[4:]
                    print(f"Received public key from {addr}: {message[4:30]}...")

                elif message == b'REQ_KEY':
                    with self.lock:
                        peer_addr = next((a for a in self.public_keys if a != client_socket.getpeername()), None)
                        if peer_addr:
                            peer_public_key = self.public_keys.pop(peer_addr)
                            client_socket.sendall(peer_public_key)
                            print(f"Sent and removed public key of {peer_addr} to {addr}: {peer_public_key[:30]}...")
                        else:
                            print(f"No public key available to send to {addr}")

                else:
                    with self.lock:
                        for client in self.clients.values():
                            if client != client_socket:
                                client.sendall(message)
                                print(f"Broadcasting message to {client.getpeername()}: {message[:30]}...")

        except socket.error as e:
            if e.errno == 9:  # Bad file descriptor
                print(f"Client {addr} disconnected.")
            else:
                print(f"Error handling client {addr}: {e}")
        finally:
            with self.lock:
                client_socket.close()
                if addr in self.clients:
                    del self.clients[addr]
                self.public_keys.pop(addr, None)
            print(f"Connection with {addr} closed.")

            # Close the remaining client if there is any
            if self.clients:
                print("A client disconnected, closing the remaining client.")
                for client in list(self.clients.values()):
                    client.close()
                self.clients.clear()
                self.public_keys.clear()

    def close_all_connections(self):
        with self.lock:
            for client_socket in list(self.clients.values()):
                client_socket.close()
            self.clients.clear()
            self.public_keys.clear()
            print("All connections closed.")

    def start(self):
        print("Server started...")
        while True:
            if len(self.clients) < 3:
                client_socket, addr = self.server.accept()
                with self.lock:
                    self.clients[addr] = client_socket
                print(f"Connection from {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            else:
                print("Maximum number of clients connected. Closing all connections.")
                self.close_all_connections()
                print("Server listening for new connections...")

if __name__ == "__main__":
    server = ChatServer()
    server.start()
