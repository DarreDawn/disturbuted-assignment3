import socket
import threading

def receive_message(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            print(message)
        except:
            print("You have been disconnected.")
            sock.close()
            break

nickname = input("Choose your nickname: ")
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 12345))
client.send(nickname.encode())

thread = threading.Thread(target=receive_message, args=(client,))
thread.start()

while True:
    message = input('')
    if message == "/quit":
        client.send("/quit".encode())
        client.close()
        break
    client.send(message.encode())
