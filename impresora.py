import math
import os
from datetime import datetime
from escpos.printer import Usb
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
import config

try:
    import cv2
    import numpy as np
except ImportError:      # sin OpenCV se omite solo el contraste local
    cv2 = None
    np = None

CARPETA_PROYECTO = os.path.dirname(os.path.abspath(__file__))

K = 3          # el marco se dibuja 3 veces más grande y luego se reduce: bordes suaves
INTERIOR = 48  # espacio, a cada lado, entre el borde del papel y la foto
LINEA = 26     # distancia del borde del papel a la línea del marco
MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]


def _p(valor):
    """Pasa una medida normal a la medida ampliada con la que se dibuja."""
    return int(round(valor * K))


def _ajuste(nombre, por_defecto):
    return getattr(config, nombre, por_defecto)


# ---------- tipografías ----------

def _fuente(ruta_config, tamano):
    """Busca la letra en la carpeta del proyecto; si no está, usa DejaVu."""
    candidatos = [
        os.path.join(CARPETA_PROYECTO, ruta_config),                          # fuentes/Lora-BoldItalic.ttf
        os.path.join(CARPETA_PROYECTO, os.path.basename(ruta_config)),        # o suelta en la carpeta principal
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for ruta in candidatos:
        try:
            return ImageFont.truetype(ruta, _p(tamano))
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=_p(tamano))
    except TypeError:
        return ImageFont.load_default()


def _alto_texto(medidor, texto, fuente):
    izq, arriba, der, abajo = medidor.textbbox((0, 0), texto, font=fuente)
    return int(math.ceil((abajo - arriba) / K))


def _dibujar_texto(d, texto, centro_x, y_arriba, fuente, espaciado=0):
    """Dibuja el texto centrado, con su parte de arriba en y_arriba.
    Devuelve (ancho, alto) en medidas normales."""
    izq, arriba, der, abajo = d.textbbox((0, 0), texto, font=fuente)
    if espaciado and len(texto) > 1:
        ancho = sum(fuente.getlength(c) for c in texto) + _p(espaciado) * (len(texto) - 1)
        x = _p(centro_x) - ancho / 2
        for letra in texto:
            d.text((x, _p(y_arriba) - arriba), letra, font=fuente, fill=0)
            x += fuente.getlength(letra) + _p(espaciado)
    else:
        ancho = der - izq
        d.text((_p(centro_x) - ancho / 2 - izq, _p(y_arriba) - arriba), texto, font=fuente, fill=0)
    return ancho / K, (abajo - arriba) / K


# ---------- adornos ----------

def _corazon(d, cx, cy, tam):
    puntos = []
    for i in range(60):
        t = 2 * math.pi * i / 60
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        puntos.append((_p(cx + x * tam / 32), _p(cy - y * tam / 32)))
    d.polygon(puntos, fill=0)


def _petalo(cx, cy, ang, largo, ancho):
    puntos = []
    for i in range(28):
        t = 2 * math.pi * i / 28
        x = largo / 2 + math.cos(t) * largo / 2
        y = math.sin(t) * ancho / 2
        puntos.append((cx + x * math.cos(ang) - y * math.sin(ang),
                       cy + x * math.sin(ang) + y * math.cos(ang)))
    return puntos


def _flor(d, cx, cy, r, petalos=6, giro=0.0):
    """Pétalos blancos con contorno negro y el centro negro."""
    for k in range(petalos):
        ang = giro + 2 * math.pi * k / petalos
        pts = [(_p(x), _p(y)) for x, y in _petalo(cx, cy, ang, r, r * 0.66)]
        d.polygon(pts, fill=255)
        d.line(pts + [pts[0]], fill=0, width=_p(1.5), joint="curve")
    rc = r * 0.26
    d.ellipse([_p(cx - rc), _p(cy - rc), _p(cx + rc), _p(cy + rc)], fill=0)


def _flor_grande(d, cx, cy, r):
    _flor(d, cx, cy, r, petalos=8)
    _flor(d, cx, cy, r * 0.62, petalos=8, giro=math.pi / 8)


def _hoja(d, cx, cy, ang, largo, ancho):
    n = 14
    lado = [(largo * (1 - math.cos(math.pi * i / n)) / 2,
             (ancho / 2) * math.sin(math.pi * i / n)) for i in range(n + 1)]
    contorno = lado + [(x, -y) for x, y in reversed(lado)]
    puntos = [(_p(cx + x * math.cos(ang) - y * math.sin(ang)),
               _p(cy + x * math.sin(ang) + y * math.cos(ang))) for x, y in contorno]
    d.polygon(puntos, fill=0)


