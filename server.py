import ssl
import socket
import argparse
import threading
from protocol import send_msg, recv_msg

class ChatServer:
    def __init__(self, host, port, certfile=None, keyfile=None):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.public_keys = {}
        self.running = True
        self.lock = threading.RLock()  # RLock: route_message calls remove_client while holding it

        # TLS is used when a certificate is given (see make_cert.sh)
        self.context = None
        if certfile and keyfile:
            self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.context.load_cert_chain(certfile=certfile, keyfile=keyfile)


    def start_server(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server started on {self.host}:{self.port} ({'TLS' if self.context else 'no TLS'})")
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

                if self.context:
                    try:
                        client_socket = self.context.wrap_socket(client_socket, server_side=True)
                    except ssl.SSLError as e:
                        print(f"TLS handshake failed: {e}")
                        client_socket.close()
                        continue

                # Only two people per chat. A third client is turned away,
                # the two already chatting are not affected.
                with self.lock:
                    full = len(self.clients) >= 2
                if full:
                    print("Chat is full. Rejecting new client.")
                    try:
                        send_msg(client_socket, "DISCONNECT")
                    except socket.error:
                        pass
                    client_socket.close()
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
            # The server only passes keys and messages along. It cannot read
            # them, and the clients' safety code shows if it swaps keys.
            send_msg(client_socket, "REQUEST_PUBLIC_KEY")
            public_key_msg = recv_msg(client_socket)
            if not public_key_msg.startswith("PUBLIC_KEY:"):
                raise ValueError("Expected a public key")
            public_key = public_key_msg.split(":", 1)[1]
            with self.lock:
                self.public_keys[client_id] = public_key
                self.clients[client_id] = client_socket
            self.broadcast_peer_public_key(client_socket, client_id)

            while True:
                try:
                    message = recv_msg(client_socket)
                    if message == "DISCONNECT":
                        print(f"Client {client_id} disconnected")
                        self.remove_client(client_socket, client_id)
                        break
                    self.route_message(client_id, message)
                except ConnectionResetError:
                    print(f"Client {client_id} reset the connection.")
                    self.remove_client(client_socket, client_id)
                    break
                except (socket.error, ConnectionError):
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
                        send_msg(other_client_socket, f"PEER_PUBLIC_KEY:{self.public_keys[client_id]}")
                        send_msg(client_socket, f"PEER_PUBLIC_KEY:{self.public_keys[other_client_id]}")
                        self.public_keys.clear()
                    except Exception as e:
                        print(f"Error broadcasting public key: {e}")

    def route_message(self, sender_id, message):
        with self.lock:
            for client_id, client_socket in list(self.clients.items()):
                if client_id != sender_id:
                    try:
                        send_msg(client_socket, message)
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
                    send_msg(client_socket, "DISCONNECT")
                except Exception as e:
                    print(f"Error notifying disconnection: {e}")

    def disconnect_all_clients(self):
        with self.lock:
            if not self.clients:
                return  # already done by the other client's thread
            for client_socket in list(self.clients.values()):
                try:
                    send_msg(client_socket, "DISCONNECT")
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
    parser = argparse.ArgumentParser(description="Secure chat server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7004)
    parser.add_argument("--cert", help="TLS certificate file, e.g. server.crt")
    parser.add_argument("--key", help="TLS private key file, e.g. server.key")
    args = parser.parse_args()

    server = ChatServer(args.host, args.port, args.cert, args.key)
    server.start_server()

if __name__ == '__main__':
    main()
