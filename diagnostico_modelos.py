import sys
sys.path.insert(0, ".")

print("📦 Importando modelos...")
try:
    from app.models import (
        Cliente, DireccionCliente, ContactoCliente,
        ModeloImpresora, Equipo,
        TipoPlan, Contrato, ContratoEquipo, MovimientoEquipo,
        LecturaContador, OrdenLectura,
        Usuario, AuditoriaAcceso,
        CategoriaArticulo, Articulo, MovimientoAlmacen,
        Mantenimiento, MantenimientoEquipo, MantenimientoRefaccion,
        SolicitudAlmacen, SolicitudAlmacenDetalle, InventarioCliente,
        DocumentoCobro, DetalleCobroEquipo, DetalleCobroBolsa,
    )
    print("✅ Todos los modelos importados")
except Exception as e:
    print(f"❌ Error importando: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("")
print("📋 Tablas registradas:")
from app.database import Base
for tabla in sorted(Base.metadata.tables.keys()):
    print(f"  - {tabla}")

print("")
print(f"📊 Total: {len(Base.metadata.tables)} tablas")

# Verificar específicamente las problemáticas
print("")
print("🔍 Verificando tablas clave:")
for tabla in ["contrato_equipos", "documentos_cobro", "detalle_cobro_equipos", "detalle_cobro_bolsas"]:
    if tabla in Base.metadata.tables:
        print(f"  ✅ {tabla}")
    else:
        print(f"  ❌ {tabla} NO ENCONTRADA")