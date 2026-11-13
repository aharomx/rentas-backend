"""
Script de seed para pruebas completas.
Crea todos los datos base necesarios.

Ejecutar: python scripts/seed_datos_prueba.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from decimal import Decimal
from app.database import SessionLocal
from app.security import hash_password

# Imports de modelos
from app.models.usuario import Usuario
from app.models.tipo_plan import TipoPlan
from app.models.categoria_articulo import CategoriaArticulo
from app.models.modelo_impresora import ModeloImpresora
from app.models.cliente import Cliente, DireccionCliente, ContactoCliente
from app.models.articulo import Articulo
from app.models.equipo import Equipo
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo


def seed():
    db = SessionLocal()
    
    try:
        print("🌱 Iniciando seed de datos de prueba...")
        print("")
        
        # ========== 1. USUARIOS ==========
        print("👤 Creando usuarios...")
        
        usuarios = [
            {
                "username": "sysdba",
                "email": "sysdba@test.com",
                "password": "masterkey",
                "nombre_completo": "Super Usuario",
                "rol": "superuser",
            },
            {
                "username": "admin1",
                "email": "admin1@test.com",
                "password": "admin12345",
                "nombre_completo": "Admin Uno",
                "rol": "admin",
            },
            {
                "username": "coord1",
                "email": "coord1@test.com",
                "password": "coord12345",
                "nombre_completo": "Coordinador Uno",
                "rol": "coordinador",
            },
            {
                "username": "tec1",
                "email": "tec1@test.com",
                "password": "tec12345",
                "nombre_completo": "Técnico Uno",
                "rol": "tecnico",
            },
            {
                "username": "alm1",
                "email": "alm1@test.com",
                "password": "alm12345",
                "nombre_completo": "Almacenista Uno",
                "rol": "almacenista",
            },
        ]
        
        for u in usuarios:
            existente = db.query(Usuario).filter(Usuario.username == u["username"]).first()
            if existente:
                print(f"  ⚠️  Usuario ya existe: {u['username']}")
                continue
            
            db_user = Usuario(
                username=u["username"],
                email=u["email"],
                password_hash=hash_password(u["password"]),
                nombre_completo=u["nombre_completo"],
                rol=u["rol"],
                activo=True,
                requiere_cambio_password=False,
            )
            db.add(db_user)
            print(f"  ✅ {u['username']} ({u['rol']})")
        
        db.commit()
        
        # ========== 2. TIPOS DE PLAN ==========
        print("\n📋 Creando tipos de plan...")
        
        tipos = [
            {"nombre": "solo_renta", "descripcion": "Solo cobra renta mensual"},
            {"nombre": "renta_click", "descripcion": "Renta + click (global)"},
            {"nombre": "renta_bolsa", "descripcion": "Renta + bolsa + excedente"},
            {"nombre": "solo_click", "descripcion": "Solo click (global)"},
            {"nombre": "costo_diferenciado", "descripcion": "Costos por equipo"},
        ]
        
        for t in tipos:
            existente = db.query(TipoPlan).filter(TipoPlan.nombre == t["nombre"]).first()
            if existente:
                print(f"  ⚠️  Tipo ya existe: {t['nombre']}")
                continue
            db.add(TipoPlan(**t))
            print(f"  ✅ {t['nombre']}")
        
        db.commit()
        
        # ========== 3. CATEGORÍAS DE ARTÍCULOS ==========
        print("\n📦 Creando categorías de artículos...")
        
        categorias = [
            {"nombre": "Tóners", "descripcion": "Cartuchos de tóner"},
            {"nombre": "Refacciones", "descripcion": "Rodillos, fusores, etc."},
            {"nombre": "Kits", "descripcion": "Kits de mantenimiento"},
        ]
        
        for c in categorias:
            existente = db.query(CategoriaArticulo).filter(CategoriaArticulo.nombre == c["nombre"]).first()
            if existente:
                print(f"  ⚠️  Categoría ya existe: {c['nombre']}")
                continue
            db.add(CategoriaArticulo(**c))
            print(f"  ✅ {c['nombre']}")
        
        db.commit()
        
        # ========== 4. MODELOS DE IMPRESORAS ==========
        print("\n🖨️  Creando modelos de impresoras...")
        
        modelos = [
            {
                "nombre_modelo": "HP LaserJet Pro M404dn",
                "es_color": False,
                "velocidad_ppm": 40,
                "rendimiento_toner_negro": 3000,
                "rendimiento_toner_color": 0,
            },
            {
                "nombre_modelo": "HP Color LaserJet Pro M479fdw",
                "es_color": True,
                "velocidad_ppm": 28,
                "rendimiento_toner_negro": 2400,
                "rendimiento_toner_color": 2100,
            },
        ]
        
        for m in modelos:
            existente = db.query(ModeloImpresora).filter(
                ModeloImpresora.nombre_modelo == m["nombre_modelo"]
            ).first()
            if existente:
                print(f"  ⚠️  Modelo ya existe: {m['nombre_modelo']}")
                continue
            db.add(ModeloImpresora(**m))
            print(f"  ✅ {m['nombre_modelo']}")
        
        db.commit()
        
        # ========== 5. CLIENTES ==========
        print("\n🏢 Creando clientes...")
        
        cliente1 = db.query(Cliente).filter(Cliente.rfc == "TEM123456ABC").first()
        if not cliente1:
            cliente1 = Cliente(
                razon_social="Tecnología Empresarial SA de CV",
                nombre_comercial="TechEmp",
                rfc="TEM123456ABC",
                email_empresa="contacto@techempresa.com",
                telefono_empresa="5555555555",
                tipo_persona="moral",
            )
            db.add(cliente1)
            db.flush()
            
            db.add(DireccionCliente(
                id_cliente=cliente1.id,
                tipo_direccion="fiscal",
                es_principal=True,
                calle="Av. Reforma",
                numero_exterior="123",
                colonia="Centro",
                codigo_postal="06000",
                ciudad="Ciudad de México",
                estado="CDMX",
            ))
            
            db.add(ContactoCliente(
                id_cliente=cliente1.id,
                nombre="Juan Pérez",
                puesto="Gerente",
                email="juan@techempresa.com",
                roles=["administracion", "compras"],
                es_principal=True,
            ))
            print(f"  ✅ {cliente1.razon_social}")
        
        cliente2 = db.query(Cliente).filter(Cliente.rfc == "RASP800101ABC").first()
        if not cliente2:
            cliente2 = Cliente(
                razon_social="Pedro Ramírez Sánchez",
                rfc="RASP800101ABC",
                email_empresa="pedro@email.com",
                tipo_persona="fisica",
            )
            db.add(cliente2)
            print(f"  ✅ {cliente2.razon_social}")
        
        db.commit()
        db.refresh(cliente1)
        db.refresh(cliente2)
        
        # ========== 6. ARTÍCULOS ==========
        print("\n📦 Creando artículos...")
        
        cat_toners = db.query(CategoriaArticulo).filter(CategoriaArticulo.nombre == "Tóners").first()
        cat_ref = db.query(CategoriaArticulo).filter(CategoriaArticulo.nombre == "Refacciones").first()
        cat_kits = db.query(CategoriaArticulo).filter(CategoriaArticulo.nombre == "Kits").first()
        
        modelo_mono = db.query(ModeloImpresora).filter(ModeloImpresora.es_color == False).first()
        modelo_color = db.query(ModeloImpresora).filter(ModeloImpresora.es_color == True).first()
        
        articulos = [
            {"codigo": "TON-HP404-NEGRO", "nombre": "Tóner Negro HP M404", "tipo": "toner",
             "id_categoria": cat_toners.id, "modelo_compatible": modelo_mono.id, "stock_actual": 20},
            {"codigo": "TON-HP479-NEGRO", "nombre": "Tóner Negro HP M479", "tipo": "toner",
             "id_categoria": cat_toners.id, "modelo_compatible": modelo_color.id, "stock_actual": 15},
            {"codigo": "TON-HP479-CYAN", "nombre": "Tóner Cyan HP M479", "tipo": "toner",
             "id_categoria": cat_toners.id, "modelo_compatible": modelo_color.id, "stock_actual": 10},
            {"codigo": "TON-HP479-MAGENTA", "nombre": "Tóner Magenta HP M479", "tipo": "toner",
             "id_categoria": cat_toners.id, "modelo_compatible": modelo_color.id, "stock_actual": 10},
            {"codigo": "TON-HP479-AMARILLO", "nombre": "Tóner Amarillo HP M479", "tipo": "toner",
             "id_categoria": cat_toners.id, "modelo_compatible": modelo_color.id, "stock_actual": 10},
            {"codigo": "ROD-HP404-001", "nombre": "Rodillo HP M404", "tipo": "refaccion",
             "id_categoria": cat_ref.id, "modelo_compatible": modelo_mono.id, "stock_actual": 15},
            {"codigo": "KIT-MANT-HP404", "nombre": "Kit Mantenimiento HP M404", "tipo": "kit",
             "id_categoria": cat_kits.id, "modelo_compatible": modelo_mono.id, "stock_actual": 8},
        ]
        
        for a in articulos:
            existente = db.query(Articulo).filter(Articulo.codigo == a["codigo"]).first()
            if existente:
                print(f"  ⚠️  Artículo ya existe: {a['codigo']}")
                continue
            
            # Nota: stock_actual se maneja por movimientos, pero para seed directo lo ponemos
            db_art = Articulo(
                codigo=a["codigo"],
                nombre=a["nombre"],
                tipo=a["tipo"],
                id_categoria=a["id_categoria"],
                modelo_compatible=a["modelo_compatible"],
                stock_actual=a["stock_actual"],
                stock_minimo=3,
            )
            db.add(db_art)
            print(f"  ✅ {a['codigo']}")
        
        db.commit()
        
        # ========== 7. EQUIPOS ==========
        print("\n🖨️  Creando equipos...")
        
        equipos = [
            {"numero_serie": "HP404-001", "id_modelo": modelo_mono.id, "estado": "disponible"},
            {"numero_serie": "HP404-002", "id_modelo": modelo_mono.id, "estado": "disponible"},
            {"numero_serie": "HP479-001", "id_modelo": modelo_color.id, "estado": "disponible"},
            {"numero_serie": "HP479-002", "id_modelo": modelo_color.id, "estado": "disponible"},
        ]
        
        for e in equipos:
            existente = db.query(Equipo).filter(Equipo.numero_serie == e["numero_serie"]).first()
            if existente:
                print(f"  ⚠️  Equipo ya existe: {e['numero_serie']}")
                continue
            db.add(Equipo(**e))
            print(f"  ✅ {e['numero_serie']}")
        
        db.commit()
        
        # ========== 8. CONTRATOS DE PRUEBA ==========
        print("\n📄 Creando contratos de prueba...")
        
        tp_solo_renta = db.query(TipoPlan).filter(TipoPlan.nombre == "solo_renta").first()
        tp_renta_click = db.query(TipoPlan).filter(TipoPlan.nombre == "renta_click").first()
        tp_renta_bolsa = db.query(TipoPlan).filter(TipoPlan.nombre == "renta_bolsa").first()
        tp_solo_click = db.query(TipoPlan).filter(TipoPlan.nombre == "solo_click").first()
        tp_diferenciado = db.query(TipoPlan).filter(TipoPlan.nombre == "costo_diferenciado").first()
        
        eq_mono1 = db.query(Equipo).filter(Equipo.numero_serie == "HP404-001").first()
        eq_mono2 = db.query(Equipo).filter(Equipo.numero_serie == "HP404-002").first()
        eq_color1 = db.query(Equipo).filter(Equipo.numero_serie == "HP479-001").first()
        eq_color2 = db.query(Equipo).filter(Equipo.numero_serie == "HP479-002").first()
        
        # Contrato 1: Solo renta
        c1 = db.query(Contrato).filter(Contrato.id_cliente == cliente1.id).first()
        if not c1:
            c1 = Contrato(
                id_cliente=cliente1.id,
                id_tipo_plan=tp_solo_renta.id,
                fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 12, 31),
                costo_renta_mensual=Decimal("1500.00"),
                modo_captura="contadores",
                observaciones="Contrato de prueba - Solo renta",
            )
            db.add(c1)
            db.flush()
            
            db.add(ContratoEquipo(
                id_contrato=c1.id,
                id_equipo=eq_mono1.id,
                fecha_ingreso=date(2026, 1, 1),
                contador_inicial_mono=1000,
                contador_inicial_color=0,
                contador_actual_mono=1000,
                contador_actual_color=0,
                ubicacion="Oficina Matriz",
            ))
            eq_mono1.estado = "rentado"
            print(f"  ✅ Contrato 1 (solo_renta) con {eq_mono1.numero_serie}")
        
        # Contrato 2: Renta + click
        c2 = db.query(Contrato).filter(
            Contrato.id_cliente == cliente1.id,
            Contrato.id_tipo_plan == tp_renta_click.id,
        ).first()
        if not c2:
            c2 = Contrato(
                id_cliente=cliente1.id,
                id_tipo_plan=tp_renta_click.id,
                fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 12, 31),
                costo_renta_mensual=Decimal("2000.00"),
                costo_click_mono=Decimal("0.5000"),
                costo_click_color=Decimal("2.5000"),
                modo_captura="contadores",
                observaciones="Contrato de prueba - Renta + click",
            )
            db.add(c2)
            db.flush()
            
            db.add(ContratoEquipo(
                id_contrato=c2.id,
                id_equipo=eq_color1.id,
                fecha_ingreso=date(2026, 1, 1),
                contador_inicial_mono=500,
                contador_inicial_color=200,
                contador_actual_mono=500,
                contador_actual_color=200,
                ubicacion="Recepción",
            ))
            eq_color1.estado = "rentado"
            print(f"  ✅ Contrato 2 (renta_click) con {eq_color1.numero_serie}")
        
        # Contrato 3: Renta + bolsa
        c3 = db.query(Contrato).filter(
            Contrato.id_cliente == cliente2.id,
            Contrato.id_tipo_plan == tp_renta_bolsa.id,
        ).first()
        if not c3:
            c3 = Contrato(
                id_cliente=cliente2.id,
                id_tipo_plan=tp_renta_bolsa.id,
                fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 12, 31),
                costo_renta_mensual=Decimal("1800.00"),
                bolsa_mono=1000,
                bolsa_color=500,
                costo_excedente_mono=Decimal("0.7500"),
                costo_excedente_color=Decimal("3.0000"),
                modo_captura="contadores",
                observaciones="Contrato de prueba - Bolsa",
            )
            db.add(c3)
            db.flush()
            
            db.add(ContratoEquipo(
                id_contrato=c3.id,
                id_equipo=eq_mono2.id,
                fecha_ingreso=date(2026, 1, 1),
                contador_inicial_mono=0,
                contador_inicial_color=0,
                contador_actual_mono=0,
                contador_actual_color=0,
                ubicacion="Sucursal Sur",
            ))
            eq_mono2.estado = "rentado"
            print(f"  ✅ Contrato 3 (renta_bolsa) con {eq_mono2.numero_serie}")
        
        # Contrato 4: Costo diferenciado
        c4 = db.query(Contrato).filter(
            Contrato.id_cliente == cliente2.id,
            Contrato.id_tipo_plan == tp_diferenciado.id,
        ).first()
        if not c4:
            c4 = Contrato(
                id_cliente=cliente2.id,
                id_tipo_plan=tp_diferenciado.id,
                fecha_inicio=date(2026, 1, 1),
                fecha_fin=date(2026, 12, 31),
                costo_renta_mensual=Decimal("0.00"),
                costo_click_mono=Decimal("0.5000"),
                costo_click_color=Decimal("2.5000"),
                modo_captura="contadores",
                observaciones="Contrato de prueba - Costo diferenciado",
            )
            db.add(c4)
            db.flush()
            
            db.add(ContratoEquipo(
                id_contrato=c4.id,
                id_equipo=eq_color2.id,
                fecha_ingreso=date(2026, 1, 1),
                contador_inicial_mono=0,
                contador_inicial_color=0,
                contador_actual_mono=0,
                contador_actual_color=0,
                ubicacion="Oficina 2",
                costo_renta_equipo=Decimal("800.00"),
                costo_click_mono_equipo=Decimal("0.3000"),
                costo_click_color_equipo=Decimal("2.0000"),
            ))
            eq_color2.estado = "rentado"
            print(f"  ✅ Contrato 4 (costo_diferenciado) con {eq_color2.numero_serie}")
        
        db.commit()
        
        # ========== RESUMEN ==========
        print("")
        print("=" * 60)
        print("✅ SEED COMPLETADO")
        print("=" * 60)
        print("")
        print("📋 Resumen de datos creados:")
        print("")
        
        # Mostrar IDs generados
        print("👤 Usuarios:")
        for u in db.query(Usuario).all():
            print(f"   ID {u.id}: {u.username} ({u.rol})")
        
        print("")
        print("🏢 Clientes:")
        for c in db.query(Cliente).all():
            print(f"   ID {c.id}: {c.razon_social}")
        
        print("")
        print("📄 Contratos:")
        for c in db.query(Contrato).all():
            plan = db.query(TipoPlan).filter(TipoPlan.id == c.id_tipo_plan).first()
            print(f"   ID {c.id}: {plan.nombre} - Cliente {c.id_cliente}")
        
        print("")
        print("🖨️  Equipos:")
        for e in db.query(Equipo).all():
            print(f"   ID {e.id}: {e.numero_serie} - {e.estado}")
        
        print("")
        print("📦 Artículos:")
        for a in db.query(Articulo).all():
            print(f"   ID {a.id}: {a.codigo} - Stock: {a.stock_actual}")
        
        print("")
        print("=" * 60)
        print("🎉 ¡Listo para probar!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed()