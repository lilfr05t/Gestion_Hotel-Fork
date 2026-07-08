import os
import random
from datetime import datetime, timedelta

import mysql.connector
import numpy as np
import pandas as pd

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'database': os.getenv('DB_NAME', 'hotel_db'),
}

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def clean_tables(cursor):
    print('Limpiando datos previos en orden seguro...')
    cursor.execute('DELETE FROM boleta')
    cursor.execute('DELETE FROM consumo')
    cursor.execute('DELETE FROM nota_servicio')
    cursor.execute('DELETE FROM asignacion_parking')
    cursor.execute('DELETE FROM parking')
    cursor.execute('DELETE FROM reserva')
    cursor.execute('DELETE FROM habitacion_amenidad')
    cursor.execute('DELETE FROM recepcionista')
    cursor.execute('DELETE FROM usuario')
    cursor.execute('DELETE FROM huesped')


def ensure_recepcionistas(cursor, count=8):
    print(f'Creando {count} usuarios recepcionistas...')
    users = []
    for idx in range(1, count + 1):
        users.append((
            f'Recepcionista {idx}',
            f'recepcionista{idx}@hotelbayes.pe',
            'recepcionista',
            'activo',
            f'$2b$12$stubhash{idx}',
        ))

    cursor.executemany(
        """
        INSERT INTO usuario (nombre, correo, rol, activo, password_hash)
        VALUES (%s, %s, %s, %s, %s)
        """,
        users,
    )
    cursor.execute('SELECT ID_Usuario FROM usuario WHERE rol = "recepcionista" ORDER BY ID_Usuario')
    ids = [row[0] for row in cursor.fetchall()]

    cursor.executemany(
        "INSERT INTO recepcionista (ID_Usuario) VALUES (%s)",
        [(uid,) for uid in ids],
    )
    return ids


def generate_guest_dataframe(count=1000):
    print('Generando DataFrame de huéspedes...')
    names = [
        'Carlos', 'Ana', 'Luis', 'María', 'Jorge', 'Sofía', 'Miguel', 'Andrea', 'Renzo', 'Clara',
        'Diego', 'Lucía', 'Rafael', 'Paula', 'José', 'Valeria', 'Eduardo', 'Camila', 'Marco', 'Diana',
        'Pablo', 'Rosa', 'Alejandro', 'Fernanda', 'Sebastián', 'Nadia', 'Giancarlo', 'Mireya', 'Christian', 'Martha',
        'Matías', 'Patricia', 'Javier', 'Elena', 'Daniel', 'Mónica', 'Bruno', 'Cecilia', 'Álvaro', 'Natalia',
        'Ricardo', 'Rosario', 'Gustavo', 'Luciana', 'Emilio', 'Tatiana', 'Felipe', 'Angela', 'Tomás', 'Marina',
    ]
    last_names = [
        'Pérez', 'García', 'López', 'Torres', 'Ruiz', 'Sánchez', 'Mendoza', 'Flores', 'Silva', 'Ramos',
        'Castro', 'Vargas', 'Rojas', 'Quispe', 'Salazar', 'Cárdenas', 'Huamán', 'Aguirre', 'Ojeda', 'Mamani',
        'Díaz', 'Paredes', 'Tello', 'Cabrera', 'Ibarra', 'Núñez', 'Yupanqui', 'Chávez', 'Bellido', 'Mena',
        'Maldonado', 'Velarde', 'Arias', 'Candela', 'Herrera', 'Cortez', 'Delgado', 'Aponte', 'Marín', 'Suárez',
        'Navarro', 'Ortega', 'Gonzales', 'Benites', 'Zapata', 'Vega', 'Ponce', 'Soto', 'Baquerizo', 'Guzmán',
    ]
    regions = ['Lima', 'Arequipa', 'Cusco', 'Trujillo', 'Ica', 'Piura', 'Tacna', 'Puno', 'Huancayo', 'Loreto']
    countries = ['Perú', 'EE.UU.', 'España', 'Chile', 'Argentina', 'Colombia', 'México', 'Canadá', 'Francia', 'Italia']

    data = []
    for i in range(count):
        is_international = np.random.choice([False, True], p=[0.7, 0.3])
        if is_international:
            region = np.random.choice(countries)
            origin_type = np.random.choice(['internacional_turista', 'internacional_negocio'], p=[0.6, 0.4])
        else:
            region = np.random.choice(regions)
            origin_type = np.random.choice(['nacional_turista', 'nacional_corporativo', 'nacional_familiar'], p=[0.4, 0.35, 0.25])

        dni = str(70000000 + i)
        name = random.choice(names)
        last_name = random.choice(last_names)
        email = f"{name.lower()}{last_name.lower()}{i}@mailhotel.pe"
        phone = f"9{random.randint(10000000, 99999999)}"
        data.append({
            'DNI': dni,
            'nombre': name,
            'apellido': last_name,
            'correo': email,
            'telefono': phone,
            'estado': 'activo',
            'procedencia': region,
            'segmento': origin_type,
        })

    return pd.DataFrame(data)


