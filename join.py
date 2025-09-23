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
                print(f"[RECIBIDO] {data}")

        except Exception as e:
            # Solo mostrar errores importantes, no errores de conexión
            if "10054" not in str(e):
                print(f"[ERROR RECIBIENDO] {e}")
        
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
            print(f"Error enviando mensaje: {e}")

# Crear hilos
escuchar_thread = threading.Thread(target=escuchar_mensajes, daemon=True)
escribir_thread = threading.Thread(target=escribir_mensajes, daemon=True)

# Iniciar hilos
escuchar_thread.start()
escribir_thread.start()

try:
    # Mantener el programa corriendo
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nSaliendo del chat...")

