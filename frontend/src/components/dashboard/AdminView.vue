<template>
  <section class="panel">
    <h2 class="panel__title">Panel Administrativo</h2>

    <div class="metrics-grid">
      <div class="metric-card">
        <span class="metric-card__label">Total Habitaciones</span>
        <span class="metric-card__value">{{ totalHabitaciones }}</span>
      </div>
      <div class="metric-card metric-card--success">
        <span class="metric-card__label">Disponibles</span>
        <span class="metric-card__value">{{ habitacionesDisponibles }}</span>
      </div>
      <div class="metric-card metric-card--navy">
        <span class="metric-card__label">Ocupadas</span>
        <span class="metric-card__value">{{ habitacionesOcupadas }}</span>
      </div>
      <div class="metric-card metric-card--warning">
        <span class="metric-card__label">Mantenimiento</span>
        <span class="metric-card__value">{{ habitacionesMantenimiento }}</span>
      </div>
    </div>

    <nav class="nav-pills">
      <button class="nav-pill" :class="{ 'is-active': currentAdminView === 'monitor' }" type="button" @click="$emit('show-monitor')">Monitor de Habitaciones</button>
      <button class="nav-pill" :class="{ 'is-active': currentAdminView === 'config' }" type="button" @click="$emit('show-config')">Configuración del Sistema</button>
      <button class="nav-pill" :class="{ 'is-active': currentAdminView === 'pagos' }" type="button" @click="$emit('show-pagos')">Auditoría de Pagos</button>
      <button class="nav-pill" :class="{ 'is-active': currentAdminView === 'empleados' }" type="button" @click="$emit('show-empleados')">Gestión de Empleados</button>
    </nav>

    <div v-if="currentAdminView === 'monitor'" class="card">
      <h3 class="card__title">Monitor de Habitaciones</h3>
      <ul class="room-list">
        <li v-for="room in rooms" :key="room.ID_Habitacion" class="room-row">
          <div class="room-row__info">
            <strong>Hab {{ room.numero }}</strong>
            <span class="room-row__meta">Tipo: {{ room.tipo || 'N/A' }} · Precio: {{ room.precio_noche || '-' }}</span>
            <span v-if="room.amenidades && room.amenidades.length" class="room-row__meta">
              Amenidades: {{ room.amenidades.join(', ') }}
            </span>
          </div>
          <span class="status-badge" :class="`status-badge--${room.estado}`">
            <span class="status-badge__dot"></span>{{ room.estado }}
          </span>
        </li>
      </ul>
    </div>

    <div v-else-if="currentAdminView === 'config'" class="card">
      <h3 class="card__title">Configuración del Sistema</h3>
      <form class="form-grid" @submit.prevent="$emit('save-config')">
        <div class="form-group">
          <label for="hotel-name">Nombre del Hotel</label>
          <input id="hotel-name" type="text" v-model="config.nombre_hotel" />
        </div>
        <div class="form-group">
          <label for="checkin-time">Hora de Check-in</label>
          <input id="checkin-time" type="text" v-model="config.hora_checkin" />
        </div>
        <div class="form-group">
          <label for="checkout-time">Hora de Check-out</label>
          <input id="checkout-time" type="text" v-model="config.hora_checkout" />
        </div>
        <button class="btn-gold form-grid__submit" type="submit">Guardar Cambios</button>
      </form>
    </div>

    <div v-else-if="currentAdminView === 'pagos'" class="card">
      <h3 class="card__title">Auditoría de Pagos</h3>
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Habitación</th>
            <th>Monto</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pago in pagos" :key="pago.ID_Boleta">
            <td>{{ pago.ID_Boleta }}</td>
            <td>{{ pago.numero_habitacion }}</td>
            <td>{{ pago.monto }}</td>
            <td>{{ pago.estado }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else-if="currentAdminView === 'empleados'" class="card">
      <h3 class="card__title">Gestión de Empleados</h3>
      <table class="table">
        <thead>
          <tr>
            <th>Nombre</th>
            <th>Correo</th>
            <th>Rol</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="empleado in empleados" :key="empleado.id || empleado.ID || empleado.ID_Usuario">
            <td>{{ empleado.nombre || empleado.name || empleado.full_name || 'N/A' }}</td>
            <td>{{ empleado.correo || empleado.email || empleado.email_address || 'N/A' }}</td>
            <td>{{ empleado.rol || empleado.role || empleado.user_type || 'N/A' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<script setup>
defineProps({
  rooms: Array,
  empleados: Array,
  pagos: Array,
  config: Object,
  currentAdminView: String,
  totalHabitaciones: Number,
  habitacionesDisponibles: Number,
  habitacionesOcupadas: Number,
  habitacionesMantenimiento: Number,
})

defineEmits(['show-monitor', 'show-config', 'show-pagos', 'show-empleados', 'save-config'])
</script>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 1.25rem; }
.panel__title { font-family: var(--font-display); font-size: 1.5rem; color: var(--navy); }
.card {
  background: var(--white);
  border: 1px solid var(--cream-dark);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: 1.5rem;
}
.card__title { font-size: 1.1rem; margin-bottom: 1rem; color: var(--navy); }
.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; }
.metric-card {
  background: var(--white);
  border: 1px solid var(--cream-dark);
  border-left: 4px solid var(--slate);
  border-radius: var(--radius-md);
  padding: 1rem 1.25rem;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}
.metric-card--success { border-left-color: var(--success); }
.metric-card--navy { border-left-color: var(--navy); }
.metric-card--warning { border-left-color: var(--warning); }
.metric-card__label { font-size: 0.78rem; color: var(--slate); text-transform: uppercase; letter-spacing: 0.04em; }
.metric-card__value { font-family: var(--font-display); font-size: 1.9rem; color: var(--navy); }
.nav-pills { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.nav-pill {
  background: var(--white);
  border: 1px solid var(--cream-dark);
  color: var(--navy-mid);
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.85rem;
  font-weight: 600;
  transition: all 0.15s ease;
}
.nav-pill:hover { border-color: var(--gold); color: var(--navy); }
.nav-pill.is-active {
  background: var(--navy);
  border-color: var(--navy);
  color: var(--white);
}
.room-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; }
.room-row {
  display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 0; border-bottom: 1px solid var(--cream-dark);
}
.room-row:last-child { border-bottom: none; }
.room-row__info { display: flex; flex-direction: column; gap: 0.2rem; }
.room-row__meta { color: var(--slate); font-size: 0.82rem; }
.status-badge {
  display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.7rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; text-transform: capitalize; background: var(--cream); color: var(--navy-mid);
}
.status-badge__dot { width: 7px; height: 7px; border-radius: 50%; background: var(--slate); }
.status-badge--disponible { background: rgba(62, 158, 111, 0.12); color: var(--success); }
.status-badge--disponible .status-badge__dot { background: var(--success); }
.status-badge--ocupada { background: rgba(30, 58, 95, 0.10); color: var(--navy-mid); }
.status-badge--ocupada .status-badge__dot { background: var(--navy-mid); }
.status-badge--mantenimiento, .status-badge--sucia { background: rgba(232, 150, 58, 0.14); color: var(--warning); }
.status-badge--mantenimiento .status-badge__dot, .status-badge--sucia .status-badge__dot { background: var(--warning); }
.form-grid { display: grid; gap: 1rem; }
.form-grid__submit { justify-self: flex-start; }
.form-group { display: flex; flex-direction: column; gap: 0.35rem; }
.form-group label { font-size: 0.9rem; font-weight: 600; color: var(--navy-mid); }
.form-group input, .form-group select, .form-group textarea { border: 1px solid var(--cream-dark); border-radius: var(--radius-sm); padding: 0.65rem 0.8rem; font-family: inherit; font-size: 0.95rem; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: var(--navy); box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1); }
.btn-gold { background: var(--gold); color: var(--navy); border: none; border-radius: var(--radius-sm); padding: 0.65rem 1.2rem; font-size: 0.9rem; font-weight: 600; cursor: pointer; }
.btn-gold:hover { background: var(--gold-dark); }
.table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.table th { background: var(--cream); color: var(--navy-mid); font-weight: 600; padding: 0.8rem; text-align: left; border-bottom: 2px solid var(--cream-dark); }
.table td { padding: 0.75rem 0.8rem; border-bottom: 1px solid var(--cream-dark); }
.table tbody tr:hover { background: rgba(255,255,255,0.5); }
</style>
