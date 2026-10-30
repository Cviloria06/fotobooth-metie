from escpos.printer import Usb
from PIL import Image, ImageOps
import config


def preparar_imagen(ruta_imagen):
    """
    Abre la imagen, la redimensiona al ancho del papel (manteniendo la
    proporción), mejora el contraste y la convierte a blanco y negro
    con puntitos (dithering), que es lo que mejor se ve en papel térmico.
    """
    imagen = Image.open(ruta_imagen).convert("L")

    ancho_original, alto_original = imagen.size
    nuevo_alto = int(alto_original * config.ANCHO_IMPRESION / ancho_original)
    imagen = imagen.resize((config.ANCHO_IMPRESION, nuevo_alto))

    imagen = ImageOps.autocontrast(imagen)
    imagen = imagen.convert("1")
    return imagen


def abrir_impresora():
    return Usb(
        config.VENDOR_ID,
        config.PRODUCT_ID,
        out_ep=config.USB_OUT_EP,
        in_ep=config.USB_IN_EP,
    )


def imprimir_imagen(ruta_imagen):
    """
    Manda una imagen (foto o generada por IA, de cualquier tamaño)
    a la impresora térmica y corta el papel.
    """
    imagen = preparar_imagen(ruta_imagen)
    impresora = abrir_impresora()
    impresora.image(imagen)
    impresora.text("\n\n")
    impresora.cut()


def imprimir_texto(texto):
    """
    Manda texto simple a la impresora y corta el papel.
    Útil para pruebas rápidas.
    """
    impresora = abrir_impresora()
    impresora.text(texto)
    impresora.cut()
