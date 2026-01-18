
# Dayanara

Dayanara is a lightweight peer-to-peer networking library for Python that allows
peers to discover each other using bootstrap servers and communicate inside rooms.

## Installation

```bash
pip install dayanara
````

## Basic usage

```python
from dayanara import Dayanara

d = Dayanara()
d.join("room1")

d.send("Hola")
msg = d.receive()
print(msg)
```

## API

### Dayanara

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

#### peers_list()

Return the list of known peers.

## License

MIT
