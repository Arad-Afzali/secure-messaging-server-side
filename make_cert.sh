#!/bin/sh
# Makes a self-signed certificate for testing on this machine.
# Give server.crt to the clients (it has no secret in it). Keep server.key on the server.
# For a real server, change 127.0.0.1 to its IP or domain name.
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout server.key -out server.crt \
  -subj "/CN=127.0.0.1" \
  -addext "subjectAltName=IP:127.0.0.1,DNS:localhost"
