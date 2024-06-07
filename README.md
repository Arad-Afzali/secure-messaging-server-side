# Secure Chat Server

This is a simple secure chat server implemented in Python. It allows two clients to connect, exchange public keys for secure communication, and send messages to each other. 

## Features

- Supports up to two clients.
- Exchanges public keys for secure communication.
- Routes messages between clients.
- Disconnects all clients when more than two clients attempt to connect.

## Requirements

- Python 3.x
- `openssl` (for SSL/TLS support, optional)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/chat-server.git
cd chat-server
```

2. (Optional but Recommended) Generate SSL/TLS certificates.

## Usage

1. Start the server:

```bash
python3 server.py
```

2. Connect clients to the server using a the client application.

3. SSL/TLS Support (Optional but Recommended)

To enable SSL/TLS support, uncomment the relevant sections in the ChatServer class and provide the paths to your certificate and key files:

```bash
#uncomment these sections in the code:

self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
self.context.load_cert_chain(certfile='server.crt', keyfile='server.key')

#---------

client_socket = self.context.wrap_socket(client_socket, server_side=True)

```
## Contributing

Contributions are welcome! Please open an issue or submit a pull request.




