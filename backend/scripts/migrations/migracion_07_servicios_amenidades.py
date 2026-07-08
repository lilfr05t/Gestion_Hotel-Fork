import os
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '1234'),
    'database': os.getenv('DB_NAME', 'hotel_db'),
}


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


def column_exists(cursor, table_name, column_name):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (DB_CONFIG['database'], table_name, column_name),
    )
    return cursor.fetchone()[0] > 0


def index_exists(cursor, table_name, index_name):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND INDEX_NAME=%s",
        (DB_CONFIG['database'], table_name, index_name),
    )
    return cursor.fetchone()[0] > 0


def ensure_columns(cursor):
    if not column_exists(cursor, 'servicio', 'categoria'):
        cursor.execute("ALTER TABLE servicio ADD COLUMN categoria VARCHAR(50) NULL")
    if not column_exists(cursor, 'servicio', 'costo_proveedor'):
        cursor.execute("ALTER TABLE servicio ADD COLUMN costo_proveedor DECIMAL(10,2) NULL DEFAULT 0.00")

    if not column_exists(cursor, 'amenidad', 'categoria'):
        cursor.execute("ALTER TABLE amenidad ADD COLUMN categoria VARCHAR(50) NULL")
    if not column_exists(cursor, 'amenidad', 'estado'):
        cursor.execute("ALTER TABLE amenidad ADD COLUMN estado ENUM('activo','inactivo') NOT NULL DEFAULT 'activo'")
    if not column_exists(cursor, 'amenidad', 'descripcion'):
        cursor.execute("ALTER TABLE amenidad ADD COLUMN descripcion TEXT NULL")
    if column_exists(cursor, 'amenidad', 'costo_promedio'):
        cursor.execute("ALTER TABLE amenidad DROP COLUMN costo_promedio")

    if not index_exists(cursor, 'servicio', 'idx_servicio_categoria'):
        cursor.execute("CREATE INDEX idx_servicio_categoria ON servicio(categoria)")
    if not index_exists(cursor, 'servicio', 'idx_servicio_estado'):
        cursor.execute("CREATE INDEX idx_servicio_estado ON servicio(estado)")
    if not index_exists(cursor, 'amenidad', 'idx_amenidad_categoria'):
        cursor.execute("CREATE INDEX idx_amenidad_categoria ON amenidad(categoria)")
    if not index_exists(cursor, 'amenidad', 'idx_amenidad_estado'):
        cursor.execute("CREATE INDEX idx_amenidad_estado ON amenidad(estado)")


