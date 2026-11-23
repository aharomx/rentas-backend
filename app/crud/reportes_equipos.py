from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date 
from typing import List, Dict, Any, Optional

from app.models.equipo import Equipo
from app.models.contrato_equipo import ContratoEquipo
from app.models.contrato import Contrato
from app.models.cliente import Cliente
from app.models.documento_cobro import DocumentoCobro
from app.models.detalle_cobro_equipo import DetalleCobroEquipo
from app.models.movimiento_equipo import MovimientoEquipo

def get_equipos_mas_rentables(
        db:Session,
        limite:int=20,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
) -> List[Dict[str,Any]]:
    """ 
        Top de equipo más rentables (por ingresos generados)
    """
    query=db.query(
        DetalleCobroEquipo.numero_serie,
        DetalleCobroEquipo.modelo,
        func.count(DetalleCobroEquipo.id).label("num_facturas"),
        func.sum(DetalleCobroEquipo.impresiones_mes_mono).label("total_imp_mono"),
        func.sum(DetalleCobroEquipo.impresiones_mes_color).label("total_imp_color"),
        func.sum(DetalleCobroEquipo.subtotal_equipo).label("ingresos_totales"),
    ).join(
        DocumentoCobro, DetalleCobroEquipo.id_documento == DocumentoCobro.id
    ).filter(
        DocumentoCobro.tipo == "remision",
        DocumentoCobro.estado.in_(["borrador", "emitido"]),
    )

    if fecha_inicio:
        query=query.filter(DocumentoCobro.fecha_emision>=fecha_inicio)
    if fecha_fin:
        query=query.filter(DocumentoCobro.fecha_emision<=fecha_fin)

    resultados=query.group_by(
        DetalleCobroEquipo.numero_serie,
        DetalleCobroEquipo.modelo,
    ).order_by(
        func.sum(DetalleCobroEquipo.subtotal_equipo).desc()
    ).limit(limite).all()

    return [
        {
            "numero_serie":r.numero_serie,
            "modelo":r.modelo,
            "num_facturas":r.num_facturas,
            "total_impresiones_mono":r.total_imp_mono or 0,
            "total_impresiones_color":r.total_imp_color or 0,
            "ingresos_totales":float(r.ingresos_totales or 0)
        }
        for r in resultados
    ]

def get_rotacion_equipos(
        db:Session,
        limite:int=50,
) -> List[Dict[str,Any]]:
    """ 
        Rotación de equipos: cuántas veces ha cambiado de contratao cada equipo
    """
    from app.models.movimiento_equipo import MovimientoEquipo

    # Contar transferencias por equipo
    query=db.query(
        MovimientoEquipo.id_equipo,
        func.count(MovimientoEquipo.id).label("num_movimientos"),
    ).filter(
        MovimientoEquipo.tipo_movimiento.in_(["alta","transferencia","baja"])
    ).group_by(
        MovimientoEquipo.id_equipo
    ).order_by(
        func.count(MovimientoEquipo.id).desc()
    ).limit(limite).all()

    resultados=[]
    for r in query:
        equipo=db.query(Equipo).filter(Equipo.id==r.id_equipo).first()
        if not equipo:
            continue

        # Contar altas (veces que entró a un contrato)
        altas=db.query(func.count(MovimientoEquipo.id)).filter(
            MovimientoEquipo.id_equipo==r.id_equipo,
            MovimientoEquipo.tipo_movimiento=="alta",
        ).scalar() or 0

        # Contratos en los que ha estado
        contratos_historial=db.query(ContratoEquipo.id_contrato).filter(
            ContratoEquipo.id_equipo==r.id_equipo,
        ).distinct().all()

        contratos_ids = [c[0] for c in contratos_historial]

        resultados.append({
            "id_equipo":r.id_equipo,
            "numero_serie":equipo.numero_serie,
            "modelo":equipo.modelo.nombre_modelo if equipo.modelo else None,
            "estado_actual":equipo.estado,
            "num_movimientos":r.num_mocimientos,
            "num_altas":altas,
            "num_contratos_historial":len(contratos_ids),
            "contratos_historial":contratos_ids,
        })

    return resultados

