import socket
import threading

class ChatServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.public_keys = {}
        self.running = True
        self.lock = threading.Lock()  # For thread-safe access to shared resources

    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port}")
        try:
            self.accept_clients()
        except KeyboardInterrupt:
            print("Server is shutting down.")
        finally:
            self.shutdown_server()

    def accept_clients(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"New connection from {client_address}")
                if len(self.clients) >= 2:
                    print("Too many clients connected. Disconnecting all clients.")
                    self.disconnect_all_clients()
                    continue
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.daemon = True
                client_thread.start()
            except socket.error:
                if not self.running:
                    break

    def handle_client(self, client_socket):
        client_id = client_socket.getpeername()
        try:
            client_socket.sendall("REQUEST_PUBLIC_KEY".encode('utf-8'))
            public_key_msg = client_socket.recv(4096).decode('utf-8')
            public_key = public_key_msg.split(":", 1)[1]
            with self.lock:
                self.public_keys[client_id] = public_key
                self.clients[client_id] = client_socket
            self.broadcast_peer_public_key(client_socket, client_id)

            while True:
                try:
                    message = client_socket.recv(4096).decode('utf-8')
                    if message == "DISCONNECT":
                        print(f"Client {client_id} disconnected")
                        self.remove_client(client_socket, client_id)
                        break
                    self.route_message(client_id, message)
                except ConnectionResetError:
                    print(f"Client {client_id} reset the connection.")
                    self.remove_client(client_socket, client_id)
                    break
                except socket.error:
                    break
        except Exception as e:
            print(f"Error handling client {client_id}: {e}")
            self.remove_client(client_socket, client_id)
        finally:
            self.remove_client(client_socket, client_id)

    def broadcast_peer_public_key(self, client_socket, client_id):
        with self.lock:
            for other_client_id, other_client_socket in self.clients.items():
                if other_client_id != client_id:
                    try:
                        other_client_socket.sendall(f"PEER_PUBLIC_KEY:{self.public_keys[client_id]}".encode('utf-8'))
                        client_socket.sendall(f"PEER_PUBLIC_KEY:{self.public_keys[other_client_id]}".encode('utf-8'))
                        self.public_keys.clear()
                    except Exception as e:
                        print(f"Error broadcasting public key: {e}")

    def route_message(self, sender_id, message):
        with self.lock:
            for client_id, client_socket in list(self.clients.items()):
                if client_id != sender_id:
                    try:
                        client_socket.sendall(message.encode('utf-8'))
                    except BrokenPipeError:
                        print(f"Client {client_id} has disconnected.")
                        self.remove_client(client_socket, client_id)
                    except Exception as e:
                        print(f"Error routing message: {e}")

    def remove_client(self, client_socket, client_id):
        try:
            client_socket.close()
        except Exception as e:
            print(f"Error closing socket for client {client_id}: {e}")

        with self.lock:
            if client_id in self.clients:
                del self.clients[client_id]
            if client_id in self.public_keys:
                del self.public_keys[client_id]

        self.disconnect_all_clients()

    def notify_disconnection(self, client_id):
        with self.lock:
            for client_socket in list(self.clients.values()):
                try:
                    client_socket.sendall("DISCONNECT".encode('utf-8'))
                except Exception as e:
                    print(f"Error notifying disconnection: {e}")

    def disconnect_all_clients(self):
        with self.lock:
            for client_socket in list(self.clients.values()):
                try:
                    client_socket.sendall("DISCONNECT".encode('utf-8'))
                    client_socket.close()
                except Exception as e:
                    print(f"Error disconnecting client: {e}")
            self.clients.clear()
            self.public_keys.clear()
            print("All clients have been disconnected. Waiting for new connections...")

    def shutdown_server(self):
        self.running = False
        self.disconnect_all_clients()
        try:
            self.server_socket.close()
        except Exception as e:
            print(f"Error closing server socket: {e}")

def main():
    host = '192.168.1.204'
    port = 7004
    server = ChatServer(host, port)
    server.start_server()

if __name__ == '__main__':
    main()
