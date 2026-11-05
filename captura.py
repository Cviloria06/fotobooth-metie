# Funciones de la cámara que usan tanto la prueba del botón como la pantalla.

import cv2
import numpy as np
import config


def abrir_camara():
    """
    Abre la cámara con la resolución de config.py (CAMARA_ANCHO x CAMARA_ALTO).
    Si la cámara no permite esa resolución, usa la que tenga disponible.
    Devuelve None si no se pudo abrir.
    """
    camara = cv2.VideoCapture(config.CAMARA_INDICE, cv2.CAP_V4L2)
    if not camara.isOpened():
        camara = cv2.VideoCapture(config.CAMARA_INDICE)
    if not camara.isOpened():
        return None

    camara.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMARA_ANCHO)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMARA_ALTO)
    return camara


def recortar_4_3(cuadro):
    """Recorta el centro del cuadro a proporción 4:3, como una foto normal."""
    alto, ancho = cuadro.shape[:2]
    if ancho * 3 > alto * 4:              # demasiado ancho: se recortan los lados
        nuevo_ancho = alto * 4 // 3
        x = (ancho - nuevo_ancho) // 2
        return cuadro[:, x:x + nuevo_ancho]
    if ancho * 3 < alto * 4:              # demasiado alto: se recortan arriba y abajo
        nuevo_alto = ancho * 3 // 4
        y = (alto - nuevo_alto) // 2
        return cuadro[y:y + nuevo_alto, :]
    return cuadro


def promediar(cuadros):
    """
    Promedia varios cuadros seguidos: el ruido de la cámara cambia de un
    cuadro a otro y se cancela, mientras que la imagen real se mantiene.
    Con un solo cuadro lo devuelve igual.
    """
    return np.mean(np.stack(cuadros), axis=0).astype("uint8")
