const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      form: { full_name: '', email: '', contact_number: '', password: '', experience: '', specialization: '', status: 'Active' },
      confirm_password: '', error: '',
    };
  },
  methods: {
    async createStaff() {
      this.error = '';
      if (this.form.password !== this.confirm_password) { this.error = 'Passwords do not match.'; return; }
      try {
        await apiFetch('/api/admin/staff', { method: 'POST', body: JSON.stringify(this.form) });
        window.location.href = '/admin/staff';
      } catch (e) {
        this.error = e.message || 'Could not create staff.';
      }
    },
  },
}).mount('#app');
