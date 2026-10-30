# Prueba de cámara + impresión SIN necesitar pantalla ni ventana.
# Toma una foto, la guarda como foto_prueba.jpg y la imprime.
#
# Correr con:  sudo python3 prueba_camara.py

import time
import cv2
import config
import impresora

RUTA_FOTO = "foto_prueba.jpg"

print("Paso 1: abriendo la cámara...")
camara = cv2.VideoCapture(config.CAMARA_INDICE, cv2.CAP_V4L2)
if not camara.isOpened():
    camara = cv2.VideoCapture(config.CAMARA_INDICE)

if not camara.isOpened():
    print("ERROR: no se pudo abrir la cámara en el índice", config.CAMARA_INDICE)
    print("Prueba cambiando CAMARA_INDICE en config.py (por ejemplo a 1).")
    raise SystemExit(1)

camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Paso 2: calentando la cámara (para que ajuste la luz)...")
cuadro = None
for i in range(15):
    ok, cuadro = camara.read()
    time.sleep(0.1)

camara.release()

if cuadro is None:
    print("ERROR: la cámara abrió pero no entregó ninguna imagen.")
    raise SystemExit(1)

cv2.imwrite(RUTA_FOTO, cuadro)
alto, ancho = cuadro.shape[:2]
print("Paso 3: foto guardada como", RUTA_FOTO, "- tamaño:", ancho, "x", alto)

print("Paso 4: imprimiendo la foto...")
impresora.imprimir_imagen(RUTA_FOTO)
print("Listo, revisa el papel.")