def generate_reservations_dataframe(guests_df, room_rows, recepcionista_ids, count=1000):
    print('Generando reservas correlacionadas...')
    room_df = pd.DataFrame(room_rows, columns=['ID_Habitacion', 'tipo', 'piso', 'precio_noche'])
    rows = []

    start_date = datetime(2024, 1, 1)
    end_date = datetime(2025, 6, 30)
    date_range_days = (end_date - start_date).days

    for i in range(count):
        guest = guests_df.iloc[i]
        is_international = guest['procedencia'] in {'EE.UU.', 'España', 'Chile', 'Argentina', 'Colombia', 'México', 'Canadá', 'Francia', 'Italia'}
        is_corporate = guest['segmento'] == 'nacional_corporativo' or guest['segmento'] == 'internacional_negocio'
        stay_days = int(np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14], p=[0.08, 0.12, 0.15, 0.12, 0.15, 0.12, 0.1, 0.06, 0.05, 0.03, 0.02]))
        if is_corporate and not is_international:
            stay_days = max(stay_days, 5)
        if is_international and np.random.rand() < 0.55:
            stay_days = max(stay_days, 4)

        room = room_df.sample(1, replace=True).iloc[0]
        if guest['segmento'] in {'internacional_negocio', 'internacional_turista'} and str(room['tipo']).lower() in {'suite', 'junior'}:
            room = room_df[room_df['tipo'].str.lower() == 'suite'].sample(1).iloc[0] if not room_df[room_df['tipo'].str.lower() == 'suite'].empty else room
        if guest['segmento'] == 'nacional_corporativo' and np.random.rand() < 0.7:
            room = room_df[room_df['tipo'].str.lower() == 'doble'].sample(1).iloc[0] if not room_df[room_df['tipo'].str.lower() == 'doble'].empty else room

        entry_date = start_date + timedelta(days=int(np.random.randint(0, date_range_days)))
        exit_date = entry_date + timedelta(days=stay_days)

        estado = np.random.choice(['confirmada', 'finalizada', 'activa'], p=[0.55, 0.3, 0.15])
        precio_total = round(float(room['precio_noche']) * stay_days + (30 if is_international else 10) + (20 if is_corporate else 0), 2)

        rows.append({
            'DNI': guest['DNI'],
            'ID_Habitacion': int(room['ID_Habitacion']),
            'ID_Recepcionista': int(np.random.choice(recepcionista_ids)),
            'fecha_entrada': entry_date,
            'fecha_salida': exit_date,
            'estado': estado,
            'numero_reserva': f'R{(i + 1):05d}',
            'precio_total': precio_total,
            'procedencia': guest['procedencia'],
            'segmento': guest['segmento'],
            'stay_days': stay_days,
            'fecha_creacion': entry_date,
            'fecha_actualizacion': entry_date,
        })

    return pd.DataFrame(rows)


