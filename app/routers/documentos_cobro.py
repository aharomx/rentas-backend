from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.documento_cobro import (
    GenerarDocumentoCobroRequest, VistaPreviaRequest,
    DocumentoCobroUpdate, CrearNotaRequest,
    DocumentoCobroResponse, DocumentoCobroResumenResponse,
    VistaPreviaResponse
)
from app.crud import documento_cobro as crud_doc
from app.security import get_current_user, require_roles


router = APIRouter(prefix="/documentos-cobro", tags=["Documentos de cobro"])


# ============== LISTADO Y CONSULTA ==========================

@router.get("/", response_model=List[DocumentoCobroResumenResponse])
def read_documentos(
    skip:int=0,
    limit:int=100,
    tipo:Optional[str]=None,
    estado:Optional[str]=None,
    id_contrato:Optional[int]=None,
    id_cliente:Optional[int]=None,
    mes:Optional[int]=None,
    anio:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    return crud_doc.get_documentos(
        db,
        skip=skip,
        limit=limit,
        tipo=tipo,
        estado=estado,
        id_contrato=id_contrato,
        id_cliente=id_cliente,
        mes=mes,
        anio=anio,
    )

@router.get("/{documento_id}", response_model=DocumentoCobroResponse)
def read_documento(
    documento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_doc = crud_doc.get_documento(db, documento_id)
    if not db_doc:
        raise HTTPException(
            status_code=404,
            detail="Documento no encontrado"
        )
    return db_doc

@router.get("/{documento_id}/notas", response_model=List[DocumentoCobroResumenResponse])
def read_notas(
    documento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Lista las notas asociadas a un documento """

    return crud_doc.get_notas_por_documento(db, documento_id)


# ================== VISTA PREVIA ===============================

@router.post("/vista-previa", response_model=VistaPreviaResponse)
def vista_previa(
    data:VistaPreviaRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Calcula la facturación sin guardar (para revisar antes de generar )"""

    try:
        return crud_doc.calcular_vista_previa(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# ============== GENERAR =========================

@router.post("/generar", response_model=DocumentoCobroResponse, status_code=status.HTTP_201_CREATED)
def generar_documento(
    data:GenerarDocumentoCobroRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"])),
):
    """ Generar una remisión mensual """

    try:
        return crud_doc.generar_documento_cobro(db, data, generado_por_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=.400,
            detal=str(e)
        )


# ==================== ACTUALIZAR ============================

@router.put("/{documento_id}", response_model=DocumentoCobroResponse)
def update_documento(
    documento_id:int,
    data:DocumentoCobroResponse,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    try: 
        db_doc = crud_doc.update_documento(db, documento_id, data)
        if not db_doc:
            raise HTTPException(
                status_code=400,
                detail="Documento no encontrado"
            )
        return db_doc
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ================ EMITIR / CANCELAR =======================

@router.post("/{documento_id}/emitir", response_model=DocumentoCobroResponse)
def emitir_documento(
    documento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    try:
        db_doc=crud_doc.emitir_documento(db,documento_id)
        if not db_doc:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado"
            )
        return db_doc
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/{documento_id}/cancelar", response_model=DocumentoCobroResponse)
def cancelar_documento(
    documento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):
    try:
        db_doc=crud_doc.cancelar_documento(db, documento_id)
        if not db_doc:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado"
            )
        return db_doc
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# ===================== NOTAS =====================

@router.post("/{documento_id}/notas", response_model=DocumentoCobroResponse, status_code=status.HTTP_201_CREATED)
def crear_nota(
    documento_id:int,
    data:CrearNotaRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):
    """ Crea una nota de cargo o crédito. Solo admin/superuser"""

    try:
        return crud_doc.crear_nota(
            db,
            documento_id,
            autorizado_por_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ======================== ELIMINAR ====================
@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_documento(
    documento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):
    try:
        success = crud_doc.delete_documento(db,documento_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Documento no encontrado"
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# ===================== PDF =======================

@router.get("/{documento_id}/pdf")
def descargar_pdf(
    documento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Descarga el PDF del documento de cobro """
    from app.utils.pdf_cobro import generar_pdf_cobro

    db_doc = crud_doc.get_documento(db, documento_id)
    if not db_doc:
        raise HTTPException(
            status_code=404,
            detail="Documento no encontrado"
        )

    try:
        ruta_pdf = generar_pdf_cobro(db, documento_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return FileResponse(
        ruta_pdf,
        media_type="application/pdf",
        filename=f"{db_doc.folio}.pdf",
    )


    