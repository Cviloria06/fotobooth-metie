# Modo IA: escucha lo que dices por el micrófono y crea la imagen con IA.
#
#   escuchar_descripcion() -> graba con el micrófono (arecord) y transcribe la voz a texto
#   generar_imagen(texto)  -> crea la imagen y la guarda en temp/generada.jpg
#                             con Pollinations (gratis, sin clave) o con Gemini (de pago),
#                             según PROVEEDOR_IA en config.py
#
# Si algo falla se lanza ErrorIA: "detalle" es para la terminal (qué pasó de verdad)
# y "corto" es el aviso que se muestra en la pantalla pequeña.

import io
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import wave

import numpy as np

import config

CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))


class ErrorIA(Exception):
    def __init__(self, detalle, corto="Intenta de nuevo"):
        super().__init__(detalle)
        self.detalle = detalle
        self.corto = corto


def _ajuste(nombre, por_defecto):
    return getattr(config, nombre, por_defecto)


# ------------------------------------------------------------ micrófono

def _dispositivo_microfono():
    """Devuelve el dispositivo de ALSA a usar. "auto" = la primera tarjeta de captura."""
    elegido = str(_ajuste("MICROFONO_DISPOSITIVO", "auto")).strip()
    if elegido and elegido != "auto":
        return elegido

    try:
        entorno = dict(os.environ, LC_ALL="C")
        salida = subprocess.run(["arecord", "-l"], capture_output=True, text=True,
                                timeout=5, env=entorno).stdout
    except FileNotFoundError:
        raise ErrorIA("No existe el programa arecord. Instálalo con: sudo apt install alsa-utils",
                      "Micrófono no disponible")
    except subprocess.TimeoutExpired:
        raise ErrorIA("arecord -l no respondió.", "Micrófono no disponible")

    tarjetas = re.findall(r"card (\d+):.*?device (\d+):", salida)
    if not tarjetas:
        raise ErrorIA("No se encontró ningún micrófono. Revisa con: arecord -l",
                      "No encuentro el micrófono")
    tarjeta, dispositivo = tarjetas[0]
    return "plughw:%s,%s" % (tarjeta, dispositivo)


def grabar_audio(ruta, segundos):
    """Graba 'segundos' de audio (16 kHz, mono) en un archivo WAV."""
    dispositivo = _dispositivo_microfono()
    comando = ["arecord", "-q", "-D", dispositivo, "-f", "S16_LE", "-r", "16000",
               "-c", "1", "-d", str(int(segundos)), ruta]
    try:
        resultado = subprocess.run(comando, capture_output=True, text=True,
                                   timeout=segundos + 10)
    except subprocess.TimeoutExpired:
        raise ErrorIA("La grabación se quedó trabada.", "Micrófono no disponible")
    if resultado.returncode != 0:
        raise ErrorIA("arecord falló con " + dispositivo + ": " + resultado.stderr.strip(),
                      "Micrófono no disponible")
    return dispositivo


def nivel_audio(ruta):
    """Devuelve (volumen_medio, pico) del WAV, en una escala de 0 a 32767."""
    with wave.open(ruta, "rb") as archivo:
        datos = np.frombuffer(archivo.readframes(archivo.getnframes()), dtype=np.int16)
    if datos.size == 0:
        return 0, 0
    datos = datos.astype(np.float64)
    return float(np.sqrt(np.mean(datos ** 2))), float(np.max(np.abs(datos)))


def _subir_volumen(ruta, pico):
    """Los micrófonos de las webcams suenan bajito: se sube el volumen hasta un nivel normal."""
    objetivo = 20000.0
    if pico <= 0 or pico >= objetivo:
        return
    ganancia = min(8.0, objetivo / pico)
    with wave.open(ruta, "rb") as archivo:
        parametros = archivo.getparams()
        datos = np.frombuffer(archivo.readframes(archivo.getnframes()), dtype=np.int16)
    fuerte = np.clip(datos.astype(np.float64) * ganancia, -32768, 32767).astype(np.int16)
    with wave.open(ruta, "wb") as salida:
        salida.setparams(parametros)
        salida.writeframes(fuerte.tobytes())


