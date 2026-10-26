from pydantic import BaseModel
from decimal import Decimal

class DetalleCobroBolsaResponse(BaseModel):
    id:int
    id_documento:int 
    tipo:str # mono | color
    bolsa_total:int 
    impresiones_mes:int 
    excedentes:int=0
    costo_unitario:Decimal=Decimal("0")
    cargo_excedente:Decimal=Decimal("0")

    class Config:
        from_attributes=True

