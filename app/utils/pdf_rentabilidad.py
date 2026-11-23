from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional
import os

from app.config import empresa


def genera_pdf_rentabilidad(
        db:Session,
        id_contrato:int,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
        output_dir:str="reportes",
) -> str:
    """ Genera PDF de rentabilidad por contrato """
    from app.crud import reportes_facturacion as crud_fact

    os.makedirs(output_dir, exist_ok=True)

    # Obtener datos
    data=crud_fact.get_rentabilidad_contrato(
        db, id_contrato,fecha_inicio=fecha_inicio,fecha_fin=fecha_fin
    )

    filename=f"{output_dir}/rentabilidad_contrato_{id_contrato}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
    )

    styles=getSampleStyleSheet()

    titulo_style=ParagraphStyle(
        'Titulo',parent=styles["Heading1"],fontSize=16,
        alignment=TA_CENTER,spaceAfter=10,textColor=colors.HexColor("1a5490")
    )

    subtitulo_style=ParagraphStyle(
        'Subtitulo',parent=styles['Heading2'],fontSize=12,
        spaceAfter=6, textColor=colors.HexColor("#1a5490")
    )

    empresa_style=ParagraphStyle(
        'Empresa',parent=styles['Normal'],fontSize=9,alignment=TA_LEFT,leading=11
    )

    celda_style=ParagraphStyle(
        'Celda',parent=styles['Normal'],fontSize=10,alignment=TA_LEFT
    )

    celda_der=ParagraphStyle(
        'CeldaDer',parent=styles['Normal'],fontSize=10,alignment=TA_RIGHT
    )

    elementos=[]

    # Encabezado con datos de la empresa
    datos_empresa=f"""
    <b>{empresa.EMPRESA_NOMBRE}</b><br/>
    RFC: {empresa.EMPRESA_RFC}<br/>
    {empresa.EMPRESA_DIRECCION}<br/>
    tel: {empresa.EMPRESA_TELEFONO}
    """

    elementos.append(Paragraph(datos_empresa, empresa_style))
    elementos.append(Spacer(1,0.2*inch))

    # Título
    elementos.append(Paragraph("REPORTE DE RENTABILIDAD POR CONTRATO", subtitulo_style))
    elementos.append(Spacer(1,0.15*inch))

    # Datos del contrato
    periodo="Todo el histórico"
    if fecha_inicio or fecha_fin:
        inicio_str=fecha_inicio.strftime("%d/%m/%Y") if fecha_inicio else "-"
        fin_str=fecha_fin.strftime("%d/%m/%Y") if fecha_fin else "-"
        periodo=f"{inicio_str} al {fin_str}"

    datos_contrato=[
        ["Contrato #:", str(data["id_contrato"]), "Cliente", data["cliente_nombre"] or "-"],
        ["Periodo:", periodo, "Generado",datetime.now().strftime("%d/%m/%Y %H%M")],
    ]

    tabla_contrato=Table(datos_contrato, colWidths=[1.2*inch, 2.3*inch,1.2*inch,2.3*inch])

    tabla_contrato.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_contrato)
    elementos.append(Spacer(1,0.3*inch))


    # ====================== SECCIÓN: INGRESOS ======================
    elementos.append(Paragraph("INGRESOS", subtitulo_style))

    ingresos=data["ingresos"]
    datos_ingresos=[
        ["Concepto","Monto"],
        ["Remisiones emitidas", f"${ingresos['remisiones']:,.2f}"],
        ["Notas de cargo", f"${ingresos['notas_cargo']:,.2f}"],
        ["Notas de crédito", f"-${ingresos['notas_credito']:,.2f}"],
        ["Ingresos netos", f"${ingresos['ingresos_netos']:,.2f}"],
    ]

    tabla_ingresos=Table(datos_ingresos,colWidths=[4*inch,2*inch])
    tabla_ingresos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a5490")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#e8f0f8")),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_ingresos)
    elementos.append(Spacer(1,0.2*inch))

    # ======================= SECCION: COSTOS ====================== 
    elementos.append(Paragraph("COSTOS", subtitulo_style))

    costos=data["costos"]
    datos_costos=[
        ["Concepto","Monto"],
        ["Refacciones en mantenimientos", f"${costos['refacciones_mantenimientos']:,.2f}"],
    ]

    tabla_costos=Table(datos_costos,colWidths=[4*inch,2*inch])
    tabla_costos.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#8B0000")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabla_costos)
    elementos.append(Spacer(1,0.3*inch))

# ================== SECCIÓN: RESULTADO ================
# 
    resultado=data["resultado"]  
    utilidad=resultado["utilidad"]
    margen=resultado["margen_porcentaje"]

    datos_resultado=[
        ["RESULTADO", ""],
        ["Utilidad Neta", f"${utilidad:.2f}"],
        ["Margen de Rentabilidad", f"{margen:.2f}%"],
    ]


    tabla_resultado=Table(datos_resultado,colWidths=[4*inch, 2*inch])

    tabla_resultado.setStyle(TableStyle([
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), color_resultado),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ('GRID', (0, 1), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabla_resultado)
    elementos.append(Spacer(1,0.5*inch))

    # Pie de página
    pie_style=ParagraphStyle(
        'Pie', parent=styles['Normal'], fontSize=7, alignment=TA_CENTER, textColor=colors.grey
    )
    elementos.append(Paragraph(empresa.PIE_PAGINA, pie_style))

    doc.build(elementos)
    return filename