def transcribir(ruta):
    """Convierte un WAV a texto con el reconocimiento de voz de Google. None si no se entendió."""
    import speech_recognition as sr

    reconocedor = sr.Recognizer()
    with sr.AudioFile(ruta) as fuente:
        audio = reconocedor.record(fuente)
    try:
        return reconocedor.recognize_google(audio, language=_ajuste("IDIOMA_VOZ", "es-CO"))
    except OSError as error:
        # En la Raspberry la librería necesita el programa "flac" para enviar el audio
        raise ErrorIA("Falta el programa flac (" + str(error) + "). Instálalo con: sudo apt install flac",
                      "Falta instalar flac")
    except sr.UnknownValueError:
        print("No se entendió el audio.")
        return None
    except sr.RequestError as error:
        raise ErrorIA("Error con el reconocimiento de voz: " + str(error), "Revisa el internet")


def escuchar_descripcion():
    """
    Graba la voz y la convierte a texto.
    Devuelve el texto, o None si nadie habló o no se entendió.
    Lanza ErrorIA si el micrófono no funciona o no hay internet.
    """
    if not os.path.exists(config.CARPETA_TEMP):
        os.makedirs(config.CARPETA_TEMP)
    ruta = os.path.join(config.CARPETA_TEMP, "voz.wav")

    grabar_audio(ruta, _ajuste("MICROFONO_SEGUNDOS", 6))
    volumen, pico = nivel_audio(ruta)
    print("Volumen de la grabación: medio %d, pico %d" % (volumen, pico))

    if pico < _ajuste("MICROFONO_UMBRAL_SILENCIO", 400):
        print("No se oyó nada (volumen muy bajo). Habla más cerca del micrófono.")
        return None

    _subir_volumen(ruta, pico)
    return transcribir(ruta)


# ---------------------------------------------------------------- Gemini

def _leer_clave():
    """
    Busca la clave de Gemini en el archivo clave_gemini.txt (junto al programa) o,
    si no está, en la variable GEMINI_API_KEY. Va en un archivo porque "sudo" no
    hereda las variables de entorno.
    """
    ruta = os.path.join(CARPETA_PROYECTO, _ajuste("ARCHIVO_CLAVE_GEMINI", "clave_gemini.txt"))
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as archivo:
            texto = archivo.read().strip()
        if texto:
            return texto
    for variable in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        if os.environ.get(variable, "").strip():
            return os.environ[variable].strip()
    raise ErrorIA("No hay clave de Gemini. Crea el archivo " + ruta + " y pega la clave dentro.",
                  "Falta la clave de Gemini")


def _configuracion(types):
    modalidades = ["TEXT", "IMAGE"]
    try:
        return types.GenerateContentConfig(
            response_modalities=modalidades,
            image_config=types.ImageConfig(aspect_ratio=_ajuste("GEMINI_PROPORCION", "3:4")),
        )
    except Exception:       # SDK viejo sin image_config: se pide sin proporción
        return types.GenerateContentConfig(response_modalities=modalidades)


def _traducir_error(error):
    """Convierte el error de Gemini en un aviso corto para la pantalla."""
    texto = str(error)
    mayus = texto.upper()
    if "API_KEY_INVALID" in mayus or "API KEY NOT VALID" in mayus or "UNAUTHENTICATED" in mayus:
        corto = "Clave de Gemini inválida"
    elif "RESOURCE_EXHAUSTED" in mayus or "429" in texto or "QUOTA" in mayus:
        corto = "Límite de Gemini alcanzado"
    elif "PERMISSION_DENIED" in mayus or "403" in texto or "BILLING" in mayus:
        corto = "Gemini sin permiso: revisa la facturación"
    elif "TIMEOUT" in mayus or "TIMED OUT" in mayus or "CONNECT" in mayus:
        corto = "Sin conexión con Gemini"
    else:
        corto = "La IA no respondió"
    return ErrorIA("Error de Gemini: " + texto, corto)


def _guardar_imagen(respuesta):
    """Saca la imagen de la respuesta de Gemini y la guarda. Devuelve la ruta."""
    from PIL import Image

    textos = []
    for candidato in (respuesta.candidates or []):
        contenido = getattr(candidato, "content", None)
        for parte in (getattr(contenido, "parts", None) or []):
            datos = getattr(getattr(parte, "inline_data", None), "data", None)
            if datos:
                if not os.path.exists(config.CARPETA_TEMP):
                    os.makedirs(config.CARPETA_TEMP)
                ruta = os.path.join(config.CARPETA_TEMP, "generada.jpg")
                Image.open(io.BytesIO(datos)).convert("RGB").save(ruta, "JPEG", quality=92)
                return ruta
            if getattr(parte, "text", None):
                textos.append(parte.text)

    motivo = " ".join(textos).strip()
    if not motivo:
        motivo = str(getattr(respuesta, "prompt_feedback", "") or "sin explicación")
    raise ErrorIA("Gemini no devolvió ninguna imagen. Dijo: " + motivo[:300],
                  "No se pudo crear esa imagen")


