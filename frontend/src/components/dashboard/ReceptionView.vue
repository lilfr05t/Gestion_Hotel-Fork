<template>
  <section class="panel">
    <h2 class="panel__title">Centro de Control Operativo</h2>

    <div class="card card--accent">
      <h3 class="card__title card__title--accent">Registro de Nuevo Huésped (Check-In Presencial)</h3>

      <div v-if="generatedAccessCode" class="success-banner">
        <h4 class="success-banner__title">¡Registro exitoso!</h4>
        <p class="success-banner__text">Código de acceso para el huésped:</p>
        <strong class="success-banner__code">{{ generatedAccessCode }}</strong>
        <button class="btn-gold success-banner__dismiss" @click="$emit('clear-code')">Entendido</button>
      </div>

      <form class="checkin-form" @submit.prevent="$emit('submit-checkin')">
        <div class="form-group">
          <label>DNI / Documento de Identidad <span class="required">*</span></label>
          <input type="text" v-model="checkinForm.dni" required placeholder="Ej: 12345678" />
        </div>

        <div class="form-group">
          <label>Nombre Completo del Huésped <span class="required">*</span></label>
          <input type="text" v-model="checkinForm.nombreCompleto" required placeholder="Nombres y Apellidos" />
        </div>

        <div class="form-group">
          <label>Teléfono / Celular <span class="required">*</span></label>
          <input type="text" v-model="checkinForm.telefono" required placeholder="Ej: 987654321" />
        </div>

        <div class="form-group">
          <label>Correo Electrónico</label>
          <input type="email" v-model="checkinForm.correo" placeholder="ejemplo@correo.com" />
        </div>

        <div class="form-group">
          <label>Tipo de Habitación</label>
          <select v-model="checkinForm.tipoHabitacion">
            <option value="">Seleccione tipo...</option>
            <option value="Simple">Simple</option>
            <option value="Doble">Doble</option>
            <option value="Suite">Suite</option>
            <option value="Junior">Junior</option>
          </select>
        </div>

        <!-- Piso field removed for recepcionista -->

        <div class="form-group">
          <label>Procedencia del Huésped</label>
          <select v-model="checkinForm.procedencia">
            <option value="">Seleccione procedencia...</option>
            <option value="Nacional">Nacional</option>
            <option value="Extranjero">Extranjero</option>
            <option value="Local">Local</option>
          </select>
        </div>

        <div class="form-group">
          <label>Días de Estadía</label>
          <input type="number" min="1" max="30" v-model.number="checkinForm.diasEstadia" placeholder="Ej: 3" />
        </div>

        <div class="form-group">
          <label>Habitación a Asignar <span class="required">*</span></label>
          <select v-model="checkinForm.idHabitacion" required>
            <option value="" disabled>Seleccione una habitación...</option>
            <option v-for="room in availableRooms" :key="room.ID_Habitacion" :value="room.ID_Habitacion">
              Hab {{ room.numero }} ({{ room.tipo || 'N/A' }} - S/. {{ room.precio_noche }})
            </option>
          </select>
        </div>

        <div class="upselling-widget">
          <div class="upselling-widget__header">
            <h4>Sugerencias Inteligentes de Upselling</h4>
            <span v-if="upsellingLoading" class="upselling-widget__state">Analizando…</span>
          </div>

          <div v-if="upsellingLoading" class="upselling-widget__empty">Evaluando oportunidades de venta…</div>
          <div v-else-if="upsellingError" class="upselling-widget__error">{{ upsellingError }}</div>
          <div v-else-if="highlightedService" class="upselling-widget__highlight">
            <strong>🔥 ¡Oportunidad de Venta!</strong>
            <p>Alta probabilidad de consumo de {{ highlightedService.name }}. Ofrécelo ahora mismo.</p>
          </div>
          <div v-else-if="sortedProbabilities.length" class="upselling-widget__body">
            <p class="upselling-widget__hint">Las probabilidades actuales indican estas oportunidades:</p>
            <ul class="upselling-list">
              <li v-for="item in sortedProbabilities" :key="item.name" class="upselling-item">
                <div class="upselling-item__row">
                  <span>{{ item.name }}</span>
                  <strong>{{ item.percent }}%</strong>
                </div>
                <div class="upselling-bar">
                  <span :style="{ width: `${item.percent}%` }"></span>
                </div>
              </li>
            </ul>
          </div>
          <div v-else class="upselling-widget__empty">Complete los datos del huésped para ver sugerencias inteligentes.</div>
        </div>

        <div class="checkin-form__submit">
          <button type="submit" class="btn-navy">🔑 Registrar Estadía y Generar Código de Acceso</button>
        </div>
      </form>
    </div>

    <div class="card">
      <h3 class="card__title">Gestión de Habitaciones</h3>
      <ul class="room-list">
        <li v-for="room in rooms" :key="room.ID_Habitacion" class="room-row">
          <div class="room-row__info">
            <strong>Hab {{ room.numero }}</strong>
            <span class="room-row__meta">Tipo: {{ room.tipo || 'N/A' }} — Precio: {{ room.precio_noche || '-' }}</span>
            <span v-if="room.amenidades && room.amenidades.length" class="room-row__meta">Amenidades: {{ room.amenidades.join(', ') }}</span>
          </div>
          <div class="room-row__actions">
            <button class="btn-gold btn-sm" @click="$emit('register-checkout', room)" v-if="room.estado === 'ocupada'">Registrar Check-Out</button>
            <span class="status-badge status-badge--mantenimiento" v-else-if="room.estado === 'mantenimiento'">
              <span class="status-badge__dot"></span>En Limpieza
            </span>
            <span class="status-badge status-badge--disponible" v-else-if="room.estado === 'disponible'">
              <span class="status-badge__dot"></span>Disponible
            </span>
          </div>
        </li>
      </ul>
    </div>

    <div class="card">
      <h3 class="card__title">Gestión de Notas de Servicio (Tickets de Huésped)</h3>

      <div v-if="tickets.length === 0" class="empty-state">
        <span class="empty-state__icon">📭</span>
        <p>No hay solicitudes de servicio pendientes en este momento.</p>
      </div>

      <ul v-else class="ticket-list">
        <li v-for="t in tickets" :key="t.id" class="ticket-row">
          <div class="ticket-row__info">
            <strong>{{ t.title }}</strong> — <span class="ticket-row__guest">{{ t.guest }}</span>

            <div v-if="t.type === 'parking'" class="parking-block">
              <select v-model="t.parking_number" class="parking-block__select">
                <option value="" disabled>Seleccione cochera...</option>
                <option v-for="p in availableParkings" :key="p.ID_Parking" :value="String(p.numero)">Cochera #{{ p.numero }}</option>
              </select>
              <div v-if="availableParkings.length === 0" class="parking-block__warning">⚠️ No hay cocheras disponibles.</div>
              <div class="parking-block__rate">💡 Tarifa Fija Automática: S/. 20.00</div>
            </div>
          </div>

          <div class="ticket-row__actions">
            <button class="btn-success btn-sm" @click="$emit('validate-ticket', t.id)" :disabled="t.type === 'parking' && !t.parking_number">Validar</button>
            <button class="btn-navy btn-sm" @click="$emit('mark-delivered', t.id)">Marcar Entregado</button>
            <button class="btn-danger btn-sm" @click="$emit('cancel-ticket', t.id)">Cancelar</button>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  rooms: Array,
  tickets: Array,
  availableParkings: Array,
  checkinForm: Object,
  generatedAccessCode: [String, Number],
})

