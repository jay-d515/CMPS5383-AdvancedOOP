import socket
import time
import threading

class Worker(threading.Thread):
    def run(self):
        time.sleep(100)
        print("Thread done, it works...")

server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_socket.bind(("localhost", 5000))
server_socket.listen(1)

for i in range(3):
    print("Waiting for a client: ")
    client, address = server_socket.accept()
    message = client.recv(2048).decode()
    
    w = Worker()
    
    w.start()
    
    client.sendall("Hello back from the server!!!".encode())
    client.close
    

server_socket.close()