def _generar_gemini(descripcion):
    """
    Le pide a Gemini la imagen y la guarda en temp/generada.jpg.
    Devuelve la ruta. Lanza ErrorIA si algo falla.
    """
    from google import genai
    from google.genai import types

    clave = _leer_clave()
    pedido = _pedido_con_estilo(descripcion)

    cliente = genai.Client(
        api_key=clave,
        http_options=types.HttpOptions(timeout=int(_ajuste("GEMINI_TIMEOUT", 90) * 1000)),
    )
    configuracion = _configuracion(types)

    ultimo = None
    for modelo in _ajuste("GEMINI_MODELOS_IMAGEN", ["gemini-nano-banana-2.1", "gemini-3.1-flash-image"]):
        try:
            respuesta = cliente.models.generate_content(
                model=modelo, contents=[pedido], config=configuracion)
        except Exception as error:
            texto = str(error)
            if "404" in texto or "NOT_FOUND" in texto.upper():
                print("El modelo", modelo, "no existe; se prueba el siguiente.")
                ultimo = error
                continue
            raise _traducir_error(error)
        print("Imagen creada con", modelo)
        return _guardar_imagen(respuesta)

    raise ErrorIA("Ningún modelo de imagen respondió: " + str(ultimo)
                  + ". Revisa GEMINI_MODELOS_IMAGEN en config.py.", "Modelo de IA no disponible")


# ------------------------------------------------------------ Pollinations

def _pedido_con_estilo(descripcion):
    """Lo que dijiste + el estilo de config.py, para que el dibujo salga bien en papel térmico."""
    estilo = str(_ajuste("ESTILO_IA", "")).strip()
    return descripcion.strip().rstrip(".") + "." + ((" " + estilo) if estilo else "")


def _generar_pollinations(descripcion):
    """
    Pide la imagen a Pollinations (gratis, sin clave) y la guarda en temp/generada.jpg.
    El servicio gratis atiende de a una imagen y a veces dice "espera": se reintenta solo.
    """
    texto = urllib.parse.quote(_pedido_con_estilo(descripcion))
    url = ("https://image.pollinations.ai/prompt/" + texto
           + "?width=%d&height=%d&nologo=true" % (_ajuste("POLLINATIONS_ANCHO", 768),
                                                   _ajuste("POLLINATIONS_ALTO", 1024)))
    modelo = str(_ajuste("POLLINATIONS_MODELO", "")).strip()
    if modelo:
        url += "&model=" + urllib.parse.quote(modelo)

    intentos = int(_ajuste("POLLINATIONS_INTENTOS", 3))
    detalle = "sin respuesta"
    for numero in range(1, intentos + 1):
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": "fotobooth-metie"})
            with urllib.request.urlopen(pedido, timeout=_ajuste("POLLINATIONS_TIMEOUT", 90)) as resp:
                tipo = resp.headers.get("Content-Type", "")
                datos = resp.read()
            if "image" in tipo and datos:
                return _guardar_bytes(datos)
            detalle = "respondió algo que no es una imagen (" + tipo + "): " + datos[:200].decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            detalle = "código " + str(error.code) + " " + str(error.reason)
        except Exception as error:
            detalle = str(error)

        print("Pollinations, intento %d de %d falló: %s" % (numero, intentos, detalle))
        if numero < intentos:
            time.sleep(16)      # el servicio gratis deja una imagen cada ~15 segundos

    corto = "Sin conexión con la IA" if "urlopen" in detalle or "Name or service" in detalle else "La IA no respondió"
    raise ErrorIA("Pollinations no devolvió una imagen: " + detalle, corto)


def _guardar_bytes(datos):
    from PIL import Image
    if not os.path.exists(config.CARPETA_TEMP):
        os.makedirs(config.CARPETA_TEMP)
    ruta = os.path.join(config.CARPETA_TEMP, "generada.jpg")
    Image.open(io.BytesIO(datos)).convert("RGB").save(ruta, "JPEG", quality=92)
    return ruta


def generar_imagen(descripcion):
    """Crea la imagen con el proveedor elegido en config.py (PROVEEDOR_IA). Devuelve la ruta."""
    proveedor = str(_ajuste("PROVEEDOR_IA", "pollinations")).strip().lower()
    if proveedor == "gemini":
        return _generar_gemini(descripcion)
    return _generar_pollinations(descripcion)
