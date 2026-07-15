const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      treks: [], staffList: [], search: '', showForm: false,
      form: { trek_name: '', location: '', difficulty: '', duration_days: '', available_slots: '', start_date: '', end_date: '', status: 'Open' },
    };
  },
  computed: {
    filteredTreks() {
      const s = this.search.toLowerCase();
      if (!s) return this.treks;
      return this.treks.filter(t => t.trek_name.toLowerCase().includes(s) || t.location.toLowerCase().includes(s));
    },
  },
  methods: {
    async loadTreks() {
      // Uses the shared /api/treks listing (status filter left blank to show all statuses for admin view)
      const data = await apiFetch('/api/treks?status=&per_page=100');
      this.treks = data.treks || [];
    },
    async loadStaff() {
      this.staffList = await apiFetch('/api/admin/staff');
    },
    async assignStaff(t, staffProfileId) {
      if (!staffProfileId) return; // "Unassigned" chosen — no unassign endpoint, so no-op for now
      await apiFetch(`/api/admin/staff/${staffProfileId}/assign/${t.id}`, { method: 'POST' });
      this.loadTreks();
    },
    async createTrek() {
      await apiFetch('/api/admin/treks', { method: 'POST', body: JSON.stringify(this.form) });
      this.showForm = false;
      this.form = { trek_name: '', location: '', difficulty: '', duration_days: '', available_slots: '', start_date: '', end_date: '', status: 'Open' };
      this.loadTreks();
    },
    editTrek(t) {
      const newSlots = prompt('Available slots:', t.available_slots);
      if (newSlots === null) return;
      apiFetch(`/api/admin/treks/${t.id}`, { method: 'PUT', body: JSON.stringify({ available_slots: Number(newSlots) }) })
        .then(() => this.loadTreks());
    },
    async deleteTrek(id) {
      if (!confirm('Remove this trek?')) return;
      await apiFetch(`/api/admin/treks/${id}`, { method: 'DELETE' });
      this.loadTreks();
    },
  },
  mounted() {
    Promise.all([this.loadTreks(), this.loadStaff()])
      .catch(e => console.error('Load failed:', e.message));
  },
}).mount('#app');
