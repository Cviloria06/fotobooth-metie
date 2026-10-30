# ===== Configuración general del Fotobooth =====

# --- Impresora térmica (ESC/POS) ---
# Confirmados con "lsusb" en la Raspberry Pi 5 (funcionando).
VENDOR_ID = 0x0471
PRODUCT_ID = 0x0055
USB_OUT_EP = 0x02
USB_IN_EP = 0x81

# Ancho máximo de imagen en puntos (pixeles) para el papel de 80mm.
# Lo normal es 576. Si al imprimir la foto se corta el borde derecho,
# bájalo (por ejemplo a 512 o 384) hasta que salga completa.
ANCHO_IMPRESION = 576

# --- Cámara ---
CAMARA_INDICE = 0  # 0 es normalmente la primera cámara conectada

# --- Botones (pines GPIO en la Raspberry, modo BCM) ---
PIN_BOTON_FOTO = 17
PIN_BOTON_IA = 27

# --- Carpeta donde se guardan las fotos e imágenes generadas ---
CARPETA_TEMP = "temp"

# --- Pantalla ---
ANCHO_PANTALLA = 800
ALTO_PANTALLA = 480
# Si existe un archivo con este nombre en la carpeta del proyecto, se usa
# como fondo. Si no existe, se genera un fondo degradado automáticamente.
RUTA_FONDO = "fondo.png"
