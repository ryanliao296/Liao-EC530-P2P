import time
from P2P import P2PClient  # Assuming you have the P2P class in the same directory

def run_user4():
    client = P2PClient("user4", "127.0.0.1", 6004, "http://127.0.0.1:5000")
    
    time.sleep(2)
    
    # Test sending messages to user3
    client.send_message("user3", "Hello user3, I am user4. Let's see if you get this message!")
    time.sleep(2)
    client.send_message("user3", "This is another message for user3.")
    
    input("Press Enter to exit user4...")

if __name__ == "__main__":
    run_user4()
