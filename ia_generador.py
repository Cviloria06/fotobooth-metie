import speech_recognition as sr
import requests
import os
import urllib.parse
import config


def escuchar_descripcion():
    """
    Graba audio del micrófono y lo convierte a texto.
    Devuelve el texto reconocido, o None si no se entendió nada.
    """
    reconocedor = sr.Recognizer()
    microfono = sr.Microphone()

    with microfono as fuente:
        reconocedor.adjust_for_ambient_noise(fuente)
        audio = reconocedor.listen(fuente, timeout=5, phrase_time_limit=6)

    try:
        texto = reconocedor.recognize_google(audio, language="es-CO")
        return texto
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None


def generar_imagen(descripcion):
    """
    Envía la descripción a Pollinations.ai (gratis, sin API key) y
    guarda la imagen resultante. Devuelve la ruta del archivo.
    """
    texto_codificado = urllib.parse.quote(descripcion)
    url = f"https://image.pollinations.ai/prompt/{texto_codificado}?width=768&height=1024&nologo=true"

    respuesta = requests.get(url, timeout=30)

    if not os.path.exists(config.CARPETA_TEMP):
        os.makedirs(config.CARPETA_TEMP)

    ruta = os.path.join(config.CARPETA_TEMP, "generada.jpg")
    with open(ruta, "wb") as archivo:
        archivo.write(respuesta.content)

    return ruta
