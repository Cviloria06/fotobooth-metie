# Este módulo detecta si estamos en una Raspberry Pi (con GPIO disponible)
# o en un computador normal (sin GPIO).
#
# revisar_accion() se usa DENTRO del bucle de la pantalla de menú: se
# llama una y otra vez, muchas veces por segundo, y responde de inmediato
# (nunca espera). Así la pantalla puede seguir dibujándose sin trabarse
# mientras se revisa si alguien presionó un botón físico.
#
# En el computador (sin GPIO), el teclado se revisa directamente en
# pantalla.py con cv2.waitKey, así que aquí simplemente no hay botones
# que revisar y siempre se devuelve None.

import config

try:
    import RPi.GPIO as GPIO
    HAY_GPIO = True
except ImportError:
    HAY_GPIO = False

if HAY_GPIO:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(config.PIN_BOTON_FOTO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(config.PIN_BOTON_IA, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def revisar_accion():
    """
    Revisa UNA sola vez si algún botón físico está presionado ahora
    mismo (no espera a que se presione). Devuelve "foto", "ia" o None.
    """
    if not HAY_GPIO:
        return None

    if GPIO.input(config.PIN_BOTON_FOTO) == GPIO.HIGH:
        return "foto"
    if GPIO.input(config.PIN_BOTON_IA) == GPIO.HIGH:
        return "ia"
    return None
