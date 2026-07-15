const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      full_name: '', email: '', password: '', confirm_password: '',
      contact_number: '', loading: false, error: '',
    };
  },
  methods: {
    async register() {
      this.error = '';
      if (this.password !== this.confirm_password) {
        this.error = 'Passwords do not match.';
        return;
      }
      this.loading = true;
      try {
        // Hits /api/auth/register once app/auth.py is implemented.
        await apiFetch('/api/auth/register', {
          method: 'POST',
          body: JSON.stringify({
            full_name: this.full_name, email: this.email,
            password: this.password, contact_number: this.contact_number,
          }),
        });
        window.location.href = '/login';
      } catch (e) {
        this.error = e.message || 'Registration failed.';
      } finally {
        this.loading = false;
      }
    },
  },
}).mount('#app');
