
# Dayanara

Dayanara is a lightweight peer-to-peer networking library for Python that allows
peers to discover each other using bootstrap servers and communicate inside rooms.

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

## License

MIT
