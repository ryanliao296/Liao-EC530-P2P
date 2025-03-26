# Peer-to-Peer Messaging System

This project implements a simple peer-to-peer (P2P) messaging system where users can connect, send encrypted messages, and manage users' statuses (blocking and muting). The system also integrates basic server-side blocking and muting features.

## Files Overview

- **P2P.py**: Core logic for the P2P messaging system, including the client class for connecting, sending messages, and managing user blocks and mutes.
- **user1.py**: Script to simulate user 1, listening for incoming connections and sending messages to user 2.
- **user2.py**: Script to simulate user 2, listening for incoming connections and sending messages to user 1.
- **user3.py**: Script to simulate user 3, testing blocking and muting user 4.
- **user4.py**: Script to simulate user 4, where blocking and muting functionalities are also tested by seeing if user 3 is unable to see messages sent by user 4.
