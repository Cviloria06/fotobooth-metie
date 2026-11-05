# Prueba SOLO la IA de imágenes (la que diga PROVEEDOR_IA en config.py), sin pantalla ni micrófono.
#
#   python3 prueba_ia.py "un gato astronauta"
#   python3 prueba_ia.py "un gato astronauta" --imprimir    (además la imprime)

import sys
import time

import config
import ia_generador


def main():
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    descripcion = " ".join(argumentos) or "un gato astronauta flotando entre estrellas"

    print("IA elegida:", config.PROVEEDOR_IA)
    print("Pidiendo:", descripcion)
    inicio = time.time()
    try:
        ruta = ia_generador.generar_imagen(descripcion)
    except ia_generador.ErrorIA as error:
        print("ERROR:", error.detalle)
        print("En la pantalla se vería:", error.corto)
        return
    print("Listo en %.1f segundos. Imagen guardada en: %s" % (time.time() - inicio, ruta))

    if "--imprimir" in sys.argv:
        import impresora
        print("Imprimiendo...")
        impresora.imprimir_imagen(ruta)
        print("Listo, revisa el papel.")


if __name__ == "__main__":
    main()
