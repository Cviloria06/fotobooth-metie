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
import captura

RUTA_FOTO = "foto_boton.jpg"


def hacer_foto_con_cuenta():
    """Cuenta regresiva en la terminal, mientras la cámara sigue leyendo
    (así ajusta la luz). Al llegar a 0 guarda el promedio de los últimos
    cuadros, que sale con menos ruido. Devuelve la ruta o None si algo falló."""
    camara = captura.abrir_camara()
    if camara is None:
        print("ERROR: no se pudo abrir la cámara. ¿Hay otro programa usándola?")
        return None

    total = config.SEGUNDOS_CUENTA_REGRESIVA
    inicio = time.time()
    ultimo_mostrado = None
    ultimos = []

    while True:
        transcurrido = time.time() - inicio
        if transcurrido >= total:
            break

        ok, leido = camara.read()
        if ok:
            ultimos.append(captura.recortar_4_3(leido))
            if len(ultimos) > config.CUADROS_A_PROMEDIAR:
                ultimos.pop(0)

        restantes = total - int(transcurrido)
        if restantes != ultimo_mostrado:
            print("  ", restantes, "...")
            ultimo_mostrado = restantes

    camara.release()

    if not ultimos:
        print("ERROR: la cámara no entregó ninguna imagen.")
        return None

    cuadro = captura.promediar(ultimos)
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
