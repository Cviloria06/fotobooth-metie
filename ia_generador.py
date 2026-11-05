import requests
import os
import urllib.parse
import config


def escuchar_descripcion():
    """
    Graba audio del micrófono y lo convierte a texto.
    Devuelve el texto reconocido, o None si no se pudo (nadie habló,
    no se entendió, no hay micrófono o no hay internet).
    """
    # Se importa aquí para que generar_imagen() funcione aunque todavía
    # no esté instalada la librería del micrófono.
    import speech_recognition as sr

    reconocedor = sr.Recognizer()

    try:
        with sr.Microphone() as fuente:
            reconocedor.adjust_for_ambient_noise(fuente, duration=1)
            audio = reconocedor.listen(fuente, timeout=6, phrase_time_limit=8)
    except sr.WaitTimeoutError:
        print("No se detectó voz.")
        return None
    except OSError as error:
        print("No se pudo usar el micrófono:", error)
        return None

    try:
        return reconocedor.recognize_google(audio, language="es-CO")
    except sr.UnknownValueError:
        print("No se entendió el audio.")
        return None
    except sr.RequestError as error:
        print("Error con el servicio de reconocimiento de voz:", error)
        return None


def generar_imagen(descripcion):
    """
    Envía la descripción a Pollinations.ai y guarda la imagen resultante.
    Devuelve la ruta del archivo. Si la IA no devuelve una imagen,
    lanza un error que explica qué respondió.
    """
    texto_codificado = urllib.parse.quote(descripcion)
    url = f"https://image.pollinations.ai/prompt/{texto_codificado}?width=768&height=1024&nologo=true"

    respuesta = requests.get(url, timeout=90)
    tipo = respuesta.headers.get("Content-Type", "")

    if respuesta.status_code != 200 or "image" not in tipo:
        raise RuntimeError(
            "La IA no devolvió una imagen (código "
            + str(respuesta.status_code) + ", tipo " + tipo + "). Respuesta: "
            + respuesta.text[:200]
        )

    if not os.path.exists(config.CARPETA_TEMP):
        os.makedirs(config.CARPETA_TEMP)

    ruta = os.path.join(config.CARPETA_TEMP, "generada.jpg")
    with open(ruta, "wb") as archivo:
        archivo.write(respuesta.content)

    return ruta
