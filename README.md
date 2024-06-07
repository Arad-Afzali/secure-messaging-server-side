# Secure Chat Server

This is a simple secure chat server implemented in Python. It allows two clients to connect, exchange public keys for secure communication, and send messages to each other. 

## Client Application

The client application is necessary to connect to this secure chat server. You can find the client application repository and instructions on how to set it up below:

https://github.com/Arad-Afzali/secure-messaging-client-side

Please follow the installation and usage instructions in the client application's README to ensure proper communication with the server.


## Features

- Supports two clients.
- Exchanges public keys for secure communication and removes them immediately when they are not needed.
- Routes messages between clients (note: the server does not have access to the messages as they are encrypted by the clients).
- Disconnects all clients when more than two clients attempt to connect.

## Requirements

- Python 3.x
- `openssl` (for SSL/TLS support, Optional but Recommended)

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/Arad-Afzali/secure-messaging-server-side.git
    cd secure-messaging-server-side
    ```

### Note (Optional but Recommended Steps)

2. **Generate SSL/TLS certificates**:

    ```bash
    # Generate a new RSA private key
    openssl genrsa -out server.key 4096

    # Generate a Certificate Signing Request (CSR)
    openssl req -new -key server.key -out server.csr

    # Generate a self-signed SSL certificate
    openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
    ```
3. **SSL/TLS Support**

    To enable SSL/TLS support, first you should uncomment the relevant sections in the ChatServer class and provide the paths to your certificate and key files:

    ```bash
    #uncomment these sections in the code:

    self.context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    self.context.load_cert_chain(certfile='server.crt', keyfile='server.key')

    #---------

    client_socket = self.context.wrap_socket(client_socket, server_side=True)

    ```
## Usage

1. **Start the server**:

    ```bash
    python3 server.py
    ```

    ### Note
    
    You should change the IP address and port in the server.py. The default IP address in 127.0.0.1 and the default port is 7004.

2. **Connect clients to the server using the client application.**

    
## Contributing

Contributions are welcome! Please open an issue or submit a pull request.




