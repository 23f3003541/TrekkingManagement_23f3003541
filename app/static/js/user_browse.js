const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return { treks: [], q: '', difficulty: '', location: '', locations: [], page: 1, pages: 1 };
  },
  methods: {
    async loadTreks() {
      const params = new URLSearchParams({ status: 'Open', page: this.page });
      if (this.q) params.set('q', this.q);
      if (this.difficulty) params.set('difficulty', this.difficulty);
      if (this.location) params.set('location', this.location);
      const data = await apiFetch('/api/treks?' + params.toString());
      this.treks = data.treks || [];
      this.pages = data.pages || 1;
      this.locations = [...new Set(this.treks.map(t => t.location))];
    },
    async book(t) {
      try {
        await apiFetch('/api/user/bookings', {
          method: 'POST',
          body: JSON.stringify({ trek_id: t.id })
        });
        await this.loadTreks();
        alert(`Booked successfully: ${t.trek_name}`);
      } catch (e) {
        alert(e.message || 'Booking failed');
      }
    },
    viewDetails(t) {
      alert(`${t.trek_name} — ${t.location}\n${t.difficulty} · ${t.duration_days} days\nSlots left: ${t.available_slots}`);
    },
  },
  mounted() {
    this.loadTreks().catch(e => console.error('Load failed (expected until backend is implemented):', e.message));
  },
}).mount('#app');
