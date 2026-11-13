
"""
Seed de lecturas de contadores para pruebas de facturación.
Usa los contratos existentes en tu BD.

Ejecutar: python scripts/seed_lecturas.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from app.database import SessionLocal
from app.models.lectura_contador import LecturaContador
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.usuario import Usuario


def seed_lecturas():
    db = SessionLocal()
    
    try:
        print("📊 Creando lecturas de contadores...\n")
        
        usuario = db.query(Usuario).filter(Usuario.rol == "superuser").first()
        if not usuario:
            print("❌ No hay usuario superuser.")
            return
        
        # Configuración de lecturas por contrato
        # Formato: {id_contrato: {"agosto": {...}, "septiembre": {...}}}
        config_lecturas = {
            6: {  # solo_renta - HP404-001 (mono)
                "equipo_serie": "HP404-001",
                "agosto": {"mono": 1000, "color": None},
                "septiembre": {"mono": 1500, "color": None},
            },
            7: {  # renta_click - HP479-001 (color)
                "equipo_serie": "HP479-001",
                "agosto": {"mono": 500, "color": 200},
                "septiembre": {"mono": 1200, "color": 800},
            },
            8: {  # renta_bolsa - HP404-002 (mono)
                "equipo_serie": "HP404-002",
                "agosto": {"mono": 0, "color": None},
                "septiembre": {"mono": 1200, "color": None},  # 200 de excedente
            },
            9: {  # costo_diferenciado - HP479-002 (color)
                "equipo_serie": "HP479-002",
                "agosto": {"mono": 0, "color": 0},
                "septiembre": {"mono": 400, "color": 300},
            },
        }
        
        lecturas_creadas = 0
        lecturas_omitidas = 0
        
        for id_contrato, config in config_lecturas.items():
            contrato = db.query(Contrato).filter(Contrato.id == id_contrato).first()
            if not contrato:
                print(f"  ⚠️  Contrato {id_contrato} no encontrado, saltando...")
                continue
            
            # Buscar el contrato_equipo por número de serie
            ce = db.query(ContratoEquipo).join(
                ContratoEquipo.equipo
            ).filter(
                ContratoEquipo.id_contrato == id_contrato,
                ContratoEquipo.activo == True,
            ).first()
            
            if not ce:
                print(f"  ⚠️  Contrato {id_contrato} sin equipos, saltando...")
                continue
            
            equipo_serie = ce.equipo.numero_serie if ce.equipo else "N/A"
            es_color = ce.equipo.modelo.es_color if ce.equipo and ce.equipo.modelo else False
            
            print(f"  📄 Contrato {id_contrato} - {equipo_serie} ({'color' if es_color else 'mono'}):")
            
            # ========== LECTURA AGOSTO 2026 ==========
            existe_ago = db.query(LecturaContador).filter(
                LecturaContador.id_contrato_equipo == ce.id,
                LecturaContador.fecha_lectura == date(2026, 8, 31),
            ).first()
            
            if not existe_ago:
                cont_mono = config["agosto"]["mono"]
                cont_color = config["agosto"]["color"] if es_color else None
                
                # Contador anterior = contador inicial
                cont_ant_mono = ce.contador_inicial_mono or 0
                cont_ant_color = (ce.contador_inicial_color or 0) if es_color else None
                
                lectura_ago = LecturaContador(
                    id_contrato_equipo=ce.id,
                    fecha_lectura=date(2026, 8, 31),
                    tipo_lectura="contadores",
                    contador_mono=cont_mono,
                    contador_color=cont_color,
                    contador_anterior_mono=cont_ant_mono,
                    contador_anterior_color=cont_ant_color,
                    impresiones_mes_mono=max(0, cont_mono - cont_ant_mono),
                    impresiones_mes_color=(
                        max(0, cont_color - cont_ant_color)
                        if es_color and cont_color is not None and cont_ant_color is not None
                        else None
                    ),
                    capturada_por=usuario.id,
                )
                db.add(lectura_ago)
                lecturas_creadas += 1
                print(f"    ✅ Agosto: mono={cont_mono}, color={cont_color if es_color else 'N/A'}")
            else:
                lecturas_omitidas += 1
                print(f"    ⚠️  Agosto ya existe")
            
            # ========== LECTURA SEPTIEMBRE 2026 ==========
            existe_sep = db.query(LecturaContador).filter(
                LecturaContador.id_contrato_equipo == ce.id,
                LecturaContador.fecha_lectura == date(2026, 9, 30),
            ).first()
            
            if not existe_sep:
                cont_mono = config["septiembre"]["mono"]
                cont_color = config["septiembre"]["color"] if es_color else None
                
                # Contador anterior = agosto
                cont_ant_mono = config["agosto"]["mono"]
                cont_ant_color = config["agosto"]["color"] if es_color else None
                
                lectura_sep = LecturaContador(
                    id_contrato_equipo=ce.id,
                    fecha_lectura=date(2026, 9, 30),
                    tipo_lectura="contadores",
                    contador_mono=cont_mono,
                    contador_color=cont_color,
                    contador_anterior_mono=cont_ant_mono,
                    contador_anterior_color=cont_ant_color,
                    impresiones_mes_mono=max(0, cont_mono - cont_ant_mono),
                    impresiones_mes_color=(
                        max(0, cont_color - cont_ant_color)
                        if es_color and cont_color is not None and cont_ant_color is not None
                        else None
                    ),
                    capturada_por=usuario.id,
                )
                db.add(lectura_sep)
                lecturas_creadas += 1
                print(f"    ✅ Septiembre: mono={cont_mono}, color={cont_color if es_color else 'N/A'}")
            else:
                lecturas_omitidas += 1
                print(f"    ⚠️  Septiembre ya existe")
            
            # Actualizar contador_actual
            db.flush()
            ce.contador_actual_mono = config["septiembre"]["mono"]
            if es_color and config["septiembre"]["color"] is not None:
                ce.contador_actual_color = config["septiembre"]["color"]
            
            db.commit()
        
        print(f"\n{'=' * 60}")
        print(f"✅ Lecturas creadas: {lecturas_creadas}")
        print(f"⚠️  Lecturas omitidas: {lecturas_omitidas}")
        print(f"{'=' * 60}")
        
        # Verificar
        print("\n📊 Verificación:")
        total = db.query(LecturaContador).count()
        print(f"   Total de lecturas: {total}")
        
        for id_contrato in config_lecturas.keys():
            ce_ids = [
                ce.id for ce in db.query(ContratoEquipo).filter(
                    ContratoEquipo.id_contrato == id_contrato
                ).all()
            ]
            count = db.query(LecturaContador).filter(
                LecturaContador.id_contrato_equipo.in_(ce_ids)
            ).count() if ce_ids else 0
            print(f"   Contrato {id_contrato}: {count} lecturas")
        
        print("\n🎉 Listo para probar facturación")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_lecturas()