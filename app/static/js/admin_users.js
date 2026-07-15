const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() { return { users: [], search: '' }; },
  methods: {
    async loadUsers() {
      const qs = this.search ? `?q=${encodeURIComponent(this.search)}` : '';
      this.users = await apiFetch('/api/admin/users' + qs);
    },
    async toggleStatus(u) {
      const newStatus = u.status === 'Active' ? 'Blacklisted' : 'Active';
      await apiFetch(`/api/admin/users/${u.id}/status`, { method: 'PATCH', body: JSON.stringify({ status: newStatus }) });
      this.loadUsers();
    },
  },
  mounted() {
    this.loadUsers().catch(e => console.error('Load failed (expected until backend is implemented):', e.message));
  },
}).mount('#app');
