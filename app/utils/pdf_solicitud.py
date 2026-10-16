from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.config import empresa
from app.models.solicitud_almacen import SolicitudAlmacen
from app.models.solicitud_almacen_detalle import SolicitudAlmacenDetalle


def _get_contador_valor(actual, inicial):
    """ Helper para obtener el valor del contador """
    if actual is not None:
        return str(actual)
    if inicial is not None:
        return str(inicial)

    return "N/A"

def _formatear_fecha(fecha)->str:
    """ Fromatea fecha para mostrar en PDF """
    if not fecha:
        return "-"
    return fecha.strftime("%d/%m/%Y %H:%M")

def generar_pdf_solicitud(
        db:Session,
        solicitud_id:int,
        output_dir:str="pdfs"
) -> str:
    """ Genera el PDF de una solicitud de almacén """

    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)

    # Obtener solicitud
    solicitud=db.query(SolicitudAlmacen).filter(
        SolicitudAlmacen.id==solicitud_id
    ).first()

    if not solicitud:
        raise ValueError("Solicitud no encontrada")

    # Nombre del archivo
    filename= f"{output_dir}/{solicitud.folio}_{datetime.now().strftime("%d-%m.%Y %H:%M")}.pdf"



    doc=SimpleDocTemplate(
        filename,
        pagesize=letter,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch,
    )

    # Estilos
    styles=getSampleStyleSheet()

    estilo_titulo=ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=6,
        textColor=colors.HexColor("#1a5490"),
    )

    estilo_subtitulo=ParagraphStyle(
        "Subtitulo",
        parent=styles['Heading2'],
        fontSize=11,
        spaceAfter=4
    )

    estilo_empresa=ParagraphStyle(
        'Empresa',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_LEFT,
        leading=11,
    )

    estilo_celda=ParagraphStyle(
        'Celda',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        alignment=TA_LEFT
    )

    estilo_celda_centro=ParagraphStyle(
        'CeldaCentr',
        parent=estilo_celda,
        alignment=TA_CENTER,
    )

    estilo_encabezado=ParagraphStyle(
        'Encabezado',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold',
    )

    estilo_label=ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=9,
        fontName='Helvetica-Bold'
    )

    # Contenido del PDF

    elementos=[]

    # =========== ENCABEZADO ======================
    
    # Crear una tabla con logo a la izquierda y datos de la empresa a la derecha

    if empresa.EMPRESA_LOGO_PATH and os.path.exists(empresa.EMPRESA_LOGO_PATH):

        logo=Image(
            empresa.EMPRESA_LOGO_PATH,
            width=empresa.LOGO_WIDTH*inch,
            height=empresa.LOGO_HEIGHT*inch,
        )
    else:
        # Espacio reservado para el logo
        logo=Table(
            [[""]],
            colWidths=[empresa.LOGO_WIDTH*inch],
            rowHeights=[empresa.LOGO_HEIGHT*inch],
        )
        logo.setStyle(TableStyle([
            ('BOX',(0,0),(-1,-1),0.5, colors.lightgrey),
            ('BACKGROUND',(0,0),(-1,-1), colors.whitesmoke),
        ]))

    # Columna derecha: datos de la empresa
    datos_empresa= f"""
    <b>{empresa.EMPRESA_NOMBRE}</b><br/>
    RFC: {empresa.EMPRESA_RFC}<br/>
    {empresa.EMPRESA_DIRECCION}<br/>
    Tel: {empresa.EMPRESA_TELEFONO}<br/>
    Email: {empresa.EMPRESA_EMAIL}
    """

    tabla_encabezado=Table(
        [(logo, Paragraph(datos_empresa, estilo_empresa))],
        colWidths=[2*inch, 5.5*inch],
    )
    tabla_encabezado.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('ALIGN',(1,0),(1,0),'RIGHT'),
    ]))

    elementos.append(tabla_encabezado)
    elementos.append(Spacer(1,0.2*inch))


    # ============ TITULO ================
    if solicitud.tipo == "entrega":
        titulo = empresa.TITULO_ENTREGA
    else:
        titulo = empresa.TITULO_RECOLECCION

    elementos.append(Paragraph(titulo,estilo_titulo))
    elementos.append(Spacer(1,0.15*inch))


    # ======== DATOS DE LA SOLICITUD ==============
    # Tabla de 2 columnas con la información clave

    datos_solicitud=[
        [
            Paragraph("<b>Folio:</b>",estilo_celda),
            Paragraph(solicitud.cliente_nombre or "-",estilo_celda),
            Paragraph("<b>Contrato:</b>",estilo_celda),
            Paragraph(
                str(solicitud.contrato_numero) if solicitud.contrato_numero else "-",estilo_celda
            ),
        ],
        [
            Paragraph("<b>Cliente:</b>",estilo_celda),
            Paragraph(solicitud.cliente_nombre or "-",estilo_celda),
            Paragraph("<b>Contrato:</b>",estilo_celda),
            Paragraph(
                str(solicitud.contrato_numero) if solicitud.contrato_numero else "-",
                estilo_celda
            ),
        ],
        [
            Paragraph("<b>Chofer:</b>",estilo_celda),
            Paragraph(solicitud.chofer or "-",estilo_celda),
            Paragraph("<b>Estado:</b>",estilo_celda),
        ],
    ]

    tabla_datos=Table(
        datos_solicitud,
        colWidths=[1*inch, 2.75*inch, 1*inch, 2.75*inch],
    )
    tabla_datos.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor("#e8f0f8")),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor("#e8f0f8")),
    ]))

    elementos.append(tabla_datos)
    elementos.append(Spacer(1,0.2*inch))

    # ============== OBSERVACIONES =======================
    if solicitud.observaciones:
        elementos.append(Paragraph("<b>Observaciones:</b>",estilo_label))
        elementos.append(Spacer(1,0.5*inch))
        elementos.append(Paragraph(solicitud.observaciones,estilo_celda))
        elementos.append(Spacer(1,0.5*inch))

    # ============== TABLA DE ARTICULOS =====================
    if solicitud.tipo=="entrega":
        encabezados=[
            "#",
            "Código",
            "Artículo",
            "Cantidad",
            "No. Serie",
            "Estado",
        ]
    else: # recolección
        encabezados=[
            "#",
            "Código",
            "Artículo",
            "Cantidad",
            "No. Serie",
            "Recibido",
        ]

    filas=[[Paragraph(h,estilo_encabezado) for h in encabezados]]

    for idx, det in enumerate(solicitud.detalle,start=1):
        # Columna "Recibido" solo para recolecciones (espacio para escribir)
        ultima_columna="" if solicitud.tipo=="recoleccion" else det.estado

        filas.append([
            Paragraph(str(idx),estilo_celda_centro),
            Paragraph(det.articulo_codigo or "-",estilo_celda),
            Paragraph(det.articulo_nombre or "-",estilo_celda),
            Paragraph(str(det.cantidad),estilo_celda_centro),
            Paragraph(det.numero_serie_toner or "-",estilo_celda),
            Paragraph(ultima_columna,estilo_celda_centro),
        ])

    tabla_articulos = Table(
        filas,
        colWidths=[
            0.3*inch,   # #
            1.0*inch,   # Código
            2.7*inch,   # Artículo
            0.7*inch,   # Cantidad
            1.7*inch,   # No. Serie
            1.1*inch,   # Estado/Recibico
        ],
        repeatRows=1,
    )

    tabla_articulos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a5490")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))

    elementos.append(tabla_articulos)
    elementos.append(Spacer(1,0.3*inch))

    # ============== NOTA INFORMATIVA ================
    if solicitud.tipo=="recoleccion":
        nota=(
            "<i>Nota: Capturar en la columna 'Recibido' el número de serie de cada"
            "tóner vacío que se recoja, Los tóners que no se reciban se dejarán en blanco.</i>"
        )
        elementos.append(Paragraph(nota,estilo_celda))
        elementos.append(Spacer(1,0.2*inch))

    # ============== FIRMAS =================
    firma_data = [
        [
            Paragraph("<b>Firma del Chofer</b>", estilo_celda_centro),
            "",
            Paragraph("<b>Firma del Cliente</b>", estilo_celda_centro),
        ],
        [
            "",
            "",
            "",
        ],
        [
            Paragraph("Nombre: _______________________", estilo_celda_centro),
            "",
            Paragraph("Nombre: _______________________", estilo_celda_centro),
        ],
        [
            Paragraph("Fecha: ________________________", estilo_celda_centro),
            "",
            Paragraph("Fecha: ________________________", estilo_celda_centro),
        ],
    ]
    
    tabla_firmas = Table(
        firma_data,
        colWidths=[3 * inch, 1.5 * inch, 3 * inch],
        rowHeights=[0.25 * inch, 0.7 * inch, 0.3 * inch, 0.3 * inch],
    )
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('LINEABOVE', (0, 1), (0, 1), 0.5, colors.black),
        ('LINEABOVE', (2, 1), (2, 1), 0.5, colors.black),
    ]))

    elementos.append(tabla_firmas)
    elementos.append(Spacer(1,0.3*inch))

    # ============= PIE DE PAGINA ========================
    pie_style=ParagraphStyle(
        'Pie',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER,
        textColor=colors.grey,
    )

    elementos.append(Paragraph(empresa.PIE_PAGINA,pie_style))
    elementos.append(Paragraph(
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} por el sistema",
        pie_style
    ))

    # Generar PDF
    doc.build(elementos)
    return filename


