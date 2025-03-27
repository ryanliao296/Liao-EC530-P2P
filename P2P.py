import argparse
import requests
import socket
import threading
import time
import json
from flask import Flask, request, jsonify
from cryptography.fernet import Fernet

# Discovery Server Setup
app = Flask(__name__)
discovered_users = {}
blocked_users = {}
muted_users = {}
KEEP_ALIVE_INTERVAL = 30

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    user_id = data['user_id']
    ip = data['ip']
    port = data['port']
    discovered_users[user_id] = {'ip': ip, 'port': port, 'last_seen': time.time()}
    return jsonify({'message': 'User registered'}), 200

@app.route('/discover', methods=['GET'])
def discover():
    active_users = {k: v for k, v in discovered_users.items() if time.time() - v['last_seen'] < KEEP_ALIVE_INTERVAL}
    return jsonify(active_users)

@app.route('/keep_alive', methods=['POST'])
def keep_alive():
    data = request.json
    user_id = data['user_id']
    if user_id in discovered_users:
        discovered_users[user_id]['last_seen'] = time.time()
    return jsonify({'message': 'Keep-alive received'})

class P2PClient:
    def __init__(self, user_id, host, port, discovery_server):
        self.user_id = user_id
        self.host = host
        self.port = port
        self.discovery_server = discovery_server
        self.peers = {}
        self.blocked_users = set()
        self.muted_users = set()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(5)
        print(f"Listening on {host}:{port}")
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        threading.Thread(target=self.keep_alive_periodically, daemon=True).start()

    def discover_peers(self):
        response = requests.get(f"{self.discovery_server}/discover")
        active_users = response.json()
        for peer_id, peer_info in active_users.items():
            if peer_id != self.user_id and peer_id not in self.peers:
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect((peer_info['ip'], peer_info['port']))
                self.peers[peer_id] = peer_socket
                print(f"Connected to {peer_id}")

    def keep_alive_periodically(self):
        while True:
            time.sleep(KEEP_ALIVE_INTERVAL)
            self.send_keep_alive()

    def send_keep_alive(self):
        data = {"user_id": self.user_id}
        requests.post(f"{self.discovery_server}/keep_alive", json=data)

    def send_message(self, peer_id, message):
        if peer_id in self.blocked_users:
            print(f"Cannot send message. You have blocked {peer_id}.")
            return

        if peer_id in self.peers:
            formatted_message = f"{self.user_id}:{message}"  # Ensure correct format
            try:
                self.peers[peer_id].send(formatted_message.encode())
                print(f"Message sent to {peer_id}: {message}")
            except Exception as e:
                print(f"Failed to send message to {peer_id}: {e}")
        else:
            print(f"Peer {peer_id} not connected.")


    def listen_for_messages(self):
        while True:
            conn, addr = self.socket.accept()
            threading.Thread(target=self.handle_connection, args=(conn,)).start()

    def handle_connection(self, conn):
        data = conn.recv(1024).decode()
        if not data:
            return  # Handle the case where no data is received
        
        if ':' not in data:
            print(f"Received malformed message: {data}")
            return  # Ignore improperly formatted messages

        sender, message = data.split(':', 1)

        # Blocked user check
        if sender in self.blocked_users:
            print(f"Message received from blocked user {sender}. Ignoring message.")
            return  # Block the message silently, but print a message

        # Muted user check
        if sender in self.muted_users:
            return  # Silently ignore message

        print(f"{sender}: {message}")

    def block_user(self, peer_id):
        if peer_id not in self.blocked_users:
            self.blocked_users.add(peer_id)
            print(f"Blocked {peer_id}. Blocked list: {self.blocked_users}")
        else:
            print(f"{peer_id} is already blocked.")

    def unblock_user(self, peer_id):
        if peer_id in self.blocked_users:
            self.blocked_users.remove(peer_id)
            print(f"Unblocked {peer_id}. Current blocked list: {self.blocked_users}")
            
            # Ensure the connection is active or re-establish it if necessary
            if peer_id not in self.peers:
                self.reconnect_peer(peer_id)
        else:
            print(f"{peer_id} was not blocked. Blocked list: {self.blocked_users}")

    def reconnect_peer(self, peer_id):
        """Re-establish connection to the peer if they were previously blocked."""
        peer_info = discovered_users.get(peer_id)
        if peer_info:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                peer_socket.connect((peer_info['ip'], peer_info['port']))
                self.peers[peer_id] = peer_socket
                print(f"Reconnected to {peer_id}")
            except Exception as e:
                print(f"Failed to reconnect to {peer_id}: {e}")
        else:
            print(f"Could not find peer {peer_id} for reconnection.")

    def mute_user(self, peer_id):
        """Mute the user so their messages are silently ignored."""
        if peer_id not in self.muted_users:
            self.muted_users.add(peer_id)
            print(f"Muted {peer_id}. Mute list: {self.muted_users}")

            if peer_id not in self.peers:
                self.reconnect_peer(peer_id)
        else:
            print(f"{peer_id} is already muted.")

    
    def unmute_user(self, peer_id):
        """Unmute the user so their messages are no longer ignored."""
        if peer_id in self.muted_users:
            self.muted_users.remove(peer_id)
            print(f"Unmuted {peer_id}. Mute list: {self.muted_users}")
        else:
            print(f"{peer_id} was not muted. Mute list: {self.muted_users}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P Chat Client")
    parser.add_argument("--user_id", required=True, help="Unique username")
    parser.add_argument("--port", type=int, required=True, help="Port number")
    args = parser.parse_args()

    if args.user_id == "server":
        app.run(host="0.0.0.0", port=5000, threaded=True)
    else:
        client = P2PClient(args.user_id, "127.0.0.1", args.port, "http://127.0.0.1:5000")
        requests.post("http://127.0.0.1:5000/register", json={"user_id": args.user_id, "ip": "127.0.0.1", "port": args.port})
        while True:
            cmd = input("Enter command: ")
            if cmd.startswith("/msg"):
                _, peer_id, message = cmd.split(" ", 2)
                client.send_message(peer_id, message)
            elif cmd == "/discover":
                client.discover_peers()
            elif cmd.startswith("/block"):
                _, peer_id = cmd.split(" ")
                client.block_user(peer_id)
            elif cmd.startswith("/unblock"):
                _, peer_id = cmd.split(" ")
                client.unblock_user(peer_id)
            elif cmd.startswith("/mute"):
                _, peer_id = cmd.split(" ")
                client.mute_user(peer_id)
            elif cmd.startswith("/unmute"):
                _, peer_id = cmd.split(" ")
                client.unmute_user(peer_id)
            elif cmd == "/exit":
                break
