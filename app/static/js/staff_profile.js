const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      form: {
        full_name: '',
        email: '',
        contact_number: '',
        status: '',
        experience: '',
        specialization: '',
      },
      error: '',
      success: '',
    };
  },
  methods: {
    async loadProfile() {
      const data = await apiFetch('/api/staff/profile');
      this.form = {
        full_name: data.full_name,
        email: data.email,
        contact_number: data.contact_number,
        status: data.status,
        experience: data.experience || '',
        specialization: data.specialization || '',
      };
    },
    async saveProfile() {
      this.error = '';
      this.success = '';
      try {
        await apiFetch('/api/staff/profile', {
          method: 'PUT',
          body: JSON.stringify({
            full_name: this.form.full_name,
            contact_number: this.form.contact_number,
            experience: this.form.experience,
            specialization: this.form.specialization,
          }),
        });
        this.success = 'Profile updated successfully.';
      } catch (e) {
        this.error = e.message || 'Unable to save profile.';
      }
    },
  },
  mounted() {
    this.loadProfile().catch(e => { this.error = e.message || 'Unable to load profile.'; });
  },
}).mount('#app');
