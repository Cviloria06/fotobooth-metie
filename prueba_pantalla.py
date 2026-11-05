# Prueba SOLO la pantalla SPI, sin botón, impresora ni menú.
#
#   python3 prueba_pantalla.py            colores, orientación y letras
#   python3 prueba_pantalla.py --camara   además, 10 segundos con la imagen de la cámara
#
# Si algo no se ve bien, al final de cada paso dice qué ajuste cambiar en config.py.

import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import config
import pantalla_spi


def imagen_de_prueba(ancho, alto):
    """Barras de color y una 'F' en la esquina de arriba a la izquierda."""
    img = Image.new("RGB", (ancho, alto), (255, 255, 255))
    d = ImageDraw.Draw(img)
    barras = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255), (0, 0, 0)]
    ancho_barra = ancho // len(barras)
    for i, color in enumerate(barras):
        d.rectangle([i * ancho_barra, alto // 3, (i + 1) * ancho_barra, alto], fill=color)
    d.rectangle([0, alto - 14, ancho, alto], fill=(255, 255, 0))

    letra = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(alto * 0.28))
    d.text((8, 2), "F", font=letra, fill=(0, 0, 0))
    chica = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    d.text((ancho * 0.28, alto * 0.08), "Pantalla OK", font=chica, fill=(0, 0, 0))
    d.text((ancho * 0.28, alto * 0.20), "320 x 240", font=chica, fill=(0, 0, 0))
    return np.asarray(img)


def main():
    print("Paso 1: iniciando la pantalla...")
    pantalla = pantalla_spi.PantallaSPI()
    try:
        pantalla.iniciar()
    except Exception as error:
        print("ERROR:", error)
        print()
        print("Si dice que el SPI está apagado: sudo raspi-config nonint do_spi 0  y reinicia.")
        print("Si no hay error pero la pantalla queda en blanco: revisa los cables CS, DC,")
        print("RESET, MOSI, SCK, VCC y GND (ver la tabla de pines).")
        return

    print("Paso 2: colores de pantalla completa (1 segundo cada uno)")
    for nombre, color in [("ROJO", (255, 0, 0)), ("VERDE", (0, 255, 0)), ("AZUL", (0, 0, 255)),
                          ("BLANCO", (255, 255, 255)), ("NEGRO", (0, 0, 0))]:
        print("   ", nombre)
        pantalla.llenar(color)
        time.sleep(1.2)

    print("Paso 3: imagen de prueba (barras de color y una F arriba a la izquierda)")
    pantalla.mostrar(imagen_de_prueba(pantalla.ancho, pantalla.alto))
    time.sleep(4)

    if "--camara" in sys.argv:
        import cv2
        import captura
        print("Paso 4: cámara durante 10 segundos")
        camara = captura.abrir_camara()
        if camara is None:
            print("ERROR: no se pudo abrir la cámara.")
        else:
            cuadros = 0
            inicio = time.time()
            while time.time() - inicio < 10:
                ok, cuadro = camara.read()
                if not ok:
                    break
                cuadro = captura.recortar_4_3(cuadro)
                chico = cv2.resize(cuadro, (pantalla.ancho, pantalla.alto), interpolation=cv2.INTER_AREA)
                pantalla.mostrar(cv2.cvtColor(chico, cv2.COLOR_BGR2RGB))
                cuadros += 1
            camara.release()
            print("   %d cuadros en 10 s (%.1f por segundo)" % (cuadros, cuadros / 10))

    pantalla.apagar()

    print()
    print("Qué revisar y qué cambiar en config.py:")
    print(" - Rojo, verde y azul salieron en ese orden?  Si el rojo salió azul: PANTALLA_CAMBIAR_ROJO_AZUL = True")
    print(" - La F se ve derecha y arriba a la izquierda?  Si está de cabeza o volteada: PANTALLA_ROTACION = 3 (o 0, 2)")
    print(" - Los colores se ven como un negativo?  PANTALLA_INVERTIR_COLORES = True")
    print(" - Se ven rayas, puntitos o desorden?  Baja PANTALLA_SPI_VELOCIDAD a 16000000 o 8000000")


if __name__ == "__main__":
    main()
