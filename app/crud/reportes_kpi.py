from sqlalchemy.orm import Session
from sqlalchemy import func,and_,extract
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any

from app.models.cliente import Cliente
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.equipo import Equipo
from app.models.documento_cobro import DocumentoCobro
from app.models.lectura_contador import LecturaContador
from app.models.mantenimiento import Mantenimiento
from app.models.articulo import Articulo

def get_dashboard_kpis(db:Session)->Dict[str, Any]:
    """ Retorna los KPI's principales para el dashboard """

    hoy=date.today()
    mes_actual=hoy.month
    anio_actual=hoy.year

    # Mes anterior
    if mes_actual==1:
        mes_anterior=12
        anio_anterior=anio_actual - 1
    else:
        mes_anterior = mes_actual - 1
        anio_anterior = anio_actual

    # ================== KPIs Básicos =========================
    total_clientes=db.query(Cliente).filter(Cliente.activo==True).count()
    total_contratos=db.query(Contrato).filter(Contrato.activo==True).count()
    total_equipos_rentados=db.query(Equipo).filter(Equipo.estado=="rentado").count()
    total_equipos_disponibles=db.query(Equipo).filter(Equipo.estado=="disponible").count()

    # ================== FACTURACION ===========================
    # Mes actual
    facturacion_mes=db.query(func.coalesce(func.sum(DocumentoCobro.total),0)).filter(
        DocumentoCobro.mes==mes_actual,
        DocumentoCobro.anio==anio_actual,
        DocumentoCobro.tipo=="remision",
        DocumentoCobro.estado.in_(["borrador","emitido"]),
    ).scalar()

    # Mes anterior
    facturacion_mes_anterior=db.query(func.coalesce(func.sum(DocumentoCobro.total),0)).filter(
        DocumentoCobro.mes==mes_anterior,
        DocumentoCobro.anio==anio_anterior,
        DocumentoCobro.tipo=="remision",
        DocumentoCobro.estado.in_(["borrador","emitido"]),
    ).scalar()

    # Porcentajde de cambio
    if facturacion_mes_anterior and facturacion_mes_anterior > 0:
        cambio_porcentaje = (
            (float(facturacion_mes) - float(facturacion_mes_anterior))
            / float(facturacion_mes_anterior)
        ) * 100
    else:
        cambio_porcentaje = 0


    # ================= ALERTAS ====================
    # Contratos por vencer (30 dias)
    from datetime import timedelta
    fecha_limite=hoy+timedelta(days=30)
    contratos_por_vencer=db.query(Contrato).filter(
        Contrato.activo==True,
        Contrato.fecha_fin<=fecha_limite,
        Contrato.fecha_fin>=hoy,
    ).count()

    # Equipos sin lectura este mes
    subquery_lecturas=db.query(LecturaContador.id_contrato_equipo).filter(
        extract('month',LecturaContador.fecha_lectura)==mes_actual,
        extract('year',LecturaContador.fecha_lectura)==anio_actual,
    ).subquery()

    equipos_sin_lectura=db.query(ContratoEquipo).filter(
        ContratoEquipo.activo==True,
        ~ContratoEquipo.id.in_(subquery_lecturas)
    ).count()

    # Stock crítico
    stock_critico=db.query(Articulo).filter(
        Articulo.activo==True,
        Articulo.stock_actual <= Articulo.stock_minimo,
    ).count()

    # Mantenimientos pendientes
    mantenimientos_pendientes=db.query(Mantenimiento).filter(
        Mantenimiento.estado.in_(["en_solicitud","programado","en_proceso","espera_refacciones"])
    ).count()

    #====================== RETORNO ========================
    return {
        "fecha_calculo":datetime.now().isoformat(),
        "periodo_actual":f"{mes_actual}/{anio_actual}",
        "periodo_anterior":f"{mes_anterior}/{anio_anterior}",
        "kpis_basicos":{
            "total_cliente":total_clientes,
            "total_contratos":total_contratos,
            "total_equipos_rentados":total_equipos_rentados,
            "total_equipos_disponibles":total_equipos_disponibles,
        },
        "facturacion": {
            "mes_actual":float(facturacion_mes),
            "mes_anterior":float(mes_anterior),
            "cambio_porcentaje":round(cambio_porcentaje,2)
        },
        "alertas": {
            "contratos_por_vencer_30d":contratos_por_vencer,
            "equipos_sin_lectura_mes":equipos_sin_lectura,
            "stock_critico":stock_critico,
            "mantenimientos_pendientes":mantenimientos_pendientes,
        },
    }