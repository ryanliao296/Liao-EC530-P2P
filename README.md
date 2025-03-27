# P2P Chat Client

This is a simple peer-to-peer (P2P) chat application that supports messaging, user discovery, blocking, and muting. It allows clients to communicate with each other through a discovery server and includes features for blocking and muting users to control communication.

## Features
- **User Discovery**: Allows clients to discover other active users on the network.
- **Message Sending**: Users can send messages to each other.
- **Blocking**: Users can block other users, preventing them from sending messages.
- **Muting**: Users can mute others, causing their messages to be silently ignored.
- **Keep-Alive**: Periodic keep-alive messages are sent to the discovery server to indicate the user's presence.

## Setup

### Discovery Server (Server-side)
To run the discovery server, use the following command:

```bash
python P2P.py --user_id server --port 5000
```
This will start the discovery server, which manages the list of users and their IP addresses. The server listens for incoming connections from clients and provides the necessary user data for peer discovery.

### Peer-to-Peer Client (Client-side)
To run the client, use the following command:

```bash
python P2P.py --user_id <your_user_id> --port <port_number>
```
Replace <your_user_id> with a unique username and <port_number> with the port you want to use for communication. The client will register with the discovery server and will be able to discover and communicate with other peers.

### Registering a User
Once the client is running, it will automatically register with the discovery server by sending its IP address and port number. This allows the client to be discovered by others in the network.

## How it Works
### Discovery Server
The discovery server manages a list of active users, storing their IP addresses and ports. Clients periodically send keep-alive messages to indicate they are still active, and the server updates their status. The server responds to requests from clients to list active users, enabling them to discover peers.
- Registration: When a new client starts, it sends a request to the discovery server to register with its unique user_id, ip, and port.
- Discovery: Clients can query the server to discover other active users in the network.

### Peer-to-Peer Client
The P2P client connects to peers discovered through the discovery server. It uses TCP sockets to establish direct communication with other clients. Clients can send and receive messages and interact with each other.
- Message Sending: A client can send messages to other peers. If the peer is blocked, the message will not be sent. If the peer is muted, the message will be silently ignored.
- Blocking: Users can block other users, preventing them from sending messages. When a user is blocked, their messages will not be processed by the recipient.
- Muting: Muting a user will silently ignore their messages without disconnecting the connection. Muted users' messages are received but not printed.

### Commands
The client acceps the following commands from the user:
- /msg <peer_id> <message>: Send a message to a peer.
- /discover: Discover active peers from the discovery server.
- /block <peer_id>: Block a peer from sending messages.
- /unblock <peer_id>: Unblock a peer to allow messages again.
- /mute <peer_id>: Mute a peer to silently ignore their messages.
- /unmute <peer_id>: Unmute a peer to allow their messages to be processed.
- /exit: Exit the chat client.
