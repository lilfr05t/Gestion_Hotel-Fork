from app.core.database import SessionLocal
from app.models import Reserva, Habitacion

with SessionLocal() as db:
    active_reservas = db.query(Reserva).filter(Reserva.estado == 'activa').count()
    occupied_rooms = db.query(Habitacion).filter(Habitacion.estado == 'ocupada').count()
    reservas_by_room = db.query(Reserva).join(Habitacion, Reserva.ID_Habitacion == Habitacion.ID_Habitacion).filter(Habitacion.estado == 'ocupada').count()
    total_reservas = db.query(Reserva).count()
    print('active_reservas', active_reservas)
    print('occupied_rooms', occupied_rooms)
    print('reservas_by_room', reservas_by_room)
    print('total_reservas', total_reservas)
    if active_reservas > 0:
        sample = db.query(Reserva).filter(Reserva.estado == 'activa').limit(10).all()
        print('active_sample', [(r.ID_Reserva, r.DNI, r.ID_Habitacion, r.estado) for r in sample])
    if occupied_rooms > 0:
        sample2 = db.query(Reserva).join(Habitacion, Reserva.ID_Habitacion == Habitacion.ID_Habitacion).filter(Habitacion.estado == 'ocupada').limit(10).all()
        print('occupancy_sample', [(r.ID_Reserva, r.DNI, r.ID_Habitacion, r.estado, r.habitacion.estado if r.habitacion else None) for r in sample2])
