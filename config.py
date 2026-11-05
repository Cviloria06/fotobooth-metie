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

# --- Calidad de la foto impresa ---
# La impresora solo imprime puntos negros: cada foto se convierte a puntitos.
# Estos ajustes preparan la foto antes de convertirla para que se vea mejor.
MEJORAR_FOTO = True        # False = sin ninguna mejora (como antes)
GAMMA_IMPRESION = 0.75     # menor que 1 aclara los tonos medios (el papel térmico oscurece). 1.0 = sin cambio
CONTRASTE_LOCAL = 2.0      # rescata caras oscuras a contraluz. 0 = apagado; más alto = más fuerte (y más textura en la piel)

# --- Marco que se imprime alrededor de cada foto o imagen de IA ---
USAR_MARCO = True              # False = imprimir la foto sola, sin marco
TEXTO_SUPERIOR = "Metie 2026"  # título de arriba (letra cursiva)
TEXTO_INFERIOR = "FOTOBOOTH"   # texto de abajo
MOSTRAR_FECHA = True           # False = sin fecha
FECHA_TEXTO = "12 NOV 2026"    # fecha que se imprime. Déjalo vacío ("") para usar la fecha del día
# Tipografías (archivos .ttf dentro de la carpeta "fuentes"). Para cambiarlas,
# copia otra letra .ttf a esa carpeta y pon aquí su nombre.
FUENTE_TITULO = "fuentes/Lora-BoldItalic.ttf"
FUENTE_TEXTO = "fuentes/Poppins-Medium.ttf"

# --- Cámara ---
CAMARA_INDICE = 0  # 0 es normalmente la primera cámara conectada
# Resolución con la que se toma la foto. Más grande = más detalle (si la cámara lo permite).
CAMARA_ANCHO = 1280
CAMARA_ALTO = 720
# Se promedian los últimos cuadros antes de tomar la foto: así se reduce el "ruido" de la cámara.
CUADROS_A_PROMEDIAR = 4

# --- Botón (un solo botón arcade, pin GPIO en modo BCM) ---
# Toque corto = foto. Mantenerlo presionado = modo IA.
# Conexión: una terminal (COM) al GPIO17 (pin 11) y la otra (NO) a GND (pin 9).
PIN_BOTON = 17
# Segundos que hay que mantenerlo presionado para que cuente como "largo".
TIEMPO_PULSACION_LARGA = 1.5

# --- Cuenta regresiva antes de tomar la foto ---
# Primero se ve la cámara y se espera otro toque del botón; entonces empieza esta cuenta.
SEGUNDOS_CUENTA_REGRESIVA = 5
# Si nadie presiona el botón en la vista de la cámara durante este tiempo, vuelve al menú.
TIEMPO_MAX_VISTA_PREVIA = 90

# --- Carpeta donde se guardan las fotos e imágenes generadas ---
CARPETA_TEMP = "temp"

# --- Pantalla ---
# "spi"     = la pantalla TFT de 2.8" conectada a los pines (ILI9341, 320x240).
# "ventana" = una ventana en el escritorio de la Raspberry (sirve para probar sin la pantalla).
TIPO_PANTALLA = "spi"
if TIPO_PANTALLA == "spi":
    ANCHO_PANTALLA = 320
    ALTO_PANTALLA = 240
else:
    ANCHO_PANTALLA = 800
    ALTO_PANTALLA = 480

# Tus propios diseños (opcionales). Se buscan en la carpeta del proyecto:
#   fondo.png = fondo de todas las pantallas (debajo de los textos)
#   menu.png  = pantalla de menú completa; si existe, reemplaza al menú que se dibuja solo
# Tamaño recomendado: 640x480 (proporción 4:3). Si el tamaño es otro, se recorta al centro.
RUTA_FONDO = "fondo.png"
RUTA_MENU = "menu.png"

# Conexión de la pantalla SPI (números BCM; ver el esquema de pines del informe)
PANTALLA_PIN_DC = 24       # pin físico 18
PANTALLA_PIN_RESET = 25    # pin físico 22
# (CS va al pin físico 24 = CE0, MOSI al 19, SCK al 23: los maneja el SPI de la Raspberry)
PANTALLA_SPI_VELOCIDAD = 24000000   # si se ve ruido o puntitos raros, baja a 16000000 o 8000000

# Ajustes si la pantalla se ve distinta a lo esperado (ver prueba_pantalla.py):
PANTALLA_ROTACION = 1              # 0 y 2 = vertical, 1 y 3 = horizontal. Prueba 3 si se ve de cabeza
PANTALLA_ESPEJO = True             # la vista de la cámara se ve como un espejo (la foto impresa NO se voltea)
PANTALLA_CAMBIAR_ROJO_AZUL = False # True si el rojo sale azul y el azul sale rojo
PANTALLA_INVERTIR_COLORES = False  # True si los colores se ven como en un negativo

# ===== Modo IA =====
# --- Micrófono ---
# "auto" = usa la primera tarjeta de captura que muestre "arecord -l" (el micrófono de la webcam
# o uno USB). Si hay varios, pon aquí el dispositivo exacto, por ejemplo "plughw:2,0".
MICROFONO_DISPOSITIVO = "auto"
MICROFONO_SEGUNDOS = 6            # cuánto tiempo graba cuando dices qué imagen quieres
MICROFONO_UMBRAL_SILENCIO = 400   # si el pico de volumen es menor que esto, se considera silencio
IDIOMA_VOZ = "es-CO"

# --- ¿Qué IA crea las imágenes? ---
# "pollinations" = gratis, sin clave (lo normal). "gemini" = de pago, necesita clave y facturación.
PROVEEDOR_IA = "pollinations"
# Se añade al final de lo que dices, para que el dibujo salga bien en papel térmico (solo blanco y negro).
# Va en inglés porque la descripción se traduce al inglés antes de pedir la imagen.
ESTILO_IA = ("Clear high-contrast illustration with bold outlines and a simple background, "
             "no text or letters.")
# True = lo que dices se traduce al inglés antes de pedir la imagen (suele seguir mejor la descripción).
# Si el traductor no responde, se usa el texto original.
TRADUCIR_A_INGLES = True
TRADUCCION_TIMEOUT = 8            # segundos máximos de espera del traductor

# --- Pollinations ---
POLLINATIONS_ANCHO = 768
POLLINATIONS_ALTO = 1024          # vertical, como el papel de la impresora
POLLINATIONS_MODELO = ""          # vacío = el modelo por defecto del servicio (por ejemplo "flux")
POLLINATIONS_TIMEOUT = 90         # segundos máximos de espera por intento
POLLINATIONS_INTENTOS = 3         # si dice "espera" o falla, se reintenta solo

# --- Gemini (solo si PROVEEDOR_IA = "gemini") ---
# La clave NO va aquí: se guarda en el archivo clave_gemini.txt dentro de la carpeta del proyecto
# (créalo solo en la Raspberry; no lo subas a GitHub).
ARCHIVO_CLAVE_GEMINI = "clave_gemini.txt"
# Se prueba el primer modelo; si no existe, el siguiente. Verifica los nombres vigentes en Google AI Studio.
GEMINI_MODELOS_IMAGEN = ["gemini-nano-banana-2.1", "gemini-3.1-flash-image"]
GEMINI_PROPORCION = "3:4"         # vertical, como el papel de la impresora
GEMINI_TIMEOUT = 90               # segundos máximos de espera
