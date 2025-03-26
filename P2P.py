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

@app.route('/block', methods=['POST'])
def block_user():
    data = request.json
    user_id = data['user_id']
    block_id = data['block_id']
    blocked_users[user_id] = blocked_users.get(user_id, set())
    blocked_users[user_id].add(block_id)
    return jsonify({'message': f'User {block_id} blocked'}), 200

@app.route('/mute', methods=['POST'])
def mute_user():
    data = request.json
    user_id = data['user_id']
    mute_id = data['mute_id']
    duration = data.get('duration', 60)  # Default mute time: 60 seconds
    muted_users[user_id] = muted_users.get(user_id, {})
    muted_users[user_id][mute_id] = time.time() + duration
    return jsonify({'message': f'User {mute_id} muted for {duration} seconds'}), 200

@app.route('/block/<user_id>', methods=['GET'])
def get_blocked_users(user_id):
    return jsonify(blocked_users.get(user_id, []))

@app.route('/mute/<user_id>', methods=['GET'])
def get_muted_users(user_id):
    return jsonify(muted_users.get(user_id, {}))

class P2PClient:
    def __init__(self, user_id, host, port, discovery_server):
        self.user_id = user_id
        self.host = host
        self.port = port
        self.discovery_server = discovery_server
        self.peers = {}
        self.encryption_keys = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((host, port))
        self.socket.listen(5)
        print(f"Listening on {host}:{port}")
        threading.Thread(target=self.listen_for_messages, daemon=True).start()
        threading.Thread(target=self.keep_alive_periodically, daemon=True).start()

    def discover_peers(self):
        try:
            # Request the list of active users from the discovery server
            response = requests.get(f"{self.discovery_server}/discover")
            active_users = response.json()
            print(f"Discovered active users: {active_users}")
            
            for peer_id, peer_info in active_users.items():
                if peer_id != self.user_id:
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.connect((peer_info['ip'], peer_info['port']))
                    self.peers[peer_id] = {'socket': peer_socket}
                    print(f"Connected to {peer_id} at {peer_info['ip']}:{peer_info['port']}")
                    
                    # After connecting, send encryption key to peer
                    encryption_key = Fernet.generate_key()
                    self.encryption_keys[peer_id] = encryption_key
                    peer_socket.send(encryption_key)
                    print(f"Sent encryption key to {peer_id}")

        except requests.exceptions.RequestException as e:
            print(f"Failed to discover peers: {e}")

    def keep_alive_periodically(self):
        while True:
            time.sleep(KEEP_ALIVE_INTERVAL)
            self.send_keep_alive()

    def send_keep_alive(self):
        data = {"user_id": self.user_id}
        try:
            response = requests.post(f"{self.discovery_server}/keep_alive", json=data)
            print("Keep-alive sent", response.json())
        except requests.exceptions.RequestException as e:
            print(f"Failed to send keep-alive: {e}")

    def encrypt_message(self, message, key):
        f = Fernet(key)
        return f.encrypt(message.encode())

    def decrypt_message(self, encrypted_message, key):
        f = Fernet(key)
        return f.decrypt(encrypted_message).decode()

    def send_message(self, peer_id, message):
        print(f"Preparing to send message to {peer_id}: {message}")
        if peer_id in self.peers:
            if peer_id in blocked_users.get(self.user_id, set()):
                print(f"Message blocked: You have blocked {peer_id}")
                return
            
            if peer_id in muted_users.get(self.user_id, {}) and time.time() < muted_users[self.user_id][peer_id]:
                print(f"Message muted: You will not receive messages from {peer_id} for now")
                return

            peer_info = self.peers[peer_id]
            key = self.encryption_keys.get(peer_id)
            if not key:
                key = Fernet.generate_key()
                self.encryption_keys[peer_id] = key
                print(f"Generated new encryption key for {peer_id}")
            
            encrypted_message = self.encrypt_message(message, key)
            peer_socket = peer_info['socket']
            peer_socket.send(encrypted_message)
            print("Message sent")

    def listen_for_messages(self):
        while True:
            conn, addr = self.socket.accept()
            print(f"Connection from {addr}")
            threading.Thread(target=self.handle_connection, args=(conn,)).start()

    def handle_connection(self, conn):
        key_data = conn.recv(1024)
        if key_data:
            self.encryption_keys[self.user_id] = key_data
            print(f"Received encryption key from peer")

        data = conn.recv(1024)
        if data:
            print("Received encrypted data:", data)
            if self.user_id not in self.encryption_keys:
                print("Error: Missing encryption key for this connection.")
                return
            try:
                message = self.decrypt_message(data, self.encryption_keys[self.user_id])
                print("Decrypted message:", message)
            except Exception as e:
                print(f"Failed to decrypt message: {e}")

    def block_user(self, block_id):
        data = {"user_id": self.user_id, "block_id": block_id}
        response = self.send_request(f"{self.discovery_server}/block", data)
        if response:
            print(f"User {block_id} blocked successfully.")
        else:
            print("Failed to block user.")

    def mute_user(self, mute_id, duration=60):
        data = {"user_id": self.user_id, "mute_id": mute_id, "duration": duration}
        response = self.send_request(f"{self.discovery_server}/mute", data)
        if response:
            print(f"User {mute_id} muted for {duration} seconds.")
        else:
            print("Failed to mute user.")

    def send_request(self, url, data):
        """Send a request to the discovery server."""
        try:
            response = requests.post(url, json=data)
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to send request: {e}")
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P2P Client with Discovery Server")
    parser.add_argument("--user_id", required=True, help="Unique username for this peer")
    parser.add_argument("--port", type=int, required=True, help="Port number for this peer")
    args = parser.parse_args()

    if args.user_id == "server":
        app.run(host="0.0.0.0", port=5000, threaded=True)
    else:
        client = P2PClient(args.user_id, "127.0.0.1", args.port, "http://127.0.0.1:5000")
        ip = socket.gethostbyname(socket.gethostname())
        time.sleep(2)
        requests.post("http://127.0.0.1:5000/register", json={"user_id": args.user_id, "ip": ip, "port": args.port})
