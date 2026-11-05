# Todo lo que se ve en pantalla: menú, vista de la cámara con la cuenta
# regresiva, mensajes y el resultado.
#
# Dibuja siempre una imagen del tamaño de la pantalla (ANCHO_PANTALLA x
# ALTO_PANTALLA de config.py) y la manda a:
#   - la pantalla TFT por SPI (TIPO_PANTALLA = "spi"), o
#   - una ventana del escritorio (TIPO_PANTALLA = "ventana").
# Si la pantalla SPI no arranca, se usa la ventana y se avisa por qué.

import math
import os
import select
import sys
import time

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

import boton
import captura
import config

NOMBRE_VENTANA = "Fotobooth"
CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))

# Lo devuelve la vista de la cámara si se cancela o si pasó mucho tiempo sin tocar el botón
CANCELADO = "cancelado"

OSCURO = (84, 38, 96)        # morado oscuro para los textos
BLANCO = (255, 255, 255)

_pantalla_spi = None         # la pantalla SPI, si se pudo iniciar
_ventana_abierta = False    # True si se está usando una ventana del escritorio
_fondo = None                # fondo ya preparado (se calcula una sola vez)
_menu = None                 # menú ya preparado
_fuentes = {}


# ---------------------------------------------------------------- arranque

def inicializar():
    """Prepara la pantalla. Llamar una vez al empezar."""
    global _pantalla_spi, _ventana_abierta
    if config.TIPO_PANTALLA == "spi":
        try:
            import pantalla_spi
            nueva = pantalla_spi.PantallaSPI()
            nueva.iniciar()
            _pantalla_spi = nueva
        except Exception as error:
            print("No se pudo iniciar la pantalla SPI:", error)
            print("Se usará una ventana en el escritorio.")
            _pantalla_spi = None

    if _pantalla_spi is None:
        cv2.namedWindow(NOMBRE_VENTANA, cv2.WINDOW_NORMAL)
        ancho, alto = _medidas()
        factor = 2 if ancho <= 400 else 1
        cv2.resizeWindow(NOMBRE_VENTANA, ancho * factor, alto * factor)
        _ventana_abierta = True


# alias del nombre anterior, por si algún archivo viejo lo usa
inicializar_ventana = inicializar


def cerrar():
    """Apaga la pantalla y cierra la ventana."""
    global _pantalla_spi, _ventana_abierta
    if _pantalla_spi is not None:
        _pantalla_spi.apagar()
        _pantalla_spi = None
    if _ventana_abierta:
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass
        _ventana_abierta = False


def _medidas():
    return config.ANCHO_PANTALLA, config.ALTO_PANTALLA


def _presentar(imagen):
    """
    Manda una imagen RGB (PIL o numpy) a la pantalla.
    En modo ventana devuelve la tecla que se presionó (o None).
    """
    matriz = np.asarray(imagen)
    if _pantalla_spi is not None:
        _pantalla_spi.mostrar(matriz)
        return None
    cv2.imshow(NOMBRE_VENTANA, cv2.cvtColor(matriz, cv2.COLOR_RGB2BGR))
    k = cv2.waitKey(1) & 0xFF
    return chr(k).lower() if 0 < k < 255 else None


def _esperar(segundos):
    if _pantalla_spi is None:
        cv2.waitKey(int(segundos * 1000))
    else:
        time.sleep(segundos)


# ---------------------------------------------------------------- dibujo

