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

# --- Botón (un solo botón arcade, pin GPIO en modo BCM) ---
# Toque corto = foto. Mantenerlo presionado = modo IA.
# Conexión: una terminal (COM) al GPIO17 (pin 11) y la otra (NO) a GND (pin 9).
PIN_BOTON = 17
# Segundos que hay que mantenerlo presionado para que cuente como "largo".
TIEMPO_PULSACION_LARGA = 1.5

# --- Cuenta regresiva antes de tomar la foto ---
SEGUNDOS_CUENTA_REGRESIVA = 5

# --- Carpeta donde se guardan las fotos e imágenes generadas ---
CARPETA_TEMP = "temp"

# --- Pantalla ---
ANCHO_PANTALLA = 800
ALTO_PANTALLA = 480
# Si existe un archivo con este nombre en la carpeta del proyecto, se usa
# como fondo. Si no existe, se genera un fondo degradado automáticamente.
RUTA_FONDO = "fondo.png"
