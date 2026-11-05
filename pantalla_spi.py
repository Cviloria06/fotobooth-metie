# Controlador de la pantalla TFT de 2.8" (chip ILI9341, 240x320) conectada por SPI.
#
# Habla directo con la pantalla, sin instalar controladores del sistema:
#   - spidev   : manda los datos por el SPI (pines MOSI, SCK y CS)
#   - gpiozero : maneja los pines DC y RESET (funciona en la Raspberry Pi 5)
#
# Conexión (pin de la pantalla -> pin físico de la Raspberry):
#   VCC -> 2 (5V)     GND -> 6        LED -> 17 (3.3V)
#   CS  -> 24         RESET -> 22     DC  -> 18
#   SDI (MOSI) -> 19  SCK -> 23

import time
import numpy as np
import config

try:
    import spidev
except ImportError:
    spidev = None

try:
    from gpiozero import DigitalOutputDevice
except ImportError:
    DigitalOutputDevice = None

# comandos del ILI9341
_SWRESET = 0x01
_SLPOUT = 0x11
_INVOFF = 0x20
_INVON = 0x21
_DISPOFF = 0x28
_DISPON = 0x29
_CASET = 0x2A    # columnas
_PASET = 0x2B    # filas
_RAMWR = 0x2C    # empezar a escribir píxeles
_MADCTL = 0x36   # orientación

# valor de MADCTL según la rotación (igual que la librería de Adafruit)
_ROTACIONES = {0: 0x48, 1: 0x28, 2: 0x88, 3: 0xE8}

# secuencia de arranque estándar del ILI9341 (la misma de Adafruit y TFT_eSPI)
_INICIO = [
    (0xEF, (0x03, 0x80, 0x02)),
    (0xCF, (0x00, 0xC1, 0x30)),
    (0xED, (0x64, 0x03, 0x12, 0x81)),
    (0xE8, (0x85, 0x00, 0x78)),
    (0xCB, (0x39, 0x2C, 0x00, 0x34, 0x02)),
    (0xF7, (0x20,)),
    (0xEA, (0x00, 0x00)),
    (0xC0, (0x23,)),
    (0xC1, (0x10,)),
    (0xC5, (0x3E, 0x28)),
    (0xC7, (0x86,)),
    (0x37, (0x00,)),
    (0x3A, (0x55,)),          # 16 bits por píxel (RGB565)
    (0xB1, (0x00, 0x18)),
    (0xB6, (0x08, 0x82, 0x27)),
    (0xF2, (0x00,)),
    (0x26, (0x01,)),
    (0xE0, (0x0F, 0x31, 0x2B, 0x0C, 0x0E, 0x08, 0x4E, 0xF1,
            0x37, 0x07, 0x10, 0x03, 0x0E, 0x09, 0x00)),
    (0xE1, (0x00, 0x0E, 0x14, 0x03, 0x11, 0x07, 0x31, 0xC1,
            0x48, 0x08, 0x0F, 0x0C, 0x31, 0x36, 0x0F)),
]


def a_rgb565(rgb, cambiar_rojo_azul=False):
    """
    Convierte una imagen (alto, ancho, 3) en orden R,G,B, de 0 a 255, al formato
    de la pantalla: 2 bytes por píxel (5 bits de rojo, 6 de verde, 5 de azul),
    con el byte más importante primero.
    """
    if cambiar_rojo_azul:
        rgb = rgb[:, :, ::-1]
    r = rgb[:, :, 0].astype(np.uint16)
    g = rgb[:, :, 1].astype(np.uint16)
    b = rgb[:, :, 2].astype(np.uint16)
    valor = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return valor.astype(">u2").tobytes()


