# Olaf P2P Protocol

A lightweight peer-to-peer networking protocol implementation in Python with bootstrap server support for peer discovery and room-based connections.

## Architecture Overview

The system consists of four main components:

### 1. **Olaf Protocol** (`olaf.py`)
Binary protocol for encoding/decoding P2P messages with the following structure:
```
[type (1B)] [peers (2B + N*10B)] [payload (4B + data)]
```

Each peer address contains:
- **IPv4 address**: 4 bytes
- **Port**: 2 bytes  
- **Peer ID**: 4 bytes

**Key Methods:**
- `encode_msg(type, peers, payload)` - Encodes messages to binary
- `decode_msg(data)` - Decodes binary messages
- Supports multiple peers per message for efficient broadcasting

### 2. **Peer** (`peer.py`)
UDP socket wrapper handling low-level network communication.

**Features:**
- Non-blocking UDP sockets with configurable timeout
- Single peer and broadcast messaging
- Automatic message encoding/decoding via Olaf protocol

**Key Methods:**
- `socket_send(type, peers, payload, target_addr)` - Send to single peer
- `socket_send_all(type, peers, payload)` - Broadcast to multiple peers
- `socket_receive(timeout, buffer_size)` - Receive messages with timeout

### 3. **Network** (`network.py`)
State management for peer discovery and room membership.

**State Machine:**
- `send_join` - Request to join room via bootstrap
- `send_collector` - Report peers to bootstrap (lowest ID peer only)
- `send_ping` - Heartbeat to maintain connections
- `purge` - Remove inactive peers

**Key Methods:**
- `add_peer(peer_addr)` - Add peer to room
- `remove_peer(peer_addr)` - Remove peer from room
- `get_other_peers()` - Get list of peers excluding self
- `evaluate_state()` - Update state based on peer presence
- `delete_inactive()` - Remove peers exceeding timeout
- `update_ts(peer_addr)` - Update last-seen timestamp

### 4. **Core** (`core.py`)
Main application controller coordinating all components.

**Threading Model:**
- `connect()` - Receives and routes incoming messages
- `heart(room)` - Heartbeat loop managing state transitions

**Message Types:**
- `JOIN_B` - Join room request to bootstrap
- `BOOTSTRAP_R` - Bootstrap response with peer list
- `PEER_COLLECTOR` - Report active peers to bootstrap
- `PING` - Keep-alive between peers
- `APP_R` - Application-level data
- `ROOM_FULL` - Room capacity exceeded

## Workflow

### Joining a Room

1. Peer sends `JOIN_B` to bootstrap server with room name
2. Bootstrap responds with `BOOTSTRAP_R` containing:
   - Assigned public address `[ip, port, id]`
   - List of existing peers in room
3. Peer stores self address and adds other peers to room
4. State transitions to connected mode

### Connected State

**Heartbeat Cycle (every 3 seconds):**
1. Evaluate current state
2. If peers exist:
   - Send `PING` to all peers
   - Purge inactive peers (timeout > 15s)
   - If lowest ID: send `PEER_COLLECTOR` to bootstrap
3. If alone:
   - Send `JOIN_B` to request peers

### Message Flow

```
Peer A                  Bootstrap               Peer B
  |                         |                      |
  |------ JOIN_B ---------->|                      |
  |<--- BOOTSTRAP_R --------|                      |
  |   (includes Peer B)     |                      |
  |                         |                      |
  |------------- PING ---------------------------->|
  |<------------ PING -----------------------------|
  |                         |                      |
  |--- PEER_COLLECTOR ----->|                      |
  |   (if lowest ID)        |                      |
```

## API Usage

### Initialization

```python
from core import Core

# Connect to bootstrap servers
bootstraps = [['127.0.0.1', 5000], ['127.0.0.1', 5001]]
core = Core(bootstraps=bootstraps)

# Start threads
import threading
threading.Thread(target=core.connect, daemon=True).start()
threading.Thread(target=core.heart, args=('my-room',), daemon=True).start()
```

### Sending Data

```python
# Send to all peers in room
core.app_send("Hello, peers!")
```

### Receiving Data

```python
# Blocking receive from queue
payload = core.app_receive()
print(f"Received: {payload}")
```

### Graceful Shutdown

```python
import signal
signal.signal(signal.SIGINT, core.signal_handler)
```

## Configuration

```python
# config.py (expected)
APP_R = 0x01           # Application data
BOOTSTRAP_R = 0x02     # Bootstrap response  
PING = 0x03            # Heartbeat
ROOM_FULL = 0x04       # Room capacity error
JOIN_B = 0x05          # Join room request
PEER_COLLECTOR = 0x06  # Report peers to bootstrap
```

## Requirements

- Python 3.7+
- Standard library only (no external dependencies)

## Thread Safety

- All peer list operations are protected by threading locks
- State evaluation prevents deadlocks by avoiding nested lock calls
- Message queue for thread-safe application data delivery

## Limitations

- UDP-based (no guaranteed delivery)
- No encryption or authentication
- Fixed timeout for peer inactivity (15 seconds)
- Requires external bootstrap servers
- No NAT traversal (assumes public IPs or local network)

## Use Cases

- Lightweight game lobbies
- Decentralized chat rooms
- IoT device discovery
- File sharing networks
- Real-time collaboration tools

## Future Improvements

- TCP option for reliable delivery
- End-to-end encryption
- NAT hole punching
- Dynamic timeout adjustment
- Peer validation/authentication
- Bootstrap server implementation included

---

**License:** Not specified  
**Contributors:** Add your team here