const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return { email: '', password: '', remember: false, loading: false, error: '' };
  },
  methods: {
    async login() {
      this.error = '';
      this.loading = true;
      try {
        const data = await apiFetch('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email: this.email, password: this.password }),
        });
        localStorage.setItem('tma_token', data.access_token);
        window.location.href = data.redirect || '/';
      } catch (e) {
        this.error = e.message || 'Login failed. Please check your credentials.';
      } finally {
        this.loading = false;
      }
    },
  },
}).mount('#app');
