import time
from P2P import P2PClient  # Assuming you have the P2P class in the same directory

def run_user3():
    client = P2PClient("user3", "127.0.0.1", 6003, "http://127.0.0.1:5000")
    
    time.sleep(2)  # Allow time for registration
    
    # Block user4
    client.block_user("user4")
    print("User4 is now blocked.")
    
    # Mute user4 for 60 seconds
    client.mute_user("user4", 60)
    print("User4 is now muted for 60 seconds.")

    # Test sending messages
    client.send_message("user4", "Hello user4, I am user3. You shouldn't be able to see this if blocked!")
    time.sleep(2)
    client.send_message("user4", "This should still be blocked from user3's side.")
    
    input("Press Enter to exit user3...")

if __name__ == "__main__":
    run_user3()
