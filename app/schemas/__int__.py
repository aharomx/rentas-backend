
from app.schemas.mantenimiento import (
    MantenimientoCreate, MantenimientoUpdate, MantenimientoResponse,
    MantenimientoResumenResponse,AutorizarMantenimientoRequest,
    IniciarMantenimientoRequest,CompletarMantenimientoRequest,
    CancelarMantenimientoRequest,EsperaRefaccionesRequest
)

from app.schemas.mantenimiento_equipo import (
    MantenimientoEquipoCreate, MantenimientoEquipoUpdate,
    MantenimientoEquipoResponse
)

from app.schemas.mantenimiento_refaccion import (
    MantenimientoRefaccionCreate, MantenimientoRefaccionUpdate,
    MantenimientoRefaccionResponse
)

from app.schemas.articulo import (
    ArticuloCreate,
    ArticuloUpdate,
    ArticuloResponse
)

from app.schemas.categoria_articulo import (
    CategoriaArticuloCreate, CategoriaArticuloUpdate,
    CategoriaArticuloResponse
)

from app.schemas.movimiento_almacen import (
    MovimientoAlmacenCreate, MovimientoAlmacenResponse,
    KardexItem, StockBajoItem, ResumenMovimientos
)

from app.schemas.solicitud_almacen import (
    SolicitudAlmacenCreate, SolcitudAlmacenUpdate, SolicitudAlmacenResponse,
    SolicitudAlmacenResumenResponse,
    AutorizarSolicitudRequest,
    EntregarSolicitudRequest,
    CompletarRecoleccionRequest,
    DevolucionPosteriorRequest,
    CancelarSolicitudRequest,
    ReporteDevolucionesItem, 
    ResumenDevoluciones
)

from app.schemas.solicitud_almacen_detalle import (
    SolicitudAlmacenDetalleCreate,
    SolicitudAlmacenDetalleUpdate,
    SolicitudAlmacenDetallResponse
)

from app.schemas.inventario_cliente import (
    InventarioClienteCreate,
    InventarioClienteUpdate,
    InventarioClienteResponse,
    ResumenInventarioCliente,
    TonerEnCliente
)