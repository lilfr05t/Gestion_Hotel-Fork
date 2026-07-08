from datetime import date
from app.core.database import SessionLocal
from app.models import Reserva

with SessionLocal() as db:
    today = date.today()
    reservas = db.query(Reserva).filter(Reserva.fecha_entrada >= today).order_by(Reserva.ID_Reserva.desc()).all()
    print('today', today)
    for r in reservas:
        print(r.ID_Reserva, r.DNI, r.ID_Habitacion, r.estado, r.fecha_entrada)
