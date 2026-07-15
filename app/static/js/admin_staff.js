const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() { return { staff: [], search: '' }; },
  methods: {
    async loadStaff() {
      const qs = this.search ? `?q=${encodeURIComponent(this.search)}` : '';
      this.staff = await apiFetch('/api/admin/staff' + qs);
    },
    async toggleStatus(s) {
      const newStatus = s.status === 'Active' ? 'Blacklisted' : 'Active';
      await apiFetch(`/api/admin/staff/${s.id}/status`, { method: 'PATCH', body: JSON.stringify({ status: newStatus }) });
      this.loadStaff();
    },
  },
  mounted() {
    this.loadStaff().catch(e => console.error('Load failed (expected until backend is implemented):', e.message));
  },
}).mount('#app');
