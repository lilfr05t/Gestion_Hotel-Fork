from app.core.database import SessionLocal
from app.models import Reserva, Recepcionista, Usuario

with SessionLocal() as db:
    r = db.query(Reserva).filter(Reserva.ID_Reserva == 1014).first()
    if not r:
        print('Reserva 1014 no encontrada')
    else:
        print('Reserva', r.ID_Reserva, 'DNI', r.DNI, 'Habitacion', r.ID_Habitacion, 'estado', r.estado, 'ID_Recepcionista', r.ID_Recepcionista)
        rec = db.query(Recepcionista).filter(Recepcionista.ID_Usuario == r.ID_Recepcionista).first()
        if rec:
            user = db.query(Usuario).filter(Usuario.ID_Usuario == rec.ID_Usuario).first()
            print('Recepcionista -> Usuario id', rec.ID_Usuario, 'rol', user.rol if user else None)
        else:
            user = db.query(Usuario).filter(Usuario.ID_Usuario == r.ID_Recepcionista).first()
            print('Usuario directo', user.ID_Usuario if user else None, 'rol', user.rol if user else None)