defineEmits(['submit-checkin', 'register-checkout', 'validate-ticket', 'mark-delivered', 'cancel-ticket', 'clear-code'])

const upsellingPrediction = ref(null)
const upsellingLoading = ref(false)
const upsellingError = ref(null)

const availableRooms = computed(() => {
  const tipo = String(props.checkinForm?.tipoHabitacion || '').trim()
  return (props.rooms || []).filter((room) => {
    const estadoOk = String(room.estado || '').toLowerCase() === 'disponible'
    const tipoOk = !tipo || String((room.tipo || '')).toLowerCase() === tipo.toLowerCase()
    return estadoOk && tipoOk
  })
})

const sortedProbabilities = computed(() => {
  const rawProbabilities = upsellingPrediction.value?.probabilidades || {}
  return Object.entries(rawProbabilities)
    .map(([name, value]) => ({
      name,
      value: Number(value) || 0,
      percent: Math.round((Number(value) || 0) * 100),
    }))
    .sort((a, b) => b.value - a.value)
})

const highlightedService = computed(() => {
  return sortedProbabilities.value.find((item) => ['Spa', 'Lavanderia'].includes(item.name) && item.value > 0.6) || null
})

function getUpsellingPayload() {
  return {
    Tipo_Habitacion: props.checkinForm?.tipoHabitacion || '',
    Piso_Habitacion: String(props.checkinForm?.piso || ''),
    Procedencia_Huesped: props.checkinForm?.procedencia || '',
    Dias_Estadia: Number(props.checkinForm?.diasEstadia) || 1,
  }
}

async function requestUpsellingPrediction() {
  const payload = getUpsellingPayload()
  if (!payload.Tipo_Habitacion || !payload.Procedencia_Huesped || !payload.Dias_Estadia) {
    upsellingPrediction.value = null
    upsellingError.value = null
    return
  }

  upsellingLoading.value = true
  upsellingError.value = null

  try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001'}/api/predict-upselling`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    })

    if (!response.ok) {
      throw new Error('No fue posible obtener la predicción en este momento.')
    }

    const data = await response.json()
    upsellingPrediction.value = data || null
  } catch (err) {
    console.error('Error consultando upselling:', err)
    upsellingPrediction.value = null
    upsellingError.value = err.message || 'No fue posible obtener la predicción.'
  } finally {
    upsellingLoading.value = false
  }
}

