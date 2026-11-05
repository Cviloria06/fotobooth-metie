# Prueba SOLO el micrófono: graba unos segundos, muestra el volumen y escribe lo que entendió.
#
#   python3 prueba_microfono.py
#
# Cuando empiece a grabar, di una frase, por ejemplo: "un gato con sombrero de fiesta".

import subprocess

import config
import ia_generador


def main():
    print("Paso 1: micrófonos que ve la Raspberry (arecord -l)")
    try:
        print(subprocess.run(["arecord", "-l"], capture_output=True, text=True).stdout)
    except FileNotFoundError:
        print("No existe arecord. Instálalo con: sudo apt install alsa-utils")
        return

    try:
        dispositivo = ia_generador._dispositivo_microfono()
    except ia_generador.ErrorIA as error:
        print("ERROR:", error.detalle)
        return
    print("Paso 2: se usará el dispositivo:", dispositivo)

    segundos = config.MICROFONO_SEGUNDOS
    print("Paso 3: grabando", segundos, "segundos... HABLA AHORA")
    ruta = "voz_prueba.wav"
    try:
        ia_generador.grabar_audio(ruta, segundos)
    except ia_generador.ErrorIA as error:
        print("ERROR:", error.detalle)
        return

    volumen, pico = ia_generador.nivel_audio(ruta)
    barra = "#" * int(min(pico, 32767) / 32767 * 40)
    print("Paso 4: volumen medio %d, pico %d   [%-40s]" % (volumen, pico, barra))
    if pico < config.MICROFONO_UMBRAL_SILENCIO:
        print("   Casi no se oyó nada. Habla más cerca, o prueba otro dispositivo en")
        print("   MICROFONO_DISPOSITIVO (config.py), por ejemplo 'plughw:2,0'.")
        return

    ia_generador._subir_volumen(ruta, pico)
    print("Paso 5: convirtiendo la voz a texto (necesita internet)...")
    try:
        texto = ia_generador.transcribir(ruta)
    except ia_generador.ErrorIA as error:
        print("ERROR:", error.detalle)
        return
    print("   Entendí:", texto if texto else "(nada, no se entendió)")


if __name__ == "__main__":
    main()