def upsert_servicio(cursor, nombre, tipo, precio_unitario, descripcion, categoria, costo_proveedor):
    cursor.execute("SELECT ID_Servicio FROM servicio WHERE nombre = %s LIMIT 1", (nombre,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE servicio
            SET tipo=%s, estado='activo', precio_unitario=%s, descripcion=%s, categoria=%s, costo_proveedor=%s
            WHERE ID_Servicio=%s
            """,
            (tipo, precio_unitario, descripcion, categoria, costo_proveedor, existing[0]),
        )
        return existing[0]

    cursor.execute(
        """
        INSERT INTO servicio (nombre, tipo, estado, precio_unitario, descripcion, categoria, costo_proveedor)
        VALUES (%s, %s, 'activo', %s, %s, %s, %s)
        """,
        (nombre, tipo, precio_unitario, descripcion, categoria, costo_proveedor),
    )
    return cursor.lastrowid


def upsert_amenidad(cursor, nombre, categoria, descripcion):
    cursor.execute("SELECT ID_Amenidad FROM amenidad WHERE nombre = %s LIMIT 1", (nombre,))
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE amenidad
            SET categoria=%s, estado='activo', descripcion=%s
            WHERE ID_Amenidad=%s
            """,
            (categoria, descripcion, existing[0]),
        )
        return existing[0]

    cursor.execute(
        """
        INSERT INTO amenidad (nombre, categoria, estado, descripcion)
        VALUES (%s, %s, 'activo', %s)
        """,
        (nombre, categoria, descripcion),
    )
    return cursor.lastrowid


def assign_amenities(cursor):
    premium_amenities = [
        'Smart TV 55" con streaming',
        'Cafetera de cápsulas premium',
        'Batas de baño premium',
        'Minibar premium',
        'Wi-Fi Premium',
    ]
    standard_amenities = [
        'Wi-Fi Gratuito',
        'Aire Acondicionado Inverter',
        'Caja Fuerte Digital',
        'Kit de baño orgánico',
        'Toallas premium',
    ]
    mixed_amenities = [
        'Smart TV 43"',
        'Cafetera de cápsulas',
        'Cama king size',
        'Secador de cabello',
    ]

    # Garantizar que todas las amenidades existan
    for name in premium_amenities + standard_amenities + mixed_amenities:
        upsert_amenidad(cursor, name, 'Hotel', 'Amenidad estándar o premium del catálogo')

    # Premium: Suite o pisos altos
    for amenidad_nombre in premium_amenities:
        cursor.execute(
            """
            INSERT INTO habitacion_amenidad (ID_Habitacion, ID_Amenidad)
            SELECT h.ID_Habitacion, a.ID_Amenidad
            FROM habitacion h
            JOIN amenidad a ON a.nombre = %s
            WHERE (h.tipo = 'Suite' OR h.piso >= 5)
              AND NOT EXISTS (
                  SELECT 1 FROM habitacion_amenidad ha
                  WHERE ha.ID_Habitacion = h.ID_Habitacion AND ha.ID_Amenidad = a.ID_Amenidad
              )
            """,
            (amenidad_nombre,),
        )

    # Estándar: habitaciones simples o dobles
    for amenidad_nombre in standard_amenities:
        cursor.execute(
            """
            INSERT INTO habitacion_amenidad (ID_Habitacion, ID_Amenidad)
            SELECT h.ID_Habitacion, a.ID_Amenidad
            FROM habitacion h
            JOIN amenidad a ON a.nombre = %s
            WHERE h.tipo IN ('Simple', 'Doble')
              AND NOT EXISTS (
                  SELECT 1 FROM habitacion_amenidad ha
                  WHERE ha.ID_Habitacion = h.ID_Habitacion AND ha.ID_Amenidad = a.ID_Amenidad
              )
            """,
            (amenidad_nombre,),
        )

    # Mixto: habitaciones Junior o tipo intermedio
    for amenidad_nombre in mixed_amenities:
        cursor.execute(
            """
            INSERT INTO habitacion_amenidad (ID_Habitacion, ID_Amenidad)
            SELECT h.ID_Habitacion, a.ID_Amenidad
            FROM habitacion h
            JOIN amenidad a ON a.nombre = %s
            WHERE h.tipo IN ('Junior', 'Doble')
              AND NOT EXISTS (
                  SELECT 1 FROM habitacion_amenidad ha
                  WHERE ha.ID_Habitacion = h.ID_Habitacion AND ha.ID_Amenidad = a.ID_Amenidad
              )
            """,
            (amenidad_nombre,),
        )


def verify_assignments(cursor):
    cursor.execute(
        """
        SELECT h.numero, h.tipo, h.piso, a.nombre AS amenidad
        FROM habitacion h
        JOIN habitacion_amenidad ha ON ha.ID_Habitacion = h.ID_Habitacion
        JOIN amenidad a ON a.ID_Amenidad = ha.ID_Amenidad
        ORDER BY h.numero, a.nombre
        LIMIT 80
        """
    )
    rows = cursor.fetchall()
    print(f"\nVerificación JOIN: {len(rows)} relaciones encontradas")
    for row in rows[:20]:
        print(f"- Hab {row[0]} | {row[1]} | piso {row[2]} | {row[3]}")

    cursor.execute(
        """
        SELECT COUNT(*) AS huérfanas
        FROM habitacion_amenidad ha
        LEFT JOIN habitacion h ON h.ID_Habitacion = ha.ID_Habitacion
        LEFT JOIN amenidad a ON a.ID_Amenidad = ha.ID_Amenidad
        WHERE h.ID_Habitacion IS NULL OR a.ID_Amenidad IS NULL
        """
    )
    orphan_count = cursor.fetchone()[0]
    print(f"Registros huérfanos en habitacion_amenidad: {orphan_count}")


def main():
    print('migracion_07_servicios_amenidades: Iniciando')
    conn = get_conn()
    cursor = conn.cursor()
    try:
        ensure_columns(cursor)

        servicios = [
            ('Spa Sunset', 'Bienestar', 120.00, 'Spa premium con masajes, sauna y rituales de relajación.', 'Bienestar', 55.00),
            ('Desayuno Buffet Ejecutivo', 'Alimentación', 25.00, 'Desayuno buffet premium con opciones internacionales.', 'Alimentación', 12.00),
            ('Lavandería Express', 'Limpieza', 15.00, 'Servicio de lavandería rápida en 24 horas.', 'Limpieza', 6.50),
            ('Transfer Aeropuerto', 'Transporte', 45.00, 'Traslado privado desde y hacia el aeropuerto.', 'Transporte', 22.00),
            ('Servicio de Habitaciones 24h', 'Alimentación', 18.00, 'Menú variado disponible las 24 horas.', 'Alimentación', 8.00),
            ('Masaje Relajante', 'Bienestar', 95.00, 'Sesión de masaje relajante para huéspedes.', 'Bienestar', 42.00),
            ('Tour City Tour', 'Turismo', 60.00, 'Excursión guiada por los puntos más representativos.', 'Turismo', 28.00),
            ('Parking Premium', 'Estacionamiento', 20.00, 'Espacio de estacionamiento reservado.', 'Estacionamiento', 9.00),
            ('Check-in Exprés', 'Recepción', 0.00, 'Atención prioritaria para registro rápido.', 'Recepción', 0.00),
            ('Café de la Tarde', 'Alimentación', 16.00, 'Servicio de café y postres en la habitación.', 'Alimentación', 7.50),
            ('Piscina Privada', 'Bienestar', 35.00, 'Acceso premium a la piscina del hotel.', 'Bienestar', 15.00),
            ('Concierge VIP', 'Atención', 30.00, 'Asistencia personalizada de concierge.', 'Atención', 14.00),
            ('Lavado de Prendas Premium', 'Limpieza', 22.00, 'Servicio premium de lavandería con planchado.', 'Limpieza', 10.00),
            ('Bar en Habitación', 'Alimentación', 28.00, 'Selección de bebidas y snacks en la habitación.', 'Alimentación', 11.00),
            ('Asistente Personal de Habitación', 'Atención', 40.00, 'Asistencia personalizada para solicitudes especiales.', 'Atención', 19.00),
        ]

        for servicio in servicios:
            upsert_servicio(cursor, *servicio)

        amenidades = [
            ('Wi-Fi Gratuito', 'Conectividad', 'Conexión estable para trabajo y entretenimiento.'),
            ('Wi-Fi Premium', 'Conectividad', 'Alta velocidad para videollamadas y streaming.'),
            ('Aire Acondicionado Inverter', 'Climatización', 'Sistema silencioso y eficiente en energía.'),
            ('Smart TV 43"', 'Entretenimiento', 'Pantalla Full HD con apps de streaming.'),
            ('Smart TV 55" con streaming', 'Entretenimiento', 'Pantalla premium con streaming y contenido 4K.'),
            ('Caja Fuerte Digital', 'Seguridad', 'Cofre digital con acceso seguro.'),
            ('Kit de baño orgánico', 'Baño', 'Productos certificados orgánicos para huéspedes.'),
            ('Toallas premium', 'Baño', 'Toallas suaves y de alta absorción.'),
            ('Cafetera de cápsulas', 'Cocina', 'Cafetera compacta para una experiencia premium.'),
            ('Cafetera de cápsulas premium', 'Cocina', 'Cafetera premium con variedad de cápsulas.'),
            ('Batas de baño premium', 'Baño', 'Batas de baño de algodón premium.'),
            ('Minibar premium', 'Cocina', 'Mini bar de bebidas premium y snacks.'),
            ('Cama king size', 'Dormitorio', 'Cama king size con colchón premium.'),
            ('Secador de cabello', 'Baño', 'Secador de cabello profesional.'),
        ]

        for amenidad in amenidades:
            upsert_amenidad(cursor, *amenidad)

        cursor.execute("SELECT ID_Amenidad FROM amenidad WHERE nombre = %s", ('Escritorio de trabajo',))
        escritorio = cursor.fetchone()
        if escritorio:
            cursor.execute("DELETE FROM habitacion_amenidad WHERE ID_Amenidad = %s", (escritorio[0],))
            cursor.execute("DELETE FROM amenidad WHERE ID_Amenidad = %s", (escritorio[0],))

        assign_amenities(cursor)
        verify_assignments(cursor)

        conn.commit()
        print('migracion_07_servicios_amenidades: Completada')
    except Exception as e:
        conn.rollback()
        print('migracion_07_servicios_amenidades: ERROR:', e)
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