def _ramita(d, cx, cy, ang):
    """Dos hojitas que salen de un mismo punto, formando una V."""
    _hoja(d, cx, cy, ang - 0.65, 21, 8)
    _hoja(d, cx, cy, ang + 0.65, 21, 8)


def _guirnalda(d, x1, y1, x2, y2, r):
    """Flores en línea recta de (x1, y1) a (x2, y2), con ramitas entre ellas."""
    largo = math.hypot(x2 - x1, y2 - y1)
    cantidad = max(2, int(round(largo / 74)) + 1)
    ang = math.atan2(y2 - y1, x2 - x1)
    puntos = [(x1 + (x2 - x1) * i / (cantidad - 1), y1 + (y2 - y1) * i / (cantidad - 1))
              for i in range(cantidad)]
    for i in range(cantidad - 1):
        mx = (puntos[i][0] + puntos[i + 1][0]) / 2 - 9 * math.cos(ang)
        my = (puntos[i][1] + puntos[i + 1][1]) / 2 - 9 * math.sin(ang)
        _ramita(d, mx, my, ang)
    for x, y in puntos:
        _flor(d, x, y, r, petalos=6)


# ---------- la foto y el marco ----------

def _mejorar_tonos(gris):
    """
    Prepara la foto (en escala de grises) para el papel térmico:
    1) contraste local: rescata caras oscuras cuando hay luz de fondo.
    2) aclara los tonos medios: los puntos del papel térmico se "riegan" y
       oscurecen la imagen, así que se compensa de antemano.
    3) estira el contraste y 4) afina los bordes antes de pasar a puntitos.
    """
    local = float(_ajuste("CONTRASTE_LOCAL", 2.0))
    if local > 0 and cv2 is not None:
        suave = cv2.bilateralFilter(np.array(gris), 5, 35, 5)     # quita un poco de ruido sin borrar bordes
        clahe = cv2.createCLAHE(clipLimit=local, tileGridSize=(4, 4))
        gris = Image.fromarray(clahe.apply(suave))

    gamma = float(_ajuste("GAMMA_IMPRESION", 0.75))
    tabla = [int(round(255 * (i / 255) ** gamma)) for i in range(256)]
    gris = gris.point(tabla)

    gris = ImageOps.autocontrast(gris, cutoff=1)
    return gris.filter(ImageFilter.UnsharpMask(radius=1.4, percent=110, threshold=2))


def _foto_en_blanco_y_negro(ruta_imagen, ancho):
    """
    Abre la foto, la redimensiona al ancho pedido (manteniendo la proporción),
    la mejora y la convierte a blanco y negro con puntitos (tramado),
    que es lo que mejor se ve en papel térmico.
    """
    foto = Image.open(ruta_imagen).convert("L")
    alto = int(foto.height * ancho / foto.width)
    foto = foto.resize((ancho, alto), Image.LANCZOS)
    if _ajuste("MEJORAR_FOTO", True):
        foto = _mejorar_tonos(foto)
    else:
        foto = ImageOps.autocontrast(foto)
    return foto.convert("1")


def _texto_fecha():
    texto = str(_ajuste("FECHA_TEXTO", "")).strip()
    if texto:
        return texto
    hoy = datetime.now()
    return str(hoy.day) + " " + MESES[hoy.month - 1] + " " + str(hoy.year)


