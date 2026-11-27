
""" 
    Script para generar alertas automáticamente.
    Diseñado para ejecutarse por cron (ej, cada hora)

    Ejemplo de cron (cada hora):
    0 * * * * cd /ruta/al/proyecto && /ruta/al/venv/bin/python scripts/generar_alertas.py >> logs/alertas.log 2>&1
"""

import sys
import os 
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.database import SessionLocal
from app.services import alerta_service

def main():
    print(f"\n{'=' * 60}")
    print(f"Generación de alertas - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 60}\n")

    db=SessionLocal()
    try:
        resultado=alerta_service.generar_todas_las_alertas(db)

        print(f"Total generadas: {resultado['total_generadas']}")
        print(f"Total omitidas (duplicados): {resultado['total_omitidas_duplicadas']}")
        print()
        print("Detalle por tipo:")
        for tipo, stats in resultado["detalle_por_tipo"].items():
            if stats["generadas"] > 0 or stats["omitidas"] > 0:
                print(f"  {tipo}: {stats["generadas"]} generadas, {stats['omitidas']} omitidas")

        print(f"\n{'=' * 60}")
        print(" Proceso completado")
        print(f"{'=' * 60}\n")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()

    
