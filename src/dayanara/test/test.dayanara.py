import sys
from pathlib import Path
import threading

sys.path.append(str(Path(__file__).resolve().parent.parent))
from main import Dayanara

# Setup
username = input("Nombre: ")
room = input("Sala: ")

# Instanciar
d = Dayanara()

# Join async (NO bloquea)
d.join(room)

# Thread para recibir
def recibir():
    while True:
        msg = d.receive()
        if msg:
            print(f"\r{msg}")
            print(f"{username}: ", end='', flush=True)
            print(d.conn_peers())

threading.Thread(target=recibir, daemon=True).start()

# Bucle para enviar
try:
    while True:
        mensaje = input(f"{username}: ")
        if mensaje:
            d.send(f"{username}: {mensaje}")
except KeyboardInterrupt:
    print("\nCerrando...")
    sys.exit(0)

