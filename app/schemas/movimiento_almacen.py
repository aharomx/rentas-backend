from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class MovimientoAlmacenBase(BaseModel):
    id_articulo:int
    tipo:str # entrada,saiida,devolucion,ajuste_positivo,ajuste_negativo,desecho
    cantidad:int=Field(...,gt=0,description="Cantidad mayor a 0")
    numero_serie_toner:Optional[str]=None
    motivo:Optional[str]=None
    referencia:Optional[str]=None
    id_solicitud_almacen:Optional[int]=None
    id_mantenimiento:Optional[int]=None
    observaciones:Optional[str]=None


class MovimientoAlmacenCreate(MovimientoAlmacenBase):
    pass


class MovimientoAlmacenResponse(MovimientoAlmacenBase):
    id:int
    stock_anterior:int 
    stock_nuevo:int 
    registrado_por:Optional[int]=None
    fecha_movimiento:datetime

    #Datos enriquecidos
    articulo_codigo:Optional[str]=None
    articulo_nombre:Optional[str]=None
    usuario_nombre:Optional[str]=None

    class Config:
        from_attributes=True


# ================= REPORTES =======================
class KardexItem(BaseModel):
    """ Elemento del Kardex (historial de un articulo)"""
    id:int 
    tipo:str 
    cantidad:int 
    stock_anterior:int 
    stock_nuevo:int 
    motivo:Optional[str]=None 
    referencia:Optional[str]=None
    numero_serie_toner:Optional[str]=None
    observaciones:Optional[str]=None
    usuario_nombre:Optional[str]=None
    fecha_movimiento:datetime

    class Config:
        from_attributes=True


class StockBajoItem(BaseModel):
    """ Articulos con stock bajo (por debajo del mínimo)"""
    id:int 
    codigo:str 
    nombre:str 
    tipo:str 
    stock_actual:int 
    stock_minimo:int 
    faltante:int #stock_minimo - stock_actual
    categoria_nombre:Optional[str]=None

    class Config:
        from_attributes=True


class ResumenMovimientos(BaseModel):
    total_entradas:int 
    total_salidas:int 
    total_devoluciones:int 
    total_ajustes:int 
    total_desechos:int 
    movimientos:list[MovimientoAlmacenResponse]