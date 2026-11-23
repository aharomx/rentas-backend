from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from typing import List, Dict, Any, Optional

from app.models.contrato import Contrato
from app.models.cliente import Cliente
from app.models.tipo_plan import TipoPlan
from app.models.documento_cobro import DocumentoCobro

def get_contratos_por_vencer(
        db:Session,
        dias:int=30,
) -> List[Dict[str,Any]]:
    """ Contratos que vencen en los próximos N días """

    hoy = date.today()
    fecha_limite = hoy + timedelta(days=dias)

    contratos = db.query(Contrato).filter(
        Contrato.activo==True,
        Contrato.fecha_fin<=fecha_limite,
        Contrato.fecha_fin>=hoy,
    ).order_by(Contrato.fecha_fin.asc()).all()

    resultados=[]

    for c in contratos:
        cliente=db.query(Cliente).filter(Cliente.id==c.id_cliente).first()
        plan=db.query(TipoPlan).filter(TipoPlan.id==c.id_tipo_plan).first()
        dias_restantes=(c.fecha_fin-hoy).days

        resultados.append({
            "id_contrato":c.id,
            "cliente_nombre":cliente.razon_social if cliente else None,
            "tipo_plan":plan.nombre if plan else None,
            "fecha_fin":c.fecha_fin.isoformat(),
            "dias_restantes":dias_restantes,
            "costo_renta_mensual":float(c.costo_renta_mensual or 0),
        })

    return resultados 

def get_contratos_mas_rentables(
        db:Session,
        limite:int=20,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
) -> List[Dict[str,Any]]:
    """ Top Contratos por facturación total """

    query=db.query(
        DocumentoCobro.id_contrato,
        func.count(DocumentoCobro.id).label("num_facturas"),
        func.sum(DocumentoCobro.total).label("total_facturado")
    ).filter(
        DocumentoCobro.tipo=="remision",
        DocumentoCobro.estado.in_(["borrador","emitido"]),
    )

    if fecha_inicio:
        query=query.filter(DocumentoCobro.fecha_emision>=fecha_inicio)
    if fecha_fin:
        query=query.filter(DocumentoCobro.fecha_emision<=fecha_fin)

    resultados = query.group_by(
        DocumentoCobro.id_contrato
    ).order_by(
        func.sum(DocumentoCobro.total).desc()
    ).limit(limite).all()

    items=[]
    for r in resultados:
        contrato=db.query(Contrato).filter(Contrato.id==r.id_Contrato).first()
        if not contrato:
            continue

        cliente=db.query(Cliente).filter(Cliente.id==contrato.id_cliente).first()
        plan=db.query(TipoPlan).filter(TipoPlan.id==contrato.id_tipo_plan).first()

        items.append({
            "id_contrato":r.id_contrato,
            "cliente_nombre":cliente.razon_social if cliente else None,
            "tipo_plan":plan.nombre if plan else None,
            "num_facturas":r.num_facturas,
            "total_facturado":float(r.total_facturado or 0),
        })

    return items



