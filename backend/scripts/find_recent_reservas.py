import os
import sys
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.database import SessionLocal
from app.models import Reserva, Habitacion

if __name__ == '__main__':
    db = SessionLocal()
    try:
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        print('Searching reservas with fecha_entrada between', yesterday, 'and', tomorrow)
        rows = db.query(Reserva).filter(Reserva.fecha_entrada >= yesterday, Reserva.fecha_entrada <= tomorrow).order_by(Reserva.fecha_entrada.desc()).all()
        print(f'Found {len(rows)} reservas matching date range')
        for r in rows:
            print(r.ID_Reserva, r.DNI, r.ID_Habitacion, r.fecha_entrada, r.fecha_salida, r.estado)

        print('\nRooms currently ocupada:')
        occ = db.query(Habitacion).filter(Habitacion.estado == 'ocupada').all()
        for h in occ:
            print(h.ID_Habitacion, h.numero, h.tipo)
    finally:
        db.close()
