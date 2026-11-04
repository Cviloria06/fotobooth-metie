# Prueba: botón + cámara + impresora, SIN pantalla.
#
#   Toque corto  -> cuenta regresiva en la terminal, toma la foto y la imprime
#   Mantenerlo   -> por ahora solo avisa (más adelante será el modo IA)
#   Ctrl+C       -> salir
#
# Con el botón conectado:
#     sudo python3 prueba_boton.py
# Sin el botón todavía (usa el teclado):
#     sudo python3 prueba_boton.py --teclado
#   En modo teclado:  Enter = toque corto,  l + Enter = mantener,  q + Enter = salir

import sys
import time
import cv2
import config
import boton
import impresora

RUTA_FOTO = "foto_boton.jpg"


def hacer_foto_con_cuenta():
    """Cuenta regresiva en la terminal, mientras la cámara sigue leyendo
    (así ajusta la luz), y al llegar a 0 guarda la foto. Devuelve la ruta
    o None si algo falló."""
    camara = cv2.VideoCapture(config.CAMARA_INDICE, cv2.CAP_V4L2)
    if not camara.isOpened():
        camara = cv2.VideoCapture(config.CAMARA_INDICE)
    if not camara.isOpened():
        print("ERROR: no se pudo abrir la cámara. ¿Hay otro programa usándola?")
        return None

    camara.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camara.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    total = config.SEGUNDOS_CUENTA_REGRESIVA
    inicio = time.time()
    ultimo_mostrado = None
    cuadro = None

    while True:
        transcurrido = time.time() - inicio
        if transcurrido >= total:
            break

        ok, leido = camara.read()
        if ok:
            cuadro = leido

        restantes = total - int(transcurrido)
        if restantes != ultimo_mostrado:
            print("  ", restantes, "...")
            ultimo_mostrado = restantes

    camara.release()

    if cuadro is None:
        print("ERROR: la cámara no entregó ninguna imagen.")
        return None

    cv2.imwrite(RUTA_FOTO, cuadro)
    return RUTA_FOTO


def leer_teclado():
    texto = input("Enter = toque corto, l = mantener, q = salir: ").strip().lower()
    if texto == "q":
        return "salir"
    if texto == "l":
        return "ia"
    return "foto"


def main():
    usar_teclado = "--teclado" in sys.argv

    if not usar_teclado and not boton.HAY_BOTON:
        print("No se pudo usar el botón por GPIO; se usará el teclado.")
        usar_teclado = True

    if usar_teclado:
        print("Modo teclado.")
    else:
        estado = "PRESIONADO" if boton.estado_actual() else "suelto"
        print("Botón listo en GPIO", config.PIN_BOTON, "- estado actual:", estado)
        if estado == "PRESIONADO":
            print("Dice PRESIONADO sin tocarlo: el cable quedó en la terminal NC.")
            print("Cámbialo a la terminal NO y vuelve a correr la prueba.")
        print("Toque corto = foto. Mantener", config.TIEMPO_PULSACION_LARGA,
              "s = IA. Ctrl+C para salir.")

    boton.revisar_accion()  # descarta cualquier pulsación vieja

    try:
        while True:
            accion = leer_teclado() if usar_teclado else boton.esperar_accion()

            if accion == "salir":
                break

            if accion == "foto":
                print("Toque corto: foto en", config.SEGUNDOS_CUENTA_REGRESIVA, "segundos")
                ruta = hacer_foto_con_cuenta()
                if ruta is not None:
                    print("Foto tomada. Imprimiendo...")
                    try:
                        impresora.imprimir_imagen(ruta)
                        print("Listo.")
                    except Exception as error:
                        print("ERROR al imprimir:", error)

            elif accion == "ia":
                print("Pulsación larga detectada: aquí irá el modo IA (todavía no se ejecuta).")

            if not usar_teclado:
                boton.revisar_accion()  # ignora lo que se presionó mientras trabajaba

    except KeyboardInterrupt:
        pass

    print("Hasta luego.")


if __name__ == "__main__":
    main()
