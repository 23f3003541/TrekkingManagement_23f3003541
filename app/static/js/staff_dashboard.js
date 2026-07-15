const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return { stats: { assigned_treks: 0, total_participants: 0, ongoing_treks: 0 }, treks: [] };
  },
  async mounted() {
    try {
      this.stats = await apiFetch('/api/staff/dashboard');
      this.treks = await apiFetch('/api/staff/treks');
    } catch (e) {
      console.error('Load failed (expected until backend is implemented):', e.message);
    }
  },
}).mount('#app');
