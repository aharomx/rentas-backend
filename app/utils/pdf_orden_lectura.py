from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from sqlalchemy.orm import Session
from datetime import datetime
import os

from app.models.orden_lectura import OrdenLectura
from app.models.contrato_equipo import ContratoEquipo
from app.models.lectura_contador import LecturaContador


# Helper para obtener el contador más reciente
def _get_contador_valor(actual, inicial):
    """Devuelve el contador actual si existe, si no el inicial, si no 'N/A'."""
    if actual is not None:
        return str(actual)
    if inicial is not None:
        return str(inicial)
    return "N/A"

def generar_cedula_lectura(db: Session, orden_id: int, output_dir: str = "pdfs") -> str:
    """Genera el PDF de la cédula de lectura ordenada por ubicación."""

    
    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Obtener datos
    orden = db.query(OrdenLectura).filter(OrdenLectura.id == orden_id).first()
    if not orden:
        raise ValueError("Orden no encontrada")
    
    contrato = orden.contrato
    cliente = contrato.cliente
    
    # Equipos activos del contrato, ordenados por ubicación
    equipos = db.query(ContratoEquipo).filter(
        ContratoEquipo.id_contrato == contrato.id,
        ContratoEquipo.activo == True
    ).order_by(ContratoEquipo.ubicacion).all()
    
    # Crear PDF
    filename = f"{output_dir}/cedula_lectura_{orden_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()


    estilo_celda=ParagraphStyle(
        'CeldaTabla',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,          # Interlineado (menos que fotSize = más compacto)
        alignment=TA_LEFT,  # Alineación izquierda
        wordwrap='CJK'      # Envuelve palabras largas in espacio
    )

    estilo_celda_izq=ParagraphStyle(
        'CeldaIzq',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        alignment=TA_LEFT,
        wordWrap='CJK'
    )


    estilo_celda_centro=ParagraphStyle(
        'CeldaTablaCentro',
        parent=estilo_celda,
        alignment=TA_CENTER
    )

    estilo_encabezado=ParagraphStyle(
        'Encabezado',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.whitesmoke,
        fontName='Helvetica-Bold'
    )

    titulo_style = ParagraphStyle(
        'Titulo', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16, spaceAfter=6
    )
    
    subtitulo_style = ParagraphStyle(
        'Subtitulo', parent=styles['Heading2'], fontSize=12, spaceAfter=4
    )
    
    elementos = []
    
    # Encabezado
    elementos.append(Paragraph("CÉDULA DE LECTURA DE CONTADORES", titulo_style))
    elementos.append(Spacer(1, 0.2*inch))
    
    # Datos del contrato
    datos_contrato = [
        ["Cliente:", cliente.razon_social or "", "Contrato #:", str(contrato.id)],
        ["Fecha de generación:", datetime.now().strftime("%d/%m/%Y"), 
         "Fecha límite:", orden.fecha_limite.strftime("%d/%m/%Y") if orden.fecha_limite else "N/A"],
    ]
    
    tabla_contrato = Table(datos_contrato, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1.5*inch])
    tabla_contrato.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_contrato)
    elementos.append(Spacer(1, 0.3*inch))
    

 
    # Tabla de equipos (ordenada por ubicación)
    encabezados = [
        Paragraph("Ubicación", estilo_encabezado),
        Paragraph("No. Serie", estilo_encabezado),
        Paragraph("Modelo", estilo_encabezado),
        Paragraph("Contador,<br/>Actual<br/>Mono", estilo_encabezado),
        Paragraph("Contador,<br/>Nuevo<br/>Mono", estilo_encabezado),
        Paragraph("Contador,<br/>Actual<br/>Color", estilo_encabezado),
        Paragraph("Contador,<br/>Nuevo<br/>Color", estilo_encabezado),
    ]

    filas = [encabezados]

    for ce in equipos:
        # Determinar si el equipo es a color
        es_color = ce.equipo.modelo.es_color if ce.equipo and ce.equipo.modelo else False
        
        # Contadores mono (siempre aplican)
        contador_actual_mono = _get_contador_valor(
            ce.contador_actual_mono, 
            ce.contador_inicial_mono
        )
        
        # Contadores color (solo si es color)
        contador_actual_color = _get_contador_valor(
            ce.contador_actual_color,
            ce.contador_inicial_color
        ) if es_color else "-"
        
        filas.append([
            Paragraph(ce.ubicacion or "Sin ubicación", estilo_celda_izq),
            Paragraph(ce.equipo.numero_serie if ce.equipo else "N/A", estilo_celda_izq),
            Paragraph(
                ce.equipo.modelo.nombre_modelo if ce.equipo and ce.equipo.modelo else "N/A",
                estilo_celda_izq
            ),
            Paragraph(contador_actual_mono, estilo_celda_centro),
            Paragraph("", estilo_celda_centro),
            Paragraph(contador_actual_color, estilo_celda_centro),
            Paragraph("", estilo_celda_centro),
        ])

    # Agregamos un total de equipos
    total_equipos=len(equipos)
    filas.append(["","", f"Total: {total_equipos} equipos", "","","",""])

    tabla_equipos = Table(filas, colWidths=[
        1.5*inch, 
        0.9*inch, 
        1.9*inch, 
        0.7*inch, 
        0.7*inch, 
        0.7*inch, 
        0.7*inch
    ], repeatRows=1)

    tabla_equipos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))

    elementos.append(tabla_equipos)
    elementos.append(Spacer(1, 0.3*inch))


    
    # Firmas
    firma_data = [
        ["_________________________", "", "_________________________"],
        ["Firma del Técnico", "", "Firma del Cliente"],
        ["Nombre:", "", "Nombre:"],
        ["Fecha:", "", "Fecha:"],
    ]
    
    tabla_firmas = Table(firma_data, colWidths=[2.5*inch, 1*inch, 2.5*inch])
    tabla_firmas.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_firmas)
    
    # Generar PDF
    doc.build(elementos)
    return filename