# Prueba SOLO la IA de imágenes (la que diga PROVEEDOR_IA en config.py), sin pantalla ni micrófono.
#
#   python3 prueba_ia.py "un gato astronauta"
#   python3 prueba_ia.py "un gato astronauta" --modelo=flux       (probar otro modelo)
#   python3 prueba_ia.py "un gato astronauta" --sin-estilo        (sin el texto de estilo)
#   python3 prueba_ia.py "un gato astronauta" --sin-traducir      (sin traducir al inglés)
#   python3 prueba_ia.py "a cat astronaut" --imprimir             (además la imprime; con sudo)
#
# Las opciones solo valen para esta prueba: no cambian config.py.
# Cada vez la imagen se guarda en temp/generada.jpg (la anterior se reemplaza).

import sys
import time

import config
import ia_generador


def main():
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    descripcion = " ".join(argumentos) or "un gato astronauta flotando entre estrellas"

    for a in sys.argv[1:]:
        if a.startswith("--modelo="):
            config.POLLINATIONS_MODELO = a.split("=", 1)[1]
    if "--sin-estilo" in sys.argv:
        config.ESTILO_IA = ""
    if "--sin-traducir" in sys.argv:
        config.TRADUCIR_A_INGLES = False

    print("IA elegida:", config.PROVEEDOR_IA,
          "| modelo:", getattr(config, "POLLINATIONS_MODELO", "") or "(por defecto)",
          "| estilo:", "sí" if config.ESTILO_IA else "no",
          "| traducir:", "sí" if config.TRADUCIR_A_INGLES else "no")
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
