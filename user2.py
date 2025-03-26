import time
import requests
from P2P import P2PClient

# Start the client for user2 and send a message to user1
def run_user2():
    client = P2PClient("user2", "127.0.0.1", 6002, "http://127.0.0.1:5000")
    ip = "127.0.0.1"  
    time.sleep(2)  
    
    requests.post("http://127.0.0.1:5000/register", json={"user_id": "user2", "ip": ip, "port": 6002})
    
    # Wait for peer discovery and send a message to user1
    time.sleep(3)  
    client.discover_peers()
    client.send_message("user1", "Hello from user2!")
    
    input("Press Enter to exit user2...")

if __name__ == "__main__":
    run_user2()
