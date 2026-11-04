# Un solo botón con dos acciones:
#   toque corto            -> "foto"
#   mantenerlo presionado  -> "ia"
#
# Conexión (botón arcade con microswitch): una terminal (COM) al GPIO17
# (pin 11) y la otra (NO) a GND (pin 9). Al presionar, el pin se une a GND
# y se lee "presionado"; la resistencia pull-up interna lo mantiene en alto
# cuando no se presiona.
#
# Se usa gpiozero porque funciona en la Raspberry Pi 5. En un computador sin
# GPIO no hay botón físico: HAY_BOTON queda en False y el teclado se revisa
# aparte (en pantalla.py).

import time
import config

try:
    from gpiozero import Button
except ImportError:
    Button = None

HAY_BOTON = False
_boton = None
_accion_pendiente = None
_mantenido = False


def _al_mantener():
    # Se llama una vez, cuando el botón lleva presionado TIEMPO_PULSACION_LARGA.
    global _accion_pendiente, _mantenido
    _mantenido = True
    _accion_pendiente = "ia"


def _al_soltar():
    # Si no fue una pulsación larga, fue un toque corto.
    global _accion_pendiente, _mantenido
    if not _mantenido:
        _accion_pendiente = "foto"
    _mantenido = False


def iniciar():
    """Crea el botón. Devuelve True si hay un botón físico utilizable."""
    global _boton, HAY_BOTON
    if _boton is not None:
        return True
    if Button is None:
        return False

    try:
        _boton = Button(
            config.PIN_BOTON,
            pull_up=True,
            bounce_time=0.05,
            hold_time=config.TIEMPO_PULSACION_LARGA,
        )
    except Exception as error:
        print("Aviso: no se pudo iniciar el botón por GPIO:", error)
        return False

    _boton.when_held = _al_mantener
    _boton.when_released = _al_soltar
    HAY_BOTON = True
    return True


def revisar_accion():
    """
    Revisa SIN esperar si hubo una pulsación. Devuelve "foto", "ia" o None.
    Cada pulsación se entrega una sola vez. Sirve para llamarla muchas veces
    por segundo dentro del bucle de la pantalla.
    """
    global _accion_pendiente
    accion = _accion_pendiente
    _accion_pendiente = None
    return accion


def esperar_accion():
    """Espera hasta que haya una pulsación y devuelve "foto" o "ia"."""
    while True:
        accion = revisar_accion()
        if accion is not None:
            return accion
        time.sleep(0.02)


def estado_actual():
    """True si el botón está presionado en este momento (para diagnóstico)."""
    return bool(_boton is not None and _boton.is_pressed)


iniciar()
