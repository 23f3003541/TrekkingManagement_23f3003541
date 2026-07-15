const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return { bookings: [] };
  },
  async mounted() {
    try {
      this.bookings = await apiFetch('/api/admin/bookings');
    } catch (e) {
      console.error('Load failed:', e.message);
    }
  },
}).mount('#app');
