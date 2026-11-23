from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import date 
from typing import List, Dict, Any, Optional

from app.models.documento_cobro import DocumentoCobro
from app.models.cliente import Cliente
from app.models.contrato import Contrato

def get_facturacion_por_periodo(
        db:Session,
        anio:Optional[int]=None,
        id_cliente:Optional[int]=None,
) -> Dict[str,Any]:
    """ Retorna la facturación agrupada por mes """

    query= db.query(
        DocumentoCobro.anio,
        DocumentoCobro.mes,
        func.count(DocumentoCobro.id).label("cantidad"),
        func.sum(DocumentoCobro.subtotal_renta).label("total_renta"),
        func.sum(DocumentoCobro.subtotal_clicks_mono).label("total_clicks_mono"),
        func.sum(DocumentoCobro.subtotal_clicks_color).label("total_clicks_color"),
        func.sum(DocumentoCobro.subtotal_excedente_mono).label("total_excedente_mono"),
        func.sum(DocumentoCobro.subtotal_excedente_color).label("total_excedente_color"),
        func.sum(DocumentoCobro.total).label("total_facturado"),
    ).filter(
        DocumentoCobro.tipo=="remision",
        DocumentoCobro.estado.in_(["borrador","emitiro"]),
    )

    if anio:
        query=query.filter(DocumentoCobro.anio==anio)
    if id_cliente:
        query=query.filter(DocumentoCobro.id_cliente==id_cliente)

    resultados=query.group_by(
        DocumentoCobro.anio, DocumentoCobro.mes
    ).order_by(
        DocumentoCobro.anio.desc(), DocumentoCobro.mes.desc()
    ).all()

    meses = ["Ene","Feb","Mar","Abr","May","Jun",
             "Jul","Ago","Sep","Oct","Nov","Dic"]

    items = []
    total_general=0

    for r in resultados:
        items.append({
            "anio":r.anio,
            "mes":r.mes,
            "periodo":f"{meses[r.mes - 1]} {r.anio}",
            "cantidad_documentos": r.cantidad,
            "total_renta": float(r.total_renta or 0),
            "total_clicks_mono":float(r.total_clicks_mono or 0),
            "total_clicks_color":float(r.total_clicks_color or 0),
            "total_excedente_mono":float(r.total_excedente_mono or 0),
            "total_excedente_color":float(r.total_excedente_color or 0),
            "total_facturado":float(r.total_facturado or 0),
        })
        total_general += (r.total_facturado or 0)

    return {
        "anio_filtro":anio,
        "id_cliente_filtro":id_cliente,
        "total_general":total_general,
        "items":items,
    }

def get_rentabilidad_contrato(
        db:Session,
        id_contrato:int,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
) -> Dict[str,Any]:
    """ Calcula la rentabilidad de un contrato en un peridor """
    from app.models.movimiento_almacen import MovimientoAlmacen
    from app.models.articulo import Articulo
    from app.models.mantenimiento_refaccion import MantenimientoRefaccion
    from app.models.matenimiento_equipo import MantenimientoEquipo
    from app.models.mantenimiento import Mantenimiento
    from sqlalchemy import and_

    contrato = db.query(Contrato).filter(Contrato.id==id_contrato).first()
    if not contrato:
        raise ValueError("Contrato no encontrado")

    cliente = db.query(Cliente).filter(Contrato.id==id_contrato).first()
    if not contrato:
        raise ValueError("Contrato no encontrado")

    cliente=db.query(Cliente).filter(Cliente.id==contrato.id_cliente).first()

    # ============= INGRESOS =================
    query_ingresos=db.query(
        func.coalesce(func.sum(DocumentoCobro.total),0)
    ).filter(
        DocumentoCobro.id_cliente==id_contrato,
        DocumentoCobro.tipo=="remision",
        DocumentoCobro.estado.in_(["borrador","emitido"]),
    )

    if fecha_inicio:
        query_ingresos=query_ingresos.filter(
            DocumentoCobro.fecha_emision  >= fecha_inicio
        )
    if fecha_fin:
        query_ingresos=query_ingresos.filger(
            DocumentoCobro.fecha_emision <= fecha_fin
        )

    total_ingresos=query_ingresos.scalar() or 0

    # Nostas de credito (restan)
    query_notas_credito=db.query(
        func.coalesce(func.sum(DocumentoCobro.total), 0)
    ).filter(
        DocumentoCobro.id_contrato==id_contrato,
        DocumentoCobro.tipo=="nota_credito",
        DocumentoCobro.estado=="emitido",
    )

    if fecha_inicio:
        query_notas_credito=query_notas_credito.filter(
            DocumentoCobro.fecha_emision>=fecha_inicio
        )
    if fecha_fin:
        query_notas_credito=query_notas_credito.filter(
            DocumentoCobro.fecha_emision<=fecha_fin
        )

    total_notas_credito=query_notas_credito.scalar() or 0

    # Notas de cargo (suman)
    query_notas_cargo=db.query(
        func.coalesce(func.sum(DocumentoCobro.total),0)
    ).filter(
        DocumentoCobro.id==id_contrato,
        DocumentoCobro.tipo=="nota_cargo",
        DocumentoCobro.estado=="emitido",
    )

    if fecha_inicio:
        query_notas_cargo=query_notas_cargo.filter(
            DocumentoCobro.fecha_emision >= fecha_inicio
        )

    if fecha_fin:
        query_notas_cargo=query_notas_cargo.filter(
            DocumentoCobro.fecha_emision<=fecha_fin
        )

    total_notas_cargo = query_notas_cargo.scalar() or 0

    ingresos_netos = float(total_ingresos) + float(total_notas_cargo) - float(total_notas_credito)

    # ============== COSTOS ====================
    # Costo de refacciones usadas en mantenimientos del contrato
    query_costos = db.query(
        func.coalesce(func.sum(MantenimientoRefaccion.cantidad * Articulo.costo), 0)
    ). join(
        Articulo, MantenimientoRefaccion.id_articulo == Articulo.id
    ).join(
        MantenimientoEquipo, MantenimientoRefaccion.id_mantenimiento_equipo==MantenimientoEquipo.id
    ).join(
        Mantenimiento, MantenimientoEquipo.id_mantenimiento==Mantenimiento.id
    ).filter(
        Mantenimiento.id_contrato==id_contrato,
        Mantenimiento.estado=="completado",
    )

    if fecha_inicio:
        query_costos=query_costos.filter(
            Mantenimiento.fecha_solicitud>=fecha_inicio
        )
    if fecha_fin:
        query_costos=query_costos.filter(
            Mantenimiento.fecha_solicitud<=fecha_fin
        )

    total_costos=query_costos.scalar() or 0

    # ============= RESULTADO ==============
    utilidad=ingresos_netos-float(total_costos)
    margen=(utilidad/ingresos_netos * 100) if ingresos_netos>0 else 0

    return {
        "id_contrato":id_contrato,
        "cliente_nombre":cliente.razon_social if cliente else None,
        "fecha_inicio":fecha_inicio.isoformat() if fecha_inicio else None,
        "fecha_fin":fecha_fin.isoformat() if fecha_fin else None,
        "ingresos": {
            "remisiones":float(total_ingresos),
            "notas_cargo":float(total_notas_cargo),
            "notas_credito":float(total_notas_credito),
            "ingresos_netos":ingresos_netos
        },
        "costos": {
            "refacciones_mantenimientos":float(total_costos),
        },
        "resultado":{
            "utilidad":round(utilidad,2),
            "margen_porcentaje":round(margen,2)
        },
    }

