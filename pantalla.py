import cv2
import numpy as np
import time
import os
import config
import boton

NOMBRE_VENTANA = "Fotobooth"


def crear_fondo_degradado():
    """
    Genera un fondo con degradado rosado, sin necesitar ninguna imagen
    externa. Se usa si no existe un archivo de fondo personalizado.
    """
    alto = config.ALTO_PANTALLA
    ancho = config.ANCHO_PANTALLA
    fondo = np.zeros((alto, ancho, 3), dtype=np.uint8)

    color_arriba = np.array([245, 200, 220])  # BGR: rosado claro
    color_abajo = np.array([200, 140, 190])   # BGR: morado rosado

    for y in range(alto):
        proporcion = y / alto
        color = color_arriba * (1 - proporcion) + color_abajo * proporcion
        fondo[y, :] = color

    return fondo


def obtener_fondo():
    if os.path.exists(config.RUTA_FONDO):
        fondo = cv2.imread(config.RUTA_FONDO)
        if fondo is not None:
            return cv2.resize(fondo, (config.ANCHO_PANTALLA, config.ALTO_PANTALLA))
    return crear_fondo_degradado()


def inicializar_ventana():
    cv2.namedWindow(NOMBRE_VENTANA, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(NOMBRE_VENTANA, config.ANCHO_PANTALLA, config.ALTO_PANTALLA)


def centrar_texto(imagen, texto, y, escala=1.0, color=(255, 255, 255), grosor=2):
    (ancho_texto, _alto_texto), _base = cv2.getTextSize(
        texto, cv2.FONT_HERSHEY_SIMPLEX, escala, grosor
    )
    x = (imagen.shape[1] - ancho_texto) // 2
    cv2.putText(imagen, texto, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                escala, color, grosor, cv2.LINE_AA)


def mostrar_menu_y_esperar():
    """
    Muestra la pantalla de bienvenida con instrucciones y espera una
    acción. Devuelve "foto", "ia" o "salir".
    En la Raspberry: revisa los botones físicos.
    En el computador: usa el teclado (1 = foto, 2 = ia, q = salir)
    directamente sobre la ventana, sin bloquear la terminal.
    """
    while True:
        fondo = obtener_fondo().copy()
        centrar_texto(fondo, "FOTOBOOTH METIE", 140, escala=1.6, grosor=3)
        centrar_texto(fondo, "Boton 1: tomar una foto", 240, escala=0.8)
        centrar_texto(fondo, "Boton 2: crear imagen con IA", 280, escala=0.8)
        cv2.imshow(NOMBRE_VENTANA, fondo)

        accion = boton.revisar_accion()
        if accion is not None:
            return accion

        tecla = cv2.waitKey(30) & 0xFF
        if tecla == ord('1'):
            return "foto"
        elif tecla == ord('2'):
            return "ia"
        elif tecla == ord('q'):
            return "salir"


def mostrar_mensaje(texto, subtexto="", segundos=None):
    """
    Muestra un mensaje centrado sobre el fondo. Si "segundos" tiene un
    valor, se queda esa cantidad de tiempo antes de seguir; si no,
    solo lo dibuja una vez y continúa de inmediato.
    """
    fondo = obtener_fondo().copy()
    centrar_texto(fondo, texto, 220, escala=1.2, grosor=3)
    if subtexto:
        centrar_texto(fondo, subtexto, 270, escala=0.7)
    cv2.imshow(NOMBRE_VENTANA, fondo)

    if segundos is not None:
        cv2.waitKey(int(segundos * 1000))
    else:
        cv2.waitKey(1)


def mostrar_vista_previa_con_conteo(segundos_totales=5):
    """
    Abre la cámara, muestra lo que ve dentro de un marco en el centro
    de la pantalla, con una cuenta regresiva encima. Al llegar a 0,
    devuelve el cuadro capturado (sin guardar todavía). Si la cámara
    falla, devuelve None.
    """
    camara = cv2.VideoCapture(config.CAMARA_INDICE)
    inicio = time.time()

    ancho_marco = 560
    alto_marco = 380
    x0 = (config.ANCHO_PANTALLA - ancho_marco) // 2
    y0 = 40

    cuadro_final = None

    while True:
        ok, cuadro = camara.read()
        if not ok:
            break

        cuadro_chico = cv2.resize(cuadro, (ancho_marco, alto_marco))
        lienzo = obtener_fondo().copy()
        lienzo[y0:y0 + alto_marco, x0:x0 + ancho_marco] = cuadro_chico
        cv2.rectangle(lienzo, (x0 - 5, y0 - 5), (x0 + ancho_marco + 5, y0 + alto_marco + 5),
                      (255, 255, 255), 5)

        restantes = segundos_totales - int(time.time() - inicio)
        if restantes > 0:
            centrar_texto(lienzo, str(restantes), 460, escala=2.2, grosor=4)
            cv2.imshow(NOMBRE_VENTANA, lienzo)
            cv2.waitKey(1)
        else:
            cuadro_final = cuadro
            break

    camara.release()
    return cuadro_final


def guardar_captura(cuadro):
    """
    Guarda un cuadro capturado (como el que devuelve
    mostrar_vista_previa_con_conteo) en la carpeta temporal.
    Devuelve la ruta del archivo.
    """
    if not os.path.exists(config.CARPETA_TEMP):
        os.makedirs(config.CARPETA_TEMP)
    ruta = os.path.join(config.CARPETA_TEMP, "foto.jpg")
    cv2.imwrite(ruta, cuadro)
    return ruta


def mostrar_imagen_resultado(ruta_imagen, texto_arriba="Listo!"):
    """
    Muestra una imagen ya guardada (foto real o generada por IA)
    centrada en pantalla, con un título arriba.
    """
    imagen = cv2.imread(ruta_imagen)
    if imagen is None:
        mostrar_mensaje("No se pudo mostrar la imagen", segundos=2)
        return

    alto_destino = 380
    escala = alto_destino / imagen.shape[0]
    ancho_destino = int(imagen.shape[1] * escala)
    imagen = cv2.resize(imagen, (ancho_destino, alto_destino))

    lienzo = obtener_fondo().copy()
    x0 = (config.ANCHO_PANTALLA - ancho_destino) // 2
    y0 = 70
    lienzo[y0:y0 + alto_destino, x0:x0 + ancho_destino] = imagen
    cv2.rectangle(lienzo, (x0 - 5, y0 - 5), (x0 + ancho_destino + 5, y0 + alto_destino + 5),
                  (255, 255, 255), 5)
    centrar_texto(lienzo, texto_arriba, 35, escala=0.9, grosor=2)
    cv2.imshow(NOMBRE_VENTANA, lienzo)
    cv2.waitKey(1)