def build_consumptions_dataframe(reservations_df, services_df):
    print('Generando consumos correlacionados...')
    rows = []
    services_df = services_df.copy()

    for _, reserva in reservations_df.iterrows():
        is_international = reserva['procedencia'] in {'EE.UU.', 'España', 'Chile', 'Argentina', 'Colombia', 'México', 'Canadá', 'Francia', 'Italia'}
        is_corporate = reserva['segmento'] in {'nacional_corporativo', 'internacional_negocio'}
        days = int(reserva['stay_days']) if 'stay_days' in reserva and reserva['stay_days'] is not None else 3
        premium_score = 0.0
        if is_international:
            premium_score += 0.55
        if is_corporate:
            premium_score += 0.3
        if days > 5:
            premium_score += 0.25
        if np.random.rand() < premium_score:
            primary_service = 'Spa Sunset' if is_international or premium_score > 0.7 else 'Desayuno Buffet Ejecutivo'
        elif is_corporate:
            primary_service = 'Lavandería Express' if days > 5 else 'Desayuno Buffet Ejecutivo'
        else:
            primary_service = 'Servicio de Habitaciones 24h' if np.random.rand() < 0.4 else 'Café de la Tarde'

        selected = [primary_service]
        if np.random.rand() < 0.35:
            if is_international or premium_score > 0.6:
                selected.append('Transfer Aeropuerto')
            else:
                selected.append('Lavandería Express')
        if np.random.rand() < 0.25:
            selected.append('Desayuno Buffet Ejecutivo')

        for service_name in selected:
            service_row = services_df[services_df['nombre'] == service_name]
            if service_row.empty:
                continue
            service_row = service_row.iloc[0]
            rows.append({
                'ID_Reserva': int(reserva['ID_Reserva']),
                'ID_Servicio': int(service_row['ID_Servicio']),
                'cantidad': 1 if service_name != 'Lavandería Express' else 2,
                'fecha': reserva['fecha_entrada'] + timedelta(hours=4),
                'precio_unitario': float(service_row['precio_unitario']),
            })

    return pd.DataFrame(rows)


def ensure_amenities(cursor, room_rows):
    print('Asignando amenidades por tipo de habitación...')
    amenity_map = {
        'simple': [
            'Wi-Fi Gratuito',
            'Aire Acondicionado Inverter',
            'Caja Fuerte Digital',
            'Kit de baño orgánico',
            'Toallas premium',
        ],
        'doble': [
            'Wi-Fi Gratuito',
            'Aire Acondicionado Inverter',
            'Smart TV 43"',
            'Cafetera de cápsulas',
            'Cama king size',
            'Secador de cabello',
            'Kit de baño orgánico',
        ],
        'suite': [
            'Wi-Fi Premium',
            'Smart TV 55" con streaming',
            'Cafetera de cápsulas premium',
            'Batas de baño premium',
            'Minibar premium',
            'Caja Fuerte Digital',
        ],
        'junior': [
            'Wi-Fi Premium',
            'Smart TV 43"',
            'Cafetera de cápsulas',
            'Caja Fuerte Digital',
            'Secador de cabello',
            'Kit de baño orgánico',
        ],
    }

    for room in room_rows:
        room_type = str(room['tipo']).strip().lower()
        chosen_names = amenity_map.get(room_type, amenity_map['doble'])
        if room.get('piso') is not None and int(room['piso']) >= 5 and room_type != 'suite':
            chosen_names = amenity_map['suite']
        for amenity_name in chosen_names:
            cursor.execute('SELECT ID_Amenidad FROM amenidad WHERE nombre = %s LIMIT 1', (amenity_name,))
            amenity_row = cursor.fetchone()
            if not amenity_row:
                continue
            cursor.execute(
                'INSERT IGNORE INTO habitacion_amenidad (ID_Habitacion, ID_Amenidad) VALUES (%s, %s)',
                (room['ID_Habitacion'], amenity_row[0]),
            )


