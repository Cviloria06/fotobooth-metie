import cv2
import pantalla
import impresora
import ia_generador


def modo_foto():
    pantalla.mostrar_mensaje("Preparate...", segundos=1)
    cuadro = pantalla.mostrar_vista_previa_con_conteo()

    if cuadro is None:
        pantalla.mostrar_mensaje("No se pudo usar la camara", segundos=2)
        return

    ruta = pantalla.guardar_captura(cuadro)
    pantalla.mostrar_imagen_resultado(ruta, "Imprimiendo...")
    impresora.imprimir_imagen(ruta)
    pantalla.mostrar_mensaje("Listo!", segundos=2)


def modo_ia():
    pantalla.mostrar_mensaje("Escuchando...", subtexto="Di que imagen quieres")
    descripcion = ia_generador.escuchar_descripcion()

    if descripcion is None:
        pantalla.mostrar_mensaje("No se entendio, intenta de nuevo", segundos=2)
        return

    pantalla.mostrar_mensaje("Generando con IA...", subtexto=descripcion)
    ruta = ia_generador.generar_imagen(descripcion)

    pantalla.mostrar_imagen_resultado(ruta, "Imprimiendo...")
    impresora.imprimir_imagen(ruta)
    pantalla.mostrar_mensaje("Listo!", segundos=2)


def main():
    pantalla.inicializar_ventana()

    while True:
        accion = pantalla.mostrar_menu_y_esperar()
        if accion == "foto":
            modo_foto()
        elif accion == "ia":
            modo_ia()
        elif accion == "salir":
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
