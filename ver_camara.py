# Vista en vivo de la cámara, para ver qué está captando y apuntarla bien.
#
# Se corre SIN sudo, desde una terminal dentro del escritorio de la
# Raspberry (Raspberry Pi Connect -> Screen sharing):
#     python3 ver_camara.py
#
#   s = guardar una foto (foto_vista.jpg)
#   q = salir

import cv2
import config

camara = cv2.VideoCapture(config.CAMARA_INDICE, cv2.CAP_V4L2)
if not camara.isOpened():
    camara = cv2.VideoCapture(config.CAMARA_INDICE)

if not camara.isOpened():
    print("ERROR: no se pudo abrir la cámara en el índice", config.CAMARA_INDICE)
    raise SystemExit(1)

camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print("Vista en vivo. Presiona 's' para guardar una foto, 'q' para salir.")

while True:
    ok, cuadro = camara.read()
    if not ok:
        print("ERROR: la cámara no entregó imagen.")
        break

    cv2.imshow("Vista de la camara", cuadro)
    tecla = cv2.waitKey(1) & 0xFF

    if tecla == ord("s"):
        cv2.imwrite("foto_vista.jpg", cuadro)
        print("Foto guardada como foto_vista.jpg")
    elif tecla == ord("q"):
        break

camara.release()
cv2.destroyAllWindows()
