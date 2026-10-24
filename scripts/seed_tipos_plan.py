""" 
Script para insertar los tipos de plan base en la base de datos.

Ejecutar: python3 scripts/seed_tipos_plan.py

"""

import sys
import os 

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.tipo_plan import TipoPlan


def seed_tipos_plan():
    db=SessionLocal()

    tipos_plan=[
        {
            "nombre":"solo_renta",
            "descripcion":"Plan que solo cobra renta mensual"
        },
        {
            "nombre":"renta_click",
            "descripcion":"Plan que cobra renta + costo por impresión (Costo global por contrato)"
        },
        {
            "nombre":"renta_bolsa",
            "descripcion":"Plan que cobra renta + bolsa de impresiones + excedentes"
        },
        {
            "nombre":"solo_click",
            "descripción": "plan que solo cobra por impresión (costo global por contrato)"
        },
        {
            "nombre":"costo_diferenciado",
            "descripcion":"Plan con costos por equipo (click mono/color), Renta opcional global o por equipo"
        },
    ]

    print("🌱 Insertando tipos de plan...")
    print("")

    insertados = 0
    existentes = 0

    for tipo in tipos_plan:
        # Verificar si ya existe
        existing=db.query(TipoPlan).filter(TipoPlan.nombre==tipo["nombre"]).first()

        if existing:
            print (f"  ⚠️  Ya existe: {tipo['nombre']}")
            existentes += 1
        else:
            db_tipo=TipoPlan(**tipo)
            db.add(db_tipo)
            print(f"  ✅ Insertado: {tipo['nombre']}")
            insertados += 1

        db.commit()
        db.close()

        print("")
        print("=" * 50)
        print(f"✅ Insertados: {insertados}")
        print(f"⚠️  Ya existían: {existentes}")
        print("=" * 50)
        print("")
        print("🎉 Proceso completado")

        # Verificar
        print("")
        print("📋 Tipos de plan en la base de datos:")
        db=SessionLocal()
        todos=db.query(TipoPlan).order_by(TipoPlan.id).all()
        for t in todos:
            print(f" {t.id}. {t.nombre} - {t.descripcion}")
        db.close()



if __name__=="__main__":
    seed_tipos_plan()