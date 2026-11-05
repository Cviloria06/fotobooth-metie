import pantalla
import impresora
import ia_generador


def imprimir_con_aviso(ruta):
    """
    Imprime la imagen y muestra "¡Listo!". Si la impresora falla,
    muestra un aviso en pantalla en vez de cerrar todo el programa.
    """
    try:
        impresora.imprimir_imagen(ruta)
        pantalla.mostrar_mensaje("¡Listo!", subtexto="Recoge tu foto", segundos=2)
    except Exception as error:
        print("Error al imprimir:", error)
        pantalla.mostrar_mensaje("No se pudo imprimir", subtexto="Revisa la impresora", segundos=3)


def modo_foto():
    pantalla.mostrar_mensaje("Prepárate...", segundos=1)
    cuadro = pantalla.mostrar_vista_previa_con_conteo()

    if cuadro is None:
        pantalla.mostrar_mensaje("No se pudo usar la cámara", segundos=2)
        return

    ruta = pantalla.guardar_captura(cuadro)
    pantalla.mostrar_imagen_resultado(ruta, "Imprimiendo...")
    imprimir_con_aviso(ruta)


def modo_ia():
    pantalla.mostrar_mensaje("Escuchando...", subtexto="Di qué imagen quieres")
    try:
        descripcion = ia_generador.escuchar_descripcion()
    except Exception as error:
        print("Error con el micrófono:", error)
        pantalla.mostrar_mensaje("Micrófono no disponible", subtexto="Todavía no está listo", segundos=3)
        return

    if descripcion is None:
        pantalla.mostrar_mensaje("No se entendió, intenta de nuevo", segundos=2)
        return

    pantalla.mostrar_mensaje("Generando con IA...", subtexto=descripcion)
    try:
        ruta = ia_generador.generar_imagen(descripcion)
    except Exception as error:
        print("Error generando la imagen:", error)
        pantalla.mostrar_mensaje("La IA no respondió", subtexto="Intenta de nuevo", segundos=3)
        return

    pantalla.mostrar_imagen_resultado(ruta, "Imprimiendo...")
    imprimir_con_aviso(ruta)


def main():
    try:
        pantalla.inicializar()
    except Exception as error:
        print("No se pudo abrir ninguna pantalla:", error)
        print("Si estás en la terminal remota, revisa la conexión de la pantalla SPI.")
        return

    try:
        while True:
            accion = pantalla.mostrar_menu_y_esperar()
            if accion == "foto":
                modo_foto()
            elif accion == "ia":
                modo_ia()
            elif accion == "salir":
                break
    except KeyboardInterrupt:
        print("\nCerrando...")
    finally:
        pantalla.cerrar()


if __name__ == "__main__":
    main()
