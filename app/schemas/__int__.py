
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