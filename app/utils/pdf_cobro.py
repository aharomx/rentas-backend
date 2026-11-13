from sqlalchemy.orm import Session
from app.models.documento_cobro import DocumentoCobro
from datetime import datetime
import os 


def generar_pdf_cobro(db:Session, documento_id:int, output_dir:str = "pdfs") -> str:
    """ 
        STUB TEMPORAL - Se reemplazará con el PDF completo.
    """

    os.makedirs(output_dir, exist_ok=True)

    doc = db.query(DocumentoCobro).filter(DocumentoCobro.id == documento_id).first()
    if not doc:
        raise ValueError("Documento no encontrado")

    # Placeholder: crea un archivo dummy
    filename = f"{output_dir}/{doc.folio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    # Crear un PDF mínimo con reportlab

    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c= canvas.Canvas(filename, pagesize=letter)
    c.drawString(100,750,f"Documento: {doc.folio}")
    c.drawString(100,730,f"Cliente: {doc.cliente_nombre or ''}")
    c.drawString(100,710,f"Periodo: {doc.periodo}")
    c.drawString(100,690,f"Total: ${doc.total}")
    c.drawString(100,650,"(PDF en construcción - versión completa en próxima fase)")
    c.save()

    return filename