def insert_guest_frame(cursor, guests_df):
    values = [tuple(row) for row in guests_df[['DNI', 'nombre', 'apellido', 'correo', 'telefono', 'estado']].itertuples(index=False, name=None)]
    cursor.executemany(
        'INSERT INTO huesped (DNI, nombre, apellido, correo, telefono, estado) VALUES (%s, %s, %s, %s, %s, %s)',
        values,
    )


def insert_reservation_frame(cursor, reservations_df):
    values = [(
        row['DNI'],
        int(row['ID_Habitacion']),
        int(row['ID_Recepcionista']),
        row['fecha_entrada'],
        row['fecha_salida'],
        row['estado'],
        row['numero_reserva'],
        float(row['precio_total']),
        row['fecha_creacion'],
        row['fecha_actualizacion'],
    ) for _, row in reservations_df.iterrows()]
    cursor.executemany(
        """
        INSERT INTO reserva (
            DNI, ID_Habitacion, ID_Recepcionista, fecha_entrada, fecha_salida, estado,
            numero_reserva, precio_total, fecha_creacion, fecha_actualizacion
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        values,
    )


def insert_consumption_frame(cursor, consumptions_df):
    if consumptions_df.empty:
        return
    values = [(
        int(row['ID_Reserva']),
        int(row['ID_Servicio']),
        int(row['cantidad']),
        row['fecha'],
        float(row['precio_unitario']),
    ) for _, row in consumptions_df.iterrows()]
    cursor.executemany(
        'INSERT INTO consumo (ID_Reserva, ID_Servicio, cantidad, fecha, precio_unitario) VALUES (%s, %s, %s, %s, %s)',
        values,
    )


def main():
    print('seed_bayesian_data: iniciando')
    conn = get_conn()
    cursor = conn.cursor()
    try:
        clean_tables(cursor)

        recepcionista_ids = ensure_recepcionistas(cursor, count=8)

        cursor.execute('SELECT ID_Habitacion, tipo, piso, precio_noche FROM habitacion ORDER BY ID_Habitacion')
        room_rows = [dict(zip(['ID_Habitacion', 'tipo', 'piso', 'precio_noche'], row)) for row in cursor.fetchall()]
        if not room_rows:
            raise RuntimeError('No hay habitaciones disponibles para asignar al mock data.')

        cursor.execute('SELECT ID_Servicio, nombre, precio_unitario FROM servicio WHERE estado = "activo"')
        services_rows = [dict(zip(['ID_Servicio', 'nombre', 'precio_unitario'], row)) for row in cursor.fetchall()]
        services_df = pd.DataFrame(services_rows)

        guests_df = generate_guest_dataframe(count=1000)
        insert_guest_frame(cursor, guests_df)

        reservations_df = generate_reservations_dataframe(guests_df, room_rows, recepcionista_ids, count=1000)
        insert_reservation_frame(cursor, reservations_df)

        cursor.execute('SELECT ID_Reserva FROM reserva ORDER BY ID_Reserva')
        reservation_ids = [row[0] for row in cursor.fetchall()]
        reservations_df['ID_Reserva'] = reservation_ids
        consumptions_df = build_consumptions_dataframe(reservations_df, services_df)
        insert_consumption_frame(cursor, consumptions_df)

        ensure_amenities(cursor, room_rows)

        conn.commit()
        print('seed_bayesian_data: completado')
        print(f'Guías: {len(guests_df)} huéspedes, {len(reservations_df)} reservas, {len(consumptions_df)} consumos')
        cursor.execute('SELECT COUNT(*) FROM huesped')
        print('huespedes insertados:', cursor.fetchone()[0])
        cursor.execute('SELECT COUNT(*) FROM reserva')
        print('reservas insertadas:', cursor.fetchone()[0])
        cursor.execute('SELECT COUNT(*) FROM consumo')
        print('consumos insertados:', cursor.fetchone()[0])
    except Exception as e:
        conn.rollback()
        print('seed_bayesian_data: ERROR:', e)
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
