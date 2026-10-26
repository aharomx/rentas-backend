""" 
    Modificar cuando se defina una empresa real.
    Todos los pdf's toman los datos de este archivo
"""


# ========== DATOS DE LA EMPRESA ==========
EMPRESA_NOMBRE = "Rentas de Impresoras SA de CV"
EMPRESA_RFC = "RIP123456ABC"
EMPRESA_DIRECCION = "Av. Reforma 123, Col. Centro, CDMX, CP 06000"
EMPRESA_TELEFONO = "55 5555 5555"
EMPRESA_EMAIL = "contacto@rentas-impresoras.com"
IVA_PORCENTAJE = 0.16

# ========== LOGO ==========
# Ruta al archivo de logo (PNG o JPG). Si no existe, se deja espacio en blanco.
# Ejemplo: "/home/aharo/rentas_backend/app/static/logos/logo.png"
EMPRESA_LOGO_PATH = None  # Cambiar cuando tengas el logo

# Ancho y alto del logo en el PDF (en pulgadas)
LOGO_WIDTH = 1.5
LOGO_HEIGHT = 0.8


# ========== TEXTOS ==========
TITULO_ENTREGA = "SOLICITUD DE ENTREGA DE ALMACÉN"
TITULO_RECOLECCION = "ORDEN DE RECOLECCIÓN DE VACÍOS"

PIE_PAGINA = "Documento generado automáticamente por el sistema de control de rentas"