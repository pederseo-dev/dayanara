from dayanara import Dayanara
import time

boostrap = Dayanara(ip='127.0.0.1',port=5000)
boostrap.host()

print("Bootstrap iniciado en 127.0.0.1:5000")
print("Presiona Ctrl+C para detener...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Bootstrap detenido")