def _poner_marco(foto_bn):
    """Rodea la foto con flores, corazones y los textos de arriba y de abajo."""
    W = config.ANCHO_IMPRESION
    ancho_foto = W - 2 * INTERIOR
    alto_foto = foto_bn.height
    cx = W / 2

    f_titulo = _fuente(_ajuste("FUENTE_TITULO", "fuentes/Lora-BoldItalic.ttf"), 62)
    f_texto = _fuente(_ajuste("FUENTE_TEXTO", "fuentes/Poppins-Medium.ttf"), 26)
    f_fecha = _fuente(_ajuste("FUENTE_TEXTO", "fuentes/Poppins-Medium.ttf"), 20)
    texto_arriba = _ajuste("TEXTO_SUPERIOR", "Metie 2026")
    texto_abajo = _ajuste("TEXTO_INFERIOR", "FOTOBOOTH")
    con_fecha = _ajuste("MOSTRAR_FECHA", True)
    fecha = _texto_fecha()

    medidor = ImageDraw.Draw(Image.new("L", (10, 10)))
    alto_titulo = _alto_texto(medidor, texto_arriba, f_titulo)
    alto_abajo = _alto_texto(medidor, texto_abajo, f_texto)
    alto_fecha = _alto_texto(medidor, fecha, f_fecha) if con_fecha else 0

    # posiciones de arriba hacia abajo
    y_titulo = 50
    y_div1 = y_titulo + alto_titulo + 24
    y_foto = y_div1 + 25
    y_div2 = y_foto + alto_foto + 25
    y_abajo = y_div2 + 25
    y_fecha = y_abajo + alto_abajo + 10
    y_fin = (y_fecha + alto_fecha) if con_fecha else (y_abajo + alto_abajo)
    H = y_fin + 50

    arte = Image.new("L", (_p(W), _p(H)), 255)
    d = ImageDraw.Draw(arte)

    # línea del marco y flores
    d.rectangle([_p(LINEA), _p(LINEA), _p(W - 1 - LINEA), _p(H - 1 - LINEA)],
                outline=0, width=_p(3))
    inicio = LINEA + 42
    _guirnalda(d, inicio, LINEA, W - 1 - inicio, LINEA, 14)
    _guirnalda(d, inicio, H - 1 - LINEA, W - 1 - inicio, H - 1 - LINEA, 14)
    _guirnalda(d, LINEA, inicio, LINEA, H - 1 - inicio, 14)
    _guirnalda(d, W - 1 - LINEA, inicio, W - 1 - LINEA, H - 1 - inicio, 14)
    for x, y in [(LINEA, LINEA), (W - 1 - LINEA, LINEA),
                 (LINEA, H - 1 - LINEA), (W - 1 - LINEA, H - 1 - LINEA)]:
        _flor_grande(d, x, y, 24)

    # título con corazones
    ancho_t, _ = _dibujar_texto(d, texto_arriba, cx, y_titulo, f_titulo)
    cy_t = y_titulo + alto_titulo / 2
    _corazon(d, cx - ancho_t / 2 - 30, cy_t, 22)
    _corazon(d, cx + ancho_t / 2 + 30, cy_t, 22)

    # divisores con una florecita en el centro
    for y in (y_div1, y_div2):
        d.rectangle([_p(INTERIOR), _p(y - 1), _p(cx - 22), _p(y + 1)], fill=0)
        d.rectangle([_p(cx + 22), _p(y - 1), _p(W - 1 - INTERIOR), _p(y + 1)], fill=0)
        _flor(d, cx, y, 10, petalos=5)

    # texto de abajo y fecha
    ancho_i, _ = _dibujar_texto(d, texto_abajo, cx, y_abajo, f_texto, espaciado=5)
    cy_i = y_abajo + alto_abajo / 2
    _corazon(d, cx - ancho_i / 2 - 24, cy_i, 14)
    _corazon(d, cx + ancho_i / 2 + 24, cy_i, 14)
    if con_fecha:
        _dibujar_texto(d, fecha, cx, y_fecha, f_fecha, espaciado=3)

    # se reduce a tamaño real y todo queda en puro blanco y negro
    base = arte.resize((W, H), Image.LANCZOS).point(lambda p: 255 if p >= 170 else 0)
    base.paste(foto_bn.convert("L"), (INTERIOR, y_foto))
    ImageDraw.Draw(base).rectangle(
        [INTERIOR - 4, y_foto - 4, INTERIOR + ancho_foto + 3, y_foto + alto_foto + 3],
        outline=0, width=2)
    return base.convert("1")


def preparar_imagen(ruta_imagen):
    """
    Deja la imagen lista para imprimir: al ancho del papel, en blanco y
    negro con tramado y, si USAR_MARCO es True, con el marco de flores.
    """
    if not _ajuste("USAR_MARCO", True):
        return _foto_en_blanco_y_negro(ruta_imagen, config.ANCHO_IMPRESION)

    ancho_foto = config.ANCHO_IMPRESION - 2 * INTERIOR
    return _poner_marco(_foto_en_blanco_y_negro(ruta_imagen, ancho_foto))


def abrir_impresora():
    return Usb(
        config.VENDOR_ID,
        config.PRODUCT_ID,
        out_ep=config.USB_OUT_EP,
        in_ep=config.USB_IN_EP,
    )


def cerrar_impresora(impresora):
    """
    Libera el USB. Sin esto, la conexión queda abierta y la SIGUIENTE
    impresión falla con "[Errno 16] Resource busy".
    """
    try:
        impresora.close()
    except Exception:
        pass


def imprimir_imagen(ruta_imagen):
    """
    Manda una imagen (foto o generada por IA, de cualquier tamaño)
    a la impresora térmica y corta el papel.
    """
    imagen = preparar_imagen(ruta_imagen)
    impresora = abrir_impresora()
    try:
        impresora.image(imagen)
        impresora.text("\n\n")
        impresora.cut()
    finally:
        cerrar_impresora(impresora)


def imprimir_texto(texto):
    """
    Manda texto simple a la impresora y corta el papel.
    Útil para pruebas rápidas.
    """
    impresora = abrir_impresora()
    try:
        impresora.text(texto)
        impresora.cut()
    finally:
        cerrar_impresora(impresora)
