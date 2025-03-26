import time
import requests
from P2P import P2PClient

# Start the client for user1
def run_user1():
    client = P2PClient("user1", "127.0.0.1", 6001, "http://127.0.0.1:5000")
    ip = "127.0.0.1"  # Local IP for testing
    time.sleep(2)  # Ensure discovery server is running before registration
    # Register user1 with the discovery server
    requests.post("http://127.0.0.1:5000/register", json={"user_id": "user1", "ip": ip, "port": 6001})
    
    # Keep the program running so it can listen for incoming messages
    input("Press Enter to exit user1...")

if __name__ == "__main__":
    run_user1()
