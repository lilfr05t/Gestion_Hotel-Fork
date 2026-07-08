<template>
  <div class="dashboard-shell">
    <aside class="dashboard-sidebar">
      <div class="brand-card">
        <div class="brand-card__icon">🏨</div>
        <div>
          <h2>Hotel PMS</h2>
          <p>Gestión Inteligente</p>
        </div>
      </div>

      <div class="sidebar-card">
        <span class="sidebar-card__label">Rol activo</span>
        <strong>{{ roleLabel }}</strong>
      </div>

      <div class="sidebar-card sidebar-card--accent">
        <span class="sidebar-card__label">Operación</span>
        <p>Panel central de gestión del hotel y sus servicios.</p>
      </div>
    </aside>

    <div class="dashboard-main">
      <header class="topbar">
        <h1 class="topbar__title">Hotel PMS · Gestión Interna</h1>
        <div class="topbar__right">
          <span class="role-badge">{{ roleLabel }}</span>
          <button class="btn-ghost-danger" @click="$emit('logout')">Cerrar sesión</button>
        </div>
      </header>

      <main class="page">
        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
defineProps({
  roleLabel: {
    type: String,
    default: 'Usuario',
  },
})

defineEmits(['logout'])
</script>

<style scoped>
.dashboard-shell {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  min-height: 100vh;
  background: var(--cream);
  color: var(--navy);
}

.dashboard-sidebar {
  background: linear-gradient(180deg, var(--navy) 0%, var(--navy-dark) 100%);
  color: var(--white);
  padding: 1.4rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.brand-card {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  padding: 1rem;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.12);
}
.brand-card__icon {
  font-size: 1.7rem;
}
.brand-card h2 {
  margin: 0;
  font-size: 1.05rem;
}
.brand-card p {
  margin: 0.15rem 0 0;
  color: rgba(255,255,255,0.8);
  font-size: 0.88rem;
}

.sidebar-card {
  padding: 0.9rem 1rem;
  border-radius: var(--radius-md);
  background: rgba(255,255,255,0.1);
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.sidebar-card--accent {
  background: rgba(255, 207, 92, 0.16);
  border: 1px solid rgba(255, 207, 92, 0.28);
}
.sidebar-card__label {
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.8;
}
.sidebar-card p {
  margin: 0;
  color: rgba(255,255,255,0.9);
  font-size: 0.92rem;
}

.dashboard-main {
  display: flex;
  flex-direction: column;
}

.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.1rem 1.75rem;
  background: var(--white);
  border-bottom: 1px solid var(--cream-dark);
}
.topbar__title {
  font-family: var(--font-display);
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--navy);
}
.topbar__right {
  display: flex;
  gap: 1rem;
  align-items: center;
}
.role-badge {
  background: var(--cream);
  color: var(--navy-mid);
  border: 1px solid var(--cream-dark);
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
}
.btn-ghost-danger {
  background: transparent;
  color: var(--danger);
  border: none;
  font-weight: 600;
  cursor: pointer;
}
.btn-ghost-danger:hover {
  text-decoration: underline;
}

.page {
  padding: 1.5rem;
  display: grid;
  gap: 1.25rem;
  background: var(--cream);
  min-height: 100%;
}
</style>
