import os
import sys
from sqlalchemy import or_

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.database import SessionLocal
from app import models

if __name__ == '__main__':
    db = SessionLocal()
    try:
        q = (
            db.query(models.Reserva, models.Habitacion)
            .join(models.Habitacion, models.Reserva.ID_Habitacion == models.Habitacion.ID_Habitacion)
            .filter(or_(models.Reserva.estado == 'activa', models.Habitacion.estado == 'ocupada'))
        )
        rows = q.all()
        print('matched rows count:', len(rows))
        for reserva, habit in rows:
            print('RES', reserva.ID_Reserva, reserva.estado, 'HAB', habit.ID_Habitacion, habit.estado)

        # Also show reservation with ID 1014 explicitly
        r = db.query(models.Reserva).filter(models.Reserva.ID_Reserva == 1014).first()
        if r:
            h = r.habitacion
            print('\nExplicit Reserva 1014:', r.ID_Reserva, r.estado, 'ID_Habitacion', r.ID_Habitacion, 'habitacion_estado', h.estado if h else None)
        else:
            print('\nReserva 1014 not found')
    finally:
        db.close()
