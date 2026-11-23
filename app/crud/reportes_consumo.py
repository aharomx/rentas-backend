from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import date 
from typing import Dict, Any, List, Optional
from decimal import Decimal

from app.models.cliente import Cliente
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.equipo import Equipo
from app.models.inventario_cliente import InventarioCliente
from app.models.articulo import Articulo
from app.models.lectura_contador import LecturaContador
from app.models.solicitud_almacen import SolicitudAlmacen
from app.models.solicitud_almacen_detalle import SolicitudAlmacenDetalle

def get_consumo_toner_por_cliente(
        db:Session,
        id_cliente:Optional[int]=None,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
) -> Dict[str,Any]:
    """ 
        Consumo de tóner por cliente en un periodo.
        Cuenta los tóners entregados (por  tipo:negro, magenta, amarillo)
    """

    # Query base: tóners entregados a clientes
    query=db.query(
        SolicitudAlmacen.id_cliente,
        Articulo.codigo,
        Articulo.nombre,
        func.count(SolicitudAlmacenDetalle.id).label("cantidad"),
        func.sum(Articulo.costo * 1).label("costo_total"), # Costo unitario x 1
    ).join(
        SolicitudAlmacenDetalle, SolicitudAlmacenDetalle.id_articulo==SolicitudAlmacen.id
    ).join(
        Articulo, SolicitudAlmacenDetalle.id_articulo==Articulo.id
    ).filter(
        SolicitudAlmacen.tipo=="entrega",
        SolicitudAlmacen.estado.in_(["entregado","devolucion_parcial","devoulcion_total"]),
        Articulo.tipo=="toner",
    )

    if id_cliente:
        query=query.filter(SolicitudAlmacen.id_cliente==id_cliente)
    if fecha_inicio:
        query=query.filter(SolicitudAlmacen.fecha_entrega>=fecha_inicio)
    if fecha_fin:
        query=query.filter(SolicitudAlmacen.fecha_entrega<=fecha_fin)

    resultados=query.group_by(
        SolicitudAlmacen.id_cliente,
        Articulo.id,
        Articulo.codigo,
        Articulo.nombre
    ).all()

    # Agrupaor por cliente
    clientes_dict={}
    for r in resultados:
        if r.id_cliente not in clientes_dict:
            cliente=db.query(Cliente).filter(Cliente.id==r.id_cliente).first()
            clientes_dict[r.id_cliente]={
                "id_cliente":r.id_cliente,
                "cliente_nombre":cliente.razon_social if cliente else None,
                "toners":[],
                "total_toners":0,
                "costo_total":0
            }

        # Clasificar por color (deducir del nombre/código)
        color=_clasificar_color_toner(r.codigo, r.nombre)

        clientes_dict[r.id_cliente]["toners"].append({
            "id_articulo":None, # No lo tenemos en la query
            "codigo":r.codigo,
            "nombre":r.nombre,
            "color":r.color,
            "cantidad":r.cantidad,
            "costo_unitario":float(Articulo.costo) if hasattr(r,'costo') else 0,
            "costo_total":float(r.costo_total or 0),
        })
        clientes_dict[r.id_cliente]["total_toners"] += r.cantidad
        clientes_dict[r.id_cliente]["costo_total"] +=  float(r.costo_total or 0)

    # Calcular totales generales
    total_general_toners=sum(c["total_toners"] for c in clientes_dict.values())
    total_general_costo=sum(c["costo_total"] for c in clientes_dict.values())

    return {
        "fecha_inicios":fecha_inicio.isoformat() if fecha_inicio else None,
        "fecha_fin":fecha_fin.isoformat() if fecha_fin else None,
        "id_cliente_filtro":id_cliente,
        "total_toners":total_general_toners,
        "costo_total":round(total_general_costo),
        "clientes":list(clientes_dict.values()),
    }

def _clasificar_color_toner(codigo:str, nombre:str) -> str:
    """Clasifica el color del tóner basado en codigo/nombre"""

    texto= f"{codigo} {nombre}".upper()
    if "NEGRO" in texto or "BLACK" in texto or "-K" in texto:
        return "negro"
    elif "CYAN" in texto or "-C" in texto:
        return "cyan"
    elif "MAGENTA" in texto or "-M" in texto:
        return "magenta"
    elif "AMARILLO" in texto or "YELLOW" in texto or "-Y" in texto:
        return "amarillo"
    return "otro"

