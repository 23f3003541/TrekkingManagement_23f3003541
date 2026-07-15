const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      form: { full_name: '', email: '', contact_number: '' },
      error: '',
      success: '',
    };
  },
  methods: {
    async loadProfile() {
      try {
        const p = await apiFetch('/api/user/profile');
        this.form = {
          full_name: p.full_name,
          email: p.email,
          contact_number: p.contact_number || '',
        };
      } catch (e) {
        this.error = e.message || 'Unable to load profile.';
      }
    },
    async saveProfile() {
      this.error = '';
      this.success = '';
      try {
        await apiFetch('/api/user/profile', {
          method: 'PUT',
          body: JSON.stringify({
            full_name: this.form.full_name,
            contact_number: this.form.contact_number,
          }),
        });
        this.success = 'Profile updated successfully.';
      } catch (e) {
        this.error = e.message || 'Unable to save profile.';
      }
    },
  },
  mounted() {
    this.loadProfile();
  },
}).mount('#app');
