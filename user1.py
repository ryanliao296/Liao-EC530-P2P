import time
import requests
from P2P import P2PClient

# Start the client for user1
def run_user1():
    client = P2PClient("user1", "127.0.0.1", 6001, "http://127.0.0.1:5000")
    ip = "127.0.0.1" 
    time.sleep(2)  
    
    requests.post("http://127.0.0.1:5000/register", json={"user_id": "user1", "ip": ip, "port": 6001})

    input("Press Enter to exit user1...")

if __name__ == "__main__":
    run_user1()