def _fuente(ruta_config, tamano):
    tamano = max(8, int(round(tamano)))
    clave = (ruta_config, tamano)
    if clave not in _fuentes:
        fuente = None
        for ruta in (os.path.join(CARPETA_PROYECTO, ruta_config),
                     os.path.join(CARPETA_PROYECTO, os.path.basename(ruta_config)),
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            try:
                fuente = ImageFont.truetype(ruta, tamano)
                break
            except OSError:
                continue
        if fuente is None:
            fuente = ImageFont.load_default(size=tamano)
        _fuentes[clave] = fuente
    return _fuentes[clave]


def _f_titulo(tamano):
    return _fuente(config.FUENTE_TITULO, tamano)


def _f_texto(tamano):
    return _fuente(config.FUENTE_TEXTO, tamano)


def _cubrir(imagen, ancho, alto):
    """Agranda la imagen hasta llenar el tamaño y recorta lo que sobre (al centro)."""
    return ImageOps.fit(imagen, (ancho, alto), method=Image.LANCZOS, centering=(0.5, 0.5))


def _degradado(ancho, alto):
    arriba = np.array([255, 218, 235], dtype=float)
    abajo = np.array([228, 190, 242], dtype=float)
    t = np.linspace(0, 1, alto)[:, None, None]
    matriz = (arriba * (1 - t) + abajo * t) * np.ones((1, ancho, 1))
    return Image.fromarray(matriz.astype("uint8"), "RGB")


def _cargar_propia(nombre):
    """Abre una imagen propia (fondo.png / menu.png) si existe; si no, None."""
    ruta = os.path.join(CARPETA_PROYECTO, nombre)
    if not os.path.exists(ruta):
        return None
    try:
        ancho, alto = _medidas()
        return _cubrir(Image.open(ruta).convert("RGB"), ancho, alto)
    except Exception as error:
        print("No se pudo abrir", nombre, ":", error)
        return None


def _obtener_fondo():
    global _fondo
    if _fondo is None:
        _fondo = _cargar_propia(config.RUTA_FONDO)
        if _fondo is None:
            _fondo = _degradado(*_medidas())
    return _fondo.copy()


def _texto(d, texto, cx, cy, fuente, color=OSCURO, contorno=None, grosor=0, espaciado=0):
    """Escribe el texto centrado en (cx, cy)."""
    extra = {}
    if contorno is not None and grosor:
        extra = {"stroke_width": grosor, "stroke_fill": contorno}
    if espaciado and len(texto) > 1:
        anchos = [fuente.getlength(c) for c in texto]
        x = cx - (sum(anchos) + espaciado * (len(texto) - 1)) / 2
        for letra, ancho in zip(texto, anchos):
            d.text((x, cy), letra, font=fuente, fill=color, anchor="lm", **extra)
            x += ancho + espaciado
    else:
        d.text((cx, cy), texto, font=fuente, fill=color, anchor="mm", **extra)


def _partir(texto, fuente, ancho_max):
    """Parte un texto largo en renglones que quepan en ancho_max."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if actual and fuente.getlength(prueba) > ancho_max:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    return lineas


def _corazon(d, cx, cy, tam, color):
    puntos = []
    for i in range(48):
        t = 2 * math.pi * i / 48
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        puntos.append((cx + x * tam / 32, cy - y * tam / 32))
    d.polygon(puntos, fill=color)


def _icono_camara(d, cx, cy, s, color):
    grosor = max(2, int(s * 0.18))
    d.rectangle([cx - s * 0.45, cy - s * 0.95, cx - s * 0.05, cy - s * 0.6], fill=color)
    d.rounded_rectangle([cx - s, cy - s * 0.65, cx + s, cy + s * 0.75],
                        radius=s * 0.25, outline=color, width=grosor)
    d.ellipse([cx - s * 0.4, cy - s * 0.28, cx + s * 0.4, cy + s * 0.52],
              outline=color, width=grosor)


def _estrella(d, cx, cy, s, color):
    d.polygon([(cx, cy - s), (cx + s * 0.28, cy - s * 0.28), (cx + s, cy),
               (cx + s * 0.28, cy + s * 0.28), (cx, cy + s), (cx - s * 0.28, cy + s * 0.28),
               (cx - s, cy), (cx - s * 0.28, cy - s * 0.28)], fill=color)


def _icono_ia(d, cx, cy, s, color):
    _estrella(d, cx - s * 0.2, cy + s * 0.1, s * 0.8, color)
    _estrella(d, cx + s * 0.62, cy - s * 0.58, s * 0.38, color)


def _dibujar_menu():
    """El menú: el diseño propio (menu.png) o uno que se dibuja solo."""
    global _menu
    if _menu is not None:
        return _menu.copy()

    propio = _cargar_propia(config.RUTA_MENU)
    if propio is not None:
        _menu = propio
        return _menu.copy()

    ancho, alto = _medidas()
    img = _obtener_fondo()
    d = ImageDraw.Draw(img, "RGBA")

    _texto(d, config.TEXTO_SUPERIOR, ancho / 2, alto * 0.17, _f_titulo(alto * 0.17))
    _corazon(d, ancho * 0.10, alto * 0.17, alto * 0.09, OSCURO)
    _corazon(d, ancho * 0.90, alto * 0.17, alto * 0.09, OSCURO)
    _texto(d, config.TEXTO_INFERIOR, ancho / 2, alto * 0.325, _f_texto(alto * 0.062),
           espaciado=alto * 0.02)

    tarjetas = [(_icono_camara, "Toque corto: foto"),
                (_icono_ia, "Mantén presionado: IA")]
    alto_t = alto * 0.19
    for i, (icono, texto) in enumerate(tarjetas):
        cy = alto * (0.55 + 0.22 * i)
        x0, x1 = ancho * 0.08, ancho * 0.92
        d.rounded_rectangle([x0, cy - alto_t / 2, x1, cy + alto_t / 2], radius=alto_t / 2,
                            fill=(255, 255, 255, 225), outline=OSCURO, width=2)
        icono(d, x0 + alto_t * 0.62, cy, alto_t * 0.30, OSCURO)
        _texto(d, texto, (x0 + alto_t * 1.15 + x1 - alto_t * 0.3) / 2, cy, _f_texto(alto * 0.068))

    _menu = img
    return _menu.copy()


def _dibujar_mensaje(texto, subtexto=""):
    ancho, alto = _medidas()
    img = _obtener_fondo()
    d = ImageDraw.Draw(img, "RGBA")

    f_principal = _f_titulo(alto * 0.115)
    lineas = _partir(texto, f_principal, ancho * 0.86)[:3]
    paso = alto * 0.135
    arriba = alto * (0.40 if subtexto else 0.5) - paso * (len(lineas) - 1) / 2
    for i, linea in enumerate(lineas):
        _texto(d, linea, ancho / 2, arriba + paso * i, f_principal)

    if subtexto:
        f_sub = _f_texto(alto * 0.06)
        sub = _partir(subtexto, f_sub, ancho * 0.84)[:3]
        y0 = arriba + paso * (len(lineas) - 1) + alto * 0.17
        for i, linea in enumerate(sub):
            _texto(d, linea, ancho / 2, y0 + alto * 0.08 * i, f_sub)
    return img


# ------------------------------------------------------------- pantallas

def mostrar_menu_y_esperar():
    """
    Muestra el menú y espera. Devuelve "foto", "ia" o "salir".
    Con el botón: toque corto = foto, mantenerlo = IA.
    Con el teclado (para probar): 1 = foto, 2 = IA, q = salir
    (con la pantalla SPI se escribe en la terminal y Enter).
    """
    boton.revisar_accion()          # descarta pulsaciones viejas
    menu = _dibujar_menu()
    _presentar(menu)

    while True:
        accion = boton.revisar_accion()
        if accion is not None:
            return accion

        tecla = _leer_tecla()
        if tecla == "1":
            return "foto"
        if tecla == "2":
            return "ia"
        if tecla == "q":
            return "salir"

        if _pantalla_spi is None:
            _presentar(menu)        # mantiene viva la ventana


def _tecla_terminal():
    """Con la pantalla SPI: una tecla escrita en la terminal (más Enter), sin esperar. None si no hay."""
    try:
        if select.select([sys.stdin], [], [], 0)[0]:
            linea = sys.stdin.readline().strip().lower()
            return linea[:1] or None
    except (ValueError, OSError):
        pass
    return None


def _leer_tecla():
    if _pantalla_spi is None:
        k = cv2.waitKey(30) & 0xFF
        return chr(k).lower() if 0 < k < 255 else None

    time.sleep(0.03)
    return _tecla_terminal()


def mostrar_mensaje(texto, subtexto="", segundos=None):
    """Muestra un mensaje. Si se da "segundos", se queda esa cantidad de tiempo."""
    _presentar(_dibujar_mensaje(texto, subtexto))
    if segundos is not None:
        _esperar(segundos)


def _cubrir_cuadro(cuadro, ancho, alto):
    """Ajusta un cuadro de la cámara (BGR) al tamaño de la pantalla, recortando lo que sobre."""
    h, w = cuadro.shape[:2]
    escala = max(ancho / w, alto / h)
    nuevo_w = max(ancho, int(round(w * escala)))
    nuevo_h = max(alto, int(round(h * escala)))
    chico = cv2.resize(cuadro, (nuevo_w, nuevo_h), interpolation=cv2.INTER_AREA)
    x = (nuevo_w - ancho) // 2
    y = (nuevo_h - alto) // 2
    return chico[y:y + alto, x:x + ancho]


def _vista_de_camara(cuadro, ancho, alto):
    """El cuadro de la cámara ajustado a la pantalla (y como espejo, si está activado)."""
    vista = cv2.cvtColor(_cubrir_cuadro(cuadro, ancho, alto), cv2.COLOR_BGR2RGB)
    if getattr(config, "PANTALLA_ESPEJO", True):
        vista = cv2.flip(vista, 1)
    return Image.fromarray(vista)


def mostrar_vista_previa_con_conteo(segundos_totales=None):
    """
    La cámara en dos fases:
      1) Se ve lo que ve la cámara y se espera OTRO toque del botón (o la tecla 1).
      2) Con ese toque empieza la cuenta regresiva, hay un destello y se toma la foto.

    Devuelve:
      - el cuadro capturado (el promedio de los últimos cuadros, con menos ruido),
        sin guardarlo todavía;
      - CANCELADO si se mantuvo presionado el botón (o la tecla q), o si pasó
        TIEMPO_MAX_VISTA_PREVIA sin tocarlo;
      - None si la cámara falla.
    """
    if segundos_totales is None:
        segundos_totales = config.SEGUNDOS_CUENTA_REGRESIVA

    camara = captura.abrir_camara()
    if camara is None:
        return None

    ancho, alto = _medidas()
    f_numero = _f_titulo(alto * 0.36)
    f_aviso = _f_texto(alto * 0.07)
    f_chico = _f_texto(alto * 0.05)
    f_sonrie = _f_texto(alto * 0.075)
    ultimos = []

    def leer():
        """Un cuadro nuevo de la cámara (recortado a 4:3), o None si falla."""
        ok, cuadro = camara.read()
        if not ok:
            return None
        cuadro = captura.recortar_4_3(cuadro)
        ultimos.append(cuadro)
        if len(ultimos) > config.CUADROS_A_PROMEDIAR:
            ultimos.pop(0)
        return cuadro

    # ---- fase 1: ver la cámara y esperar el toque ----
    boton.revisar_accion()               # descarta pulsaciones viejas
    limite = float(getattr(config, "TIEMPO_MAX_VISTA_PREVIA", 90))
    inicio_vista = time.time()

    while True:
        cuadro = leer()
        if cuadro is None:
            camara.release()
            return None
        if time.time() - inicio_vista > limite:
            camara.release()
            return CANCELADO

        img = _vista_de_camara(cuadro, ancho, alto)
        d = ImageDraw.Draw(img, "RGBA")
        _texto(d, "Encuadra tu foto", ancho / 2, alto * 0.08, f_sonrie, BLANCO, OSCURO, 2)
        _texto(d, "Toca el botón para empezar", ancho / 2, alto * 0.83, f_aviso, BLANCO, OSCURO, 2)
        _texto(d, "Mantén presionado para volver", ancho / 2, alto * 0.92, f_chico, BLANCO, OSCURO, 2)
        tecla = _presentar(img) or _tecla_terminal()

        accion = boton.revisar_accion()
        if accion == "foto" or tecla == "1":
            break
        if accion == "ia" or tecla == "q":
            camara.release()
            return CANCELADO

    # ---- fase 2: cuenta regresiva y foto ----
    inicio = time.time()
    cuadro_final = None

    while True:
        cuadro = leer()
        if cuadro is None:
            break

        restantes = segundos_totales - int(time.time() - inicio)
        if restantes <= 0:
            cuadro_final = captura.promediar(ultimos)
            break

        img = _vista_de_camara(cuadro, ancho, alto)
        d = ImageDraw.Draw(img, "RGBA")
        # el número va en la esquina de abajo para no tapar la cara
        cx, cy, radio = ancho * 0.85, alto * 0.76, alto * 0.19
        d.ellipse([cx - radio, cy - radio, cx + radio, cy + radio], fill=(84, 38, 96, 170))
        _texto(d, str(restantes), cx, cy, f_numero, BLANCO, OSCURO, 2)
        _texto(d, "¡Sonríe!", ancho / 2, alto * 0.09, f_sonrie, BLANCO, OSCURO, 2)
        _presentar(img)

    camara.release()
    boton.revisar_accion()               # ignora lo que se presionó durante la cuenta

    if cuadro_final is not None:         # destello de la foto
        _presentar(np.full((alto, ancho, 3), 255, dtype=np.uint8))
        _esperar(0.08)
    return cuadro_final


def guardar_captura(cuadro):
    """
    Guarda un cuadro capturado en la carpeta temporal.
    Devuelve la ruta del archivo.
    """
    if not os.path.exists(config.CARPETA_TEMP):
        os.makedirs(config.CARPETA_TEMP)
    ruta = os.path.join(config.CARPETA_TEMP, "foto.jpg")
    cv2.imwrite(ruta, cuadro)
    return ruta


def mostrar_imagen_resultado(ruta_imagen, texto="¡Listo!"):
    """Muestra una imagen ya guardada (foto o imagen de IA) con un texto abajo."""
    try:
        foto = Image.open(ruta_imagen).convert("RGB")
    except Exception:
        mostrar_mensaje("No se pudo mostrar la imagen", segundos=2)
        return

    ancho, alto = _medidas()
    img = _obtener_fondo()
    d = ImageDraw.Draw(img, "RGBA")

    escala = min(ancho * 0.90 / foto.width, alto * 0.78 / foto.height)
    tam = (max(1, int(foto.width * escala)), max(1, int(foto.height * escala)))
    foto = foto.resize(tam, Image.LANCZOS)
    x = (ancho - tam[0]) // 2
    y = int(alto * 0.04)
    d.rectangle([x - 3, y - 3, x + tam[0] + 2, y + tam[1] + 2], fill=BLANCO)
    img.paste(foto, (x, y))
    _texto(d, texto, ancho / 2, alto * 0.91, _f_titulo(alto * 0.085))
    _presentar(img)
