import socket
import threading

clients = []
channels = {}
nickname_to_conn = {}

def remove_client(conn, nickname, current_channel):
    broadcast_all(f"{nickname} has left the server.", "Server")
    if current_channel and conn in channels[current_channel]:
        channels[current_channel].remove(conn)
        broadcast(f"{nickname} has left {current_channel}", "\nServer", current_channel)
    if conn in clients:
        clients.remove(conn)
    if nickname in nickname_to_conn:
        del nickname_to_conn[nickname]
    conn.close()



def client_channel_thread(conn, addr):
    nickname = ''
    while True:
        nickname = conn.recv(1024).decode().strip()
        if nickname in nickname_to_conn:
            conn.send("Nickname already taken, please choose another.".encode())
        else:
            conn.send(f"Nickname '{nickname}' is available. You have joined the server!".encode())
            nickname_to_conn[nickname] = conn
            clients.append(conn)
            break

    conn.send(
        "Available channels: general, news, sports. \nType: '/join channel_name' to join a channel. \nType: '/leave' to leave current channel. \nType: '/whisper nickname <message>' to send private massage.\nType: '/quit' to leave the server.".encode())
    current_channel = None

    try:
        while True:
            message = conn.recv(1024).decode().strip()
            if message == '/quit':
                conn.send("You are leaving the chat. Goodbye!".encode())
                break
            elif message.startswith('/join '):
                _, channel_name = message.split(maxsplit=1)
                if current_channel:
                    channels[current_channel].remove(conn)
                current_channel = channel_name
                channels.setdefault(channel_name, []).append(conn)
                conn.send(f"Joined channel {channel_name}".encode())
                broadcast(f"{nickname} has joined {channel_name}", " Server", channel_name)
            elif message == '/leave':
                if current_channel:
                    channels[current_channel].remove(conn)
                    conn.send(f"Left channel {current_channel}".encode())
                    current_channel = None
                    broadcast(f"{nickname} has left {channel_name}", " Server", channel_name)
                else:
                    conn.send("You are not in a channel.".encode())
            elif message.startswith('/whisper '):
                _, target_nickname, *whisper_message = message.split(maxsplit=2)
                whisper_message = " ".join(whisper_message)
                send_whisper(conn, whisper_message, nickname, target_nickname)
            elif current_channel:
                broadcast(message, nickname, current_channel)
            else:
                broadcast_all(message, nickname)
    finally:
        remove_client(conn, nickname, current_channel)



def send_whisper(sender_conn, message, sender_nickname, target_nickname):
    target_conn = nickname_to_conn.get(target_nickname)
    if target_conn:
        print(f"Found connection for {target_nickname}")
        try:
            target_conn.send(f"Private massage from {sender_nickname}: {message}".encode())
        except Exception as e:
            print(f"Error sending whisper to {target_nickname}: {e}")
            target_conn.close()
            if target_conn in clients:
                clients.remove(target_conn)
            if target_nickname in nickname_to_conn:
                del nickname_to_conn[target_nickname]
            sender_conn.send(f"Failed to send message to {target_nickname}. User may have disconnected.".encode())
    else:
        sender_conn.send(f"User {target_nickname} not found.".encode())

def broadcast_all(message, nickname):
    for client in clients:
        try:
            client.send(f"{nickname}: {message}".encode())
        except:
            client.close()
            clients.remove(client)
            for channel in channels.values():
                if client in channel:
                    channel.remove(client)
            if nickname in nickname_to_conn:
                del nickname_to_conn[nickname]


def broadcast(message, nickname, channel_name):
    for client in channels[channel_name]:
        try:
            client.send(f"{nickname}: {message}".encode())
        except:
            client.close()
            channels[channel_name].remove(client)
            if client in clients:
                clients.remove(client)

try:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 12345))
    server.listen()
    print("Server is listening...")

    while True:
        conn, addr = server.accept()
        if conn not in clients:
            clients.append(conn)
        thread = threading.Thread(target=client_channel_thread, args=(conn, addr))
        thread.start()
except KeyboardInterrupt:
    print("\nServer is shutting down...")
    for conn in clients:
        conn.close()
    server.close()
    print("Server shutdown complete.")