def get_consumo_real_vs_esperado(
        db:Session,
        id_cliente: Optional[int]=None,
        id_contrato:Optional[int]=None,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
        porcentaje_cobertura:Decimal=Decimal("5"),
) -> Dict[str,Any]:
    """ 
        Reporte de consumo real vs esperado de tóner,

        Calcula:
        - Tóners enciados al cliente en el periodo
        - Impresiones reales del periodo
        - Rendimiento esperado segun el modelo del equipo
        - Comparación con el % de cobertura definido por el usuario

        El % de cobertura indica qué porcentaje del rendimiento teórico se espera
        que se cubra con las impresiones. Ej: si un tóner rinde 3000 paginas al 5%,
        el redimiento esperado con una cobertura mayor al 5% será menor a las 3000
        paginas esperadas.
    """

    #Query base: contratos a analizar
    query_contratos=db.query(Contrato).filter(Contrato.activo==True)

    if id_cliente:
        query_contratos=query_contratos.filter(Contrato.id_cliente==id_cliente)
    if id_contrato:
        query_contratos=query_contratos.filter(Contrato.id==id_contrato)

    contratos=query_contratos.all()

    resultados=[]
    total_impresiones=0
    total_toners=0
    total_costo=0

    for contrato in contratos:
        cliente=db.query(Cliente).filter(Cliente.id==contrato.id_cliente).first()

        # Tóners entregados al cliente en el periodo
        query_toners=db.query(
            Articulo.codigo,
            Articulo.nombre,
            func.count(SolicitudAlmacenDetalle.id).label("cantidad"),
        ).join(
            SolicitudAlmacenDetalle, SolicitudAlmacenDetalle.id_articulo==Articulo.id
        ).join(
            SolicitudAlmacen, SolicitudAlmacenDetalle.id_solicitud==SolicitudAlmacen.id
        ).filter(
            SolicitudAlmacen.tipo=="entrega",
            SolicitudAlmacen.estado.in_(["entregado","devolucion_parcial","devolucion_total"]),
            SolicitudAlmacen.id_cliente==contrato.id_cliente,
            Articulo.tipo=="toner",
        )

        if fecha_inicio:
            query_toners=query_toners.filter(SolicitudAlmacen.fecha_entrega>=fecha_inicio)
        if fecha_fin:
            query_toners=query_toners._from_selectable(SolicitudAlmacen.fecha_entrega<=fecha_fin)

        toners=query_toners.group_by(Articulo.codigo, Articulo.nombre).all()

        # Contar tóners por color
        toners_por_color={
            "negro":0,
            "cyan":0,
            "magenta":0,
            "amarillo":0
        }

        toners_detalle=[]

        for t in toners:
            color=_clasificar_color_toner(t.codigo, t.nombre)
            if color in toners_por_color:
                toners_por_color[color] += t.cantidad
            toners_detalle.append({
                "codigo":t.codigo,
                "nombre":t.nombre,
                "color":color,
                "cantidad":t.cantidad
            })

        # Impresiones del periodo (desde lecturas)
        equipos=db.query(ContratoEquipo).filter(
            ContratoEquipo.id_contrato==contrato.id,
            ContratoEquipo.activo==True,
        ).all()

        total_imp_mono=0
        total_imp_color=0
        equipos_detalle=[]

        for ce in equipos:
            # Buscar lecturas del periodo
            query_lecturas=db.query(LecturaContador).filter(
                LecturaContador.fecha_lectura>=fecha_inicio
            )
            if fecha_inicio:
                query_lecturas=query_lecturas.filter(
                    LecturaContador.fecha_lectura>=fecha_inicio
                )
            if fecha_fin:
                query_lecturas=query_lecturas.filter(
                    LecturaContador.fecha_lectura<=fecha_fin
                )

            lecturas=query_lecturas.all()

            # Primera y última lectura del periodo
            if lecturas:
                primera=min(lecturas, key=lambda l:l.fecha_lectura)
                ultima=max(lecturas, key=lambda l:l.fecha_lectura)

                imp_mono=max(0,(ultima.contador_mono or 0) - (primera.contador_anterior_mono or primera.contador_mono or 0))
                imp_color=max(0,(ultima.contador_color or 0) - (primera.contador_anterior_color or primera.contador_color or 0))

                total_imp_mono += imp_mono
                total_imp_color += imp_color

                equipos_detalle.append({
                    "numero_serie":ce.equipo.numero_serie if ce.equipo else None,
                    "impresiones_mono":imp_mono,
                    "impresiones_color":imp_color,
                })

            # Calcular rendimiento esperado
            # Para simpliciar: usar rendimiento del modelo x % de cobertura
            
            rendimiento_esperado_mono=0
            rendimiento_esperado_color=0

            for ce in equipos:
                if ce.equipo and ce.equipo.modelo:
                    modelo=ce.equipo.modelo

                    # Tóner negro: (Cantidad de toners negros x rendimiento_negro)
                    cant_negro=toners_por_color.get("negro",0)
                    if modelo.rendimiento_toner_negro:
                        rendimiento_esperado_mono += (
                            cant_negro
                            * modelo.rendimiento_toner_negro
                        )

                    # Tóners color: (Cantidad de toners negros x rendimiento_color)
                    if modelo.es_color and modelo.rendimiento_toner_color:
                        for color in ["cyan","magenta","amarillo"]:
                            cant_color=toners_por_color.get(color,0)
                            rendimiento_esperado_color += (
                                cant_color
                                * modelo.rendimiento_toner_color
                            )

            # Comparación
            # Impresiones mono se comparan con rendimiento esperado mono + color
            # (Porque las impresiones en negro usan tóner negro de cualquier equipo)
            impresiones_totales=total_imp_mono + total_imp_color

            if rendimiento_esperado_mono > 0:
                cobertura_mono_pct=(total_imp_mono/rendimiento_esperado_mono) * 100
            else:
                cobertura_mono_pct=0

            if rendimiento_esperado_color > 0:
                cobertura_color_pct=(total_imp_color/rendimiento_esperado_color)*100
            else:
                cobertura_color_pct=0

            # Determinar alerta
            alertas=[]

            if cobertura_mono_pct<60 and toners_por_color["negro"]>0:
                alertas.append("Consumo de tóner negro por debajo de lo esperado (<60%)")
            elif cobertura_mono_pct > 120 and toners_por_color["negro"]>0:
                alertas.append("" \
                "consumo de tóner negro por encima de lo esperado (>120%)")

            if cobertura_color_pct<60 and (toners_por_color["cyan"]+toners_por_color["magenta"]+toners_por_color["amarillo"])>0:
                alertas.append("Consumo de tóner color por debajo de lo esperado (<60%)")
            elif cobertura_color_pct>120 and (toners_por_color["cyan"]+toners_por_color["magenta"]+toners_por_color["amarillo"])>0:
                alertas.append("Consumo de tóner color por encima de lo esperado (>120%)")

            resultados.append({
                "id_contrato":contrato.id,
                "id_cliente":contrato.id_cliente,
                "cliente_nombre":cliente.razon_social if cliente else None,
                "toners_enviados":{
                    "negro":toners_por_color["negro"],
                    "cyan":toners_por_color["cyan"],
                    "magenta":toners_por_color["magenta"],
                    "amarillo":toners_por_color["amarillo"],
                    "total":sum(toners_por_color.values()),
                    "detalle":toners_detalle,
                },
                "impresiones":{
                    "mono":round(rendimiento_esperado_mono,0),
                    "color":round(rendimiento_esperado_color,0)
                },
                "comparacion":{
                    "cobertura_mono_pct":round(cobertura_mono_pct,2),
                    "cobertura_color_pct":round(cobertura_color_pct,2),
                    "porcentaje_cobertura_usado":float(porcentaje_cobertura),
                },
                "alertas":alertas,
            })

            total_impresiones += impresiones_totales
            total_toners += sum(toners_por_color.values())

    return {
        "fecha_inicio":fecha_inicio.isoformat() if fecha_inicio else None,
        "fecha_fin":fecha_fin.isoformat() if fecha_fin else None,
        "porcentaje_cobertura":float(porcentaje_cobertura),
        "total_contratos_analizados":len(resultados),
        "total_impresiones":total_impresiones,
        "total_toners":total_toners,
        "resultados":resultados,
    }

