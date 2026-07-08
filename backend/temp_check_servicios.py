from app.core.database import SessionLocal
import app.models as models

with SessionLocal() as db:
    try:
        servicios = db.query(models.Servicio).filter(models.Servicio.estado == 'activo').all()
        print('Servicios encontrados:', len(servicios))
        for s in servicios:
            print(s.ID_Servicio, s.nombre, s.precio_unitario, s.costo_proveedor)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print('ERROR', e)
