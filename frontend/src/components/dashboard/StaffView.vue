<template>
  <section class="panel">
    <h2 class="panel__title">Personal de Limpieza</h2>
    <p class="info-text">Nota: Las habitaciones pasan a estado 'Sucia' automáticamente tras cada Check-out.</p>

    <nav class="tabs">
      <button :class="['tab-btn', limpiezaTab === 'pending' ? 'is-active' : '']" @click="$emit('set-tab', 'pending')">Habitaciones por Atender</button>
      <button :class="['tab-btn', limpiezaTab === 'all' ? 'is-active' : '']" @click="$emit('set-tab', 'all')">Todas las Habitaciones</button>
    </nav>

    <div class="card" v-if="limpiezaTab === 'pending'">
      <h3 class="card__title">Habitaciones por Atender</h3>
      <ul class="room-list">
        <li v-for="room in pendingRooms" :key="room.ID_Habitacion" class="room-row">
          <div class="room-row__info">
            <strong>Hab {{ room.numero }}</strong>
            <span class="status-badge" :class="`status-badge--${room.estado}`">
              <span class="status-badge__dot"></span>{{ room.estado }}
            </span>
          </div>
          <button class="btn-gold btn-sm" @click="$emit('mark-clean', room)">Marcar como Limpia/Lista</button>
        </li>
      </ul>
    </div>

    <div class="card" v-else>
      <h3 class="card__title">Todas las Habitaciones</h3>
      <ul class="room-list">
        <li v-for="room in rooms" :key="room.ID_Habitacion" class="room-row">
          <div class="room-row__info">
            <strong>Hab {{ room.numero }}</strong>
            <span class="room-row__meta">Tipo: {{ room.tipo || 'N/A' }} · Precio: {{ room.precio_noche || '-' }}</span>
            <span v-if="room.amenidades && room.amenidades.length" class="room-row__meta">Amenidades: {{ room.amenidades.join(', ') }}</span>
          </div>
          <div class="room-row__actions">
            <span class="status-badge" :class="`status-badge--${room.estado}`">
              <span class="status-badge__dot"></span>{{ room.estado }}
            </span>
            <button class="btn-gold btn-sm" @click="$emit('mark-clean', room)" v-if="['sucia', 'mantenimiento'].includes(String(room.estado || '').toLowerCase())">Marcar como Limpia/Lista</button>
            <button class="btn-ghost btn-sm" @click="$emit('report-dirty', room)" v-if="String(room.estado || '').toLowerCase() !== 'sucia'">Reportar como Sucia</button>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
defineProps({
  rooms: Array,
  pendingRooms: Array,
  limpiezaTab: String,
})

defineEmits(['set-tab', 'mark-clean', 'report-dirty'])
</script>

<style scoped>
.panel { display: flex; flex-direction: column; gap: 1.25rem; }
.panel__title { font-family: var(--font-display); font-size: 1.5rem; color: var(--navy); }
.info-text { color: var(--slate); font-size: 0.9rem; margin-bottom: 1rem; }
.tabs { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.tab-btn {
  background: var(--white); border: 1px solid var(--cream-dark); color: var(--navy-mid); padding: 0.5rem 1rem; border-radius: 999px; font-size: 0.85rem; font-weight: 600;
}
.tab-btn.is-active { background: var(--navy); border-color: var(--navy); color: var(--white); }
.card {
  background: var(--white); border: 1px solid var(--cream-dark); border-radius: var(--radius-md); box-shadow: var(--shadow-sm); padding: 1.5rem;
}
.card__title { font-size: 1.1rem; margin-bottom: 1rem; color: var(--navy); }
.room-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; }
.room-row { display: flex; justify-content: space-between; align-items: center; padding: 0.85rem 0; border-bottom: 1px solid var(--cream-dark); }
.room-row:last-child { border-bottom: none; }
.room-row__info { display: flex; flex-direction: column; gap: 0.2rem; }
.room-row__meta { color: var(--slate); font-size: 0.82rem; }
.room-row__actions { display: flex; gap: 0.6rem; align-items: center; }
.status-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.7rem; border-radius: 999px; font-size: 0.78rem; font-weight: 600; text-transform: capitalize; background: var(--cream); color: var(--navy-mid); }
.status-badge__dot { width: 7px; height: 7px; border-radius: 50%; background: var(--slate); }
.status-badge--disponible { background: rgba(62, 158, 111, 0.12); color: var(--success); }
.status-badge--disponible .status-badge__dot { background: var(--success); }
.status-badge--mantenimiento, .status-badge--sucia { background: rgba(232, 150, 58, 0.14); color: var(--warning); }
.status-badge--mantenimiento .status-badge__dot, .status-badge--sucia .status-badge__dot { background: var(--warning); }
.btn-gold, .btn-ghost, .btn-sm { border: none; border-radius: var(--radius-sm); padding: 0.65rem 1.2rem; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.15s ease; }
.btn-gold { background: var(--gold); color: var(--navy); }
.btn-gold:hover { background: var(--gold-dark); }
.btn-ghost { background: var(--cream); color: var(--navy-mid); border: 1px solid var(--cream-dark); }
.btn-ghost:hover { background: var(--white); }
.btn-sm { padding: 0.4rem 0.8rem; font-size: 0.8rem; }
</style>
