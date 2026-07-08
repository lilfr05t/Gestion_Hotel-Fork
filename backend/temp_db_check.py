from app.core.database import SessionLocal
from app.models import Huesped, Reserva, Habitacion

with SessionLocal() as db:
    dni = '72084431'
    huesped = db.query(Huesped).filter(Huesped.DNI == dni).first()
    print('HUESPED', bool(huesped), repr(huesped.nombre if huesped else None), repr(huesped.apellido if huesped else None), repr(huesped.correo if huesped else None), repr(huesped.telefono if huesped else None), repr(huesped.estado if huesped else None))
    reservas = db.query(Reserva).filter(Reserva.DNI == dni).all()
    print('RESERVAS', len(reservas))
    for r in reservas:
        print('  RES', r.ID_Reserva, r.ID_Habitacion, r.estado, r.fecha_entrada, r.fecha_salida)
    ocupadas = db.query(Habitacion).filter(Habitacion.estado == 'ocupada').count()
    print('HAB OCUPADAS', ocupadas)