class PantallaSPI:
    def __init__(self):
        self.rotacion = int(getattr(config, "PANTALLA_ROTACION", 1))
        if self.rotacion in (0, 2):
            self.ancho, self.alto = 240, 320
        else:
            self.ancho, self.alto = 320, 240
        self._spi = None
        self._dc = None
        self._reset = None

    # ---------- arranque y cierre ----------

    def iniciar(self):
        """Abre el SPI y los pines y enciende la pantalla. Si algo falla, explica qué."""
        if spidev is None or DigitalOutputDevice is None:
            raise RuntimeError(
                "Faltan librerías. Instálalas con: sudo apt install python3-spidev python3-gpiozero")

        try:
            self._spi = spidev.SpiDev()
            self._spi.open(0, 0)
        except FileNotFoundError:
            self._spi = None
            raise RuntimeError(
                "El SPI está apagado (no existe /dev/spidev0.0). Actívalo con: "
                "sudo raspi-config nonint do_spi 0   y reinicia la Raspberry.")
        except PermissionError:
            self._spi = None
            raise RuntimeError("Sin permiso para el SPI. Corre el programa con sudo.")

        self._spi.max_speed_hz = int(getattr(config, "PANTALLA_SPI_VELOCIDAD", 24000000))
        self._spi.mode = 0
        self._dc = DigitalOutputDevice(config.PANTALLA_PIN_DC)
        self._reset = DigitalOutputDevice(config.PANTALLA_PIN_RESET, initial_value=True)
        self._secuencia_de_arranque()

    def apagar(self):
        """Apaga la imagen y libera los pines."""
        try:
            if self._spi is not None and self._dc is not None:
                self._comando(_DISPOFF)
        except Exception:
            pass
        self.cerrar()

    def cerrar(self):
        for objeto in (self._spi, self._dc, self._reset):
            try:
                if objeto is not None:
                    objeto.close()
            except Exception:
                pass
        self._spi = self._dc = self._reset = None

    # ---------- comunicación con el chip ----------

    def _comando(self, comando, datos=()):
        self._dc.off()                       # DC bajo = lo que sigue es un comando
        self._spi.writebytes([comando])
        if len(datos):
            self._dc.on()                    # DC alto = lo que sigue son datos
            self._spi.writebytes(list(datos))

    def _secuencia_de_arranque(self):
        # reinicio por el pin RESET
        self._reset.on()
        time.sleep(0.01)
        self._reset.off()
        time.sleep(0.05)
        self._reset.on()
        time.sleep(0.15)

        self._comando(_SWRESET)
        time.sleep(0.15)
        for comando, datos in _INICIO:
            self._comando(comando, datos)
        self._comando(_MADCTL, (_ROTACIONES[self.rotacion],))
        self._comando(_INVON if getattr(config, "PANTALLA_INVERTIR_COLORES", False) else _INVOFF)
        self._comando(_SLPOUT)
        time.sleep(0.12)
        self._comando(_DISPON)
        time.sleep(0.02)

    def _enviar_datos(self, datos):
        try:
            self._spi.writebytes2(datos)     # rápido: lo parte en pedazos por sí solo
        except AttributeError:               # versión vieja de spidev
            for i in range(0, len(datos), 4096):
                self._spi.writebytes(list(datos[i:i + 4096]))

    # ---------- dibujar ----------

    def mostrar(self, rgb):
        """
        Muestra una imagen en toda la pantalla. "rgb" es una matriz numpy
        (alto, ancho, 3) en orden R,G,B, del tamaño de la pantalla (self.alto x self.ancho).
        """
        if rgb.shape[0] != self.alto or rgb.shape[1] != self.ancho:
            raise ValueError("La imagen debe medir %dx%d y mide %dx%d"
                             % (self.ancho, self.alto, rgb.shape[1], rgb.shape[0]))
        datos = a_rgb565(rgb, getattr(config, "PANTALLA_CAMBIAR_ROJO_AZUL", False))
        x1 = self.ancho - 1
        y1 = self.alto - 1
        self._comando(_CASET, (0, 0, x1 >> 8, x1 & 0xFF))
        self._comando(_PASET, (0, 0, y1 >> 8, y1 & 0xFF))
        self._comando(_RAMWR)
        self._dc.on()
        self._enviar_datos(datos)

    def llenar(self, color):
        """Pinta toda la pantalla de un color (R, G, B)."""
        imagen = np.zeros((self.alto, self.ancho, 3), dtype=np.uint8)
        imagen[:, :] = color
        self.mostrar(imagen)
