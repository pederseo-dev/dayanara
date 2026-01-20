# Dayanara
A minimal peer-to-peer networking protocol that lets you build distributed applications with just a few lines of code. Designed to be simple and lightweight, Dayanara handles peer discovery, room management, and message routing so you can focus on building your application. No heavy frameworks, no complex configurations—just straightforward P2P networking with minimal dependencies.

## ⚠️ Security Warning
This is a minimal, raw implementation designed for rapid prototyping and trusted networks.

- **No encryption** - All traffic is plaintext
- **No authentication** - Anyone can join any room
- **UDP-based** - No guaranteed delivery
- **No NAT traversal** - Requires public IPs or local network
- **Raw protocol** - You must implement your own security and encryption layer

This tool provides the foundation. Security, encryption, and production-hardening are your responsibility.
Recommended for: Development, local networks, VPNs, educational projects, and rapid prototyping.

## Bootstrap Server
By default, Dayanara uses a hardcoded public bootstrap server - just start coding, no setup needed.

Want to run your own bootstrap? The complete server implementation is available at: [bootstrap_p2p repository](https://github.com/pederseo-dev/bootstrap_p2p)

Deploy it, then configure your clients:

```python
# Custom bootstrap (optional)
d = Dayanara(bootstraps=[['your-server.com', 5000]])
```

## API

#### Dayanara(bootstraps=None, debug=False)

Create a new Dayanara instance.

* `bootstraps`: list of bootstrap servers (optional)
* `debug`: enable debug output (default: False)

#### join(room: str)

Join a room and start peer discovery.

#### send(data)

Send data to all connected peers.

#### receive()

Block until a message is received and return it.

## Installation

```bash
pip install dayanara
```

## P2P chat example
```python
import threading
import sys
from dayanara import Dayanara

room = input("room name: ")

d = Dayanara()

d.join(room)

# receive loop
def receiv_msg():
    while True:
        msg = d.receive()
        if msg:
            print(f'Incoming message: {msg}')

threading.Thread(target=receiv_msg, daemon=True).start()

# send loop
try:
    while True:
        message = input('message:')
        if message:
            d.send(message)
except KeyboardInterrupt:
    sys.exit(0)
```
## Use Cases

- Game lobbies
- Chat rooms
- IoT discovery
- File sharing (local networks)
- Educational P2P projects
- Hackathon prototypes

## License

MIT
