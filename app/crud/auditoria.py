from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.auditoria_acceso import AuditoriaAcceso


def registrar_acceso(
        db:Session,
        accion:str,
        id_usuario:Optional[int]=None,
        username_intento:Optional[str]=None,
        ip:Optional[str]=None,
        user_agent:Optional[str]=None,
        exito:bool=True,
        detalle:Optional[str]=None
) -> AuditoriaAcceso:
    registro=AuditoriaAcceso(
        id_usuario=id_usuario,
        username_intento=username_intento,
        accion=accion,
        ip=ip,
        user_agent=user_agent,
        exito=exito,
        detalle=detalle
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


def get_auditoria(
        db:Session,
        skip:int=0,
        limit:int=100,
        id_usuario:Optional[int]=None,
        accion:Optional[str]=None
) -> List[AuditoriaAcceso]:

    query=db.query(AuditoriaAcceso)
    if id_usuario:
        query=query.filter(AuditoriaAcceso.id_usuario==id_usuario)

    if accion:
        query=query.filter(AuditoriaAcceso.accion==accion)

    return query.order_by(AuditoriaAcceso.fecha.desc()).offset(skip).limit(limit).all()