watch(
  () => [props.checkinForm?.tipoHabitacion, props.checkinForm?.procedencia, props.checkinForm?.diasEstadia],
  () => {
    requestUpsellingPrediction()
  },
  { flush: 'post' }
)
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
.card--accent { border-left: 4px solid var(--gold); }
.card__title { font-size: 1.1rem; margin-bottom: 1rem; color: var(--navy); }
.card__title--accent { color: var(--navy-mid); }
.success-banner { background: rgba(62, 158, 111, 0.12); border-left: 4px solid var(--success); border-radius: var(--radius-sm); padding: 1rem; margin-bottom: 1rem; }
.success-banner__title { color: var(--success); font-weight: 700; margin-bottom: 0.5rem; }
.success-banner__text { color: var(--navy-mid); font-size: 0.9rem; margin-bottom: 0.5rem; }
.success-banner__code { display: block; background: var(--white); border: 2px solid var(--success); border-radius: var(--radius-sm); padding: 0.8rem; text-align: center; font-family: monospace; font-size: 1.3rem; color: var(--navy); margin-bottom: 1rem; }
.success-banner__dismiss { align-self: flex-start; }
.checkin-form { display: grid; gap: 1rem; }
.checkin-form__submit { display: flex; justify-content: center; }
.form-group { display: flex; flex-direction: column; gap: 0.35rem; }
.form-group label { font-size: 0.9rem; font-weight: 600; color: var(--navy-mid); }
.form-group input, .form-group select, .form-group textarea { border: 1px solid var(--cream-dark); border-radius: var(--radius-sm); padding: 0.65rem 0.8rem; font-family: inherit; font-size: 0.95rem; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: var(--navy); box-shadow: 0 0 0 3px rgba(30, 58, 95, 0.1); }
.btn-navy, .btn-gold, .btn-success, .btn-danger, .btn-sm { border: none; border-radius: var(--radius-sm); padding: 0.65rem 1.2rem; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: all 0.15s ease; }
.btn-navy { background: var(--navy); color: var(--white); }
.btn-navy:hover { background: var(--navy-dark); }
.btn-gold { background: var(--gold); color: var(--navy); }
.btn-gold:hover { background: var(--gold-dark); }
.btn-success { background: var(--success); color: var(--white); }
.btn-success:hover { background: var(--success-dark); }
.btn-danger { background: var(--danger); color: var(--white); }
.btn-danger:hover { background: var(--danger-dark); }
.btn-sm { padding: 0.4rem 0.8rem; font-size: 0.8rem; }
.upselling-widget { border: 1px solid var(--cream-dark); border-left: 4px solid var(--gold); border-radius: var(--radius-md); padding: 1rem; background: linear-gradient(135deg, rgba(255, 239, 197, 0.25) 0%, rgba(255, 255, 255, 0.95) 100%); }
.upselling-widget__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.upselling-widget__header h4 { margin: 0; color: var(--navy); font-size: 1rem; }
.upselling-widget__state { color: var(--navy-mid); font-size: 0.85rem; font-weight: 600; }
.upselling-widget__highlight { background: rgba(232, 150, 58, 0.12); border-radius: var(--radius-sm); padding: 0.8rem 0.9rem; color: var(--navy); line-height: 1.4; }
.upselling-widget__hint { color: var(--slate); font-size: 0.9rem; margin-bottom: 0.7rem; }
.upselling-widget__error { color: var(--danger); font-size: 0.92rem; }
.upselling-widget__empty { color: var(--slate); font-size: 0.92rem; }
.upselling-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.65rem; }
.upselling-item { display: grid; gap: 0.3rem; }
.upselling-item__row { display: flex; justify-content: space-between; align-items: center; font-size: 0.92rem; color: var(--navy-mid); }
.upselling-bar { width: 100%; height: 8px; border-radius: 999px; background: var(--cream); overflow: hidden; }
.upselling-bar span { display: block; height: 100%; background: linear-gradient(90deg, var(--gold) 0%, var(--warning) 100%); border-radius: inherit; transition: width 0.25s ease; }
.room-list, .ticket-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; }
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
.empty-state { text-align: center; padding: 2rem; }
.empty-state__icon { font-size: 3rem; display: block; margin-bottom: 1rem; }
.empty-state p { color: var(--slate); }
.ticket-row { display: flex; justify-content: space-between; align-items: flex-start; padding: 1rem 0; border-bottom: 1px solid var(--cream-dark); }
.ticket-row:last-child { border-bottom: none; }
.ticket-row__info { flex: 1; }
.ticket-row__guest { color: var(--slate); font-size: 0.9rem; }
.ticket-row__actions { display: flex; gap: 0.5rem; }
.parking-block { background: var(--cream); border-radius: var(--radius-sm); padding: 0.75rem; margin-top: 0.5rem; }
.parking-block__select { width: 100%; border: 1px solid var(--cream-dark); border-radius: var(--radius-sm); padding: 0.5rem; margin-bottom: 0.5rem; }
.parking-block__warning { color: var(--warning); font-size: 0.85rem; margin-bottom: 0.5rem; }
.parking-block__rate { color: var(--navy-mid); font-size: 0.85rem; font-weight: 600; }
.required { color: var(--danger); }
</style>
