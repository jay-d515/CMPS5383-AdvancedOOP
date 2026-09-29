import socket
import time
import threading

class Worker(threading.Thread):
    
    def run(self):
        time.sleep(10)
        print("Thread done it work....")


server_socket = socket.socket(socket.AF_INET,  socket.SOCK_STREAM)
server_socket.bind(("localhost", 5000))
server_socket.listen(1)

for i in range(3):
    print("Waiting for a client: ")
    client, address =  server_socket.accept()
    message = client.recv(2048).decode()

    # the worker take the heavy task and run them
    # in the background so the server keeps 
    # accepting connections
    # when the worker does its work should give it back to the client
    

    # think of a manager accepting orders
    # and the baristas doing the work
    # then serve it when they are done
    w = Worker()
    w.start()

    client.sendall("Hello back for the server!!!".encode())
    client.close()

server_socket.close()