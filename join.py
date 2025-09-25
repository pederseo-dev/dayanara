from dayanara import Dayanara
import threading
import time

# Terminal 2 - Peer 1  
peer1 = Dayanara()
peer1.join('sala1')

def escuchar_mensajes():
    """Hilo para escuchar mensajes entrantes"""
    while True:
        try:
            data = peer1.receive()
            if data is not None:
                print(data[3])

        except Exception as e:
            return e
        
        time.sleep(0.1)  # Pequeña pausa para no saturar CPU

def escribir_mensajes():
    """Hilo para escribir y enviar mensajes"""
    while True:
        try:
            msg = input("Tu mensaje: ")
            peer1.send(msg)
        except KeyboardInterrupt:
            break
        except Exception as e:
           return e

# Crear hilos
escuchar_thread = threading.Thread(target=escuchar_mensajes, daemon=True)
escribir_mensajes()

