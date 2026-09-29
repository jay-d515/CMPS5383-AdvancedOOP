import socket

client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

client_socket.connect(("localhost", 5000))

message = "Hello"
client_socket.sendall(message.encode())

message = client_socket.recv(2048).decode()
print(message)
client_socket.close()