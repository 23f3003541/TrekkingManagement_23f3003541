const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      profileName: '', profileContact: '', treks: [], myBookings: [], difficulty: '', location: '',
      locations: [], editingProfile: false, profileForm: { full_name: '', contact_number: '' },
    };
  },
  methods: {
    async loadTreks() {
      const params = new URLSearchParams({ status: 'Open' });
      if (this.difficulty) params.set('difficulty', this.difficulty);
      if (this.location) params.set('location', this.location);
      const data = await apiFetch('/api/treks?' + params.toString());
      this.treks = data.treks || [];
      this.locations = [...new Set(this.treks.map(t => t.location))];
    },
    async book(t) {
      try {
        await apiFetch('/api/user/bookings', { method: 'POST', body: JSON.stringify({ trek_id: t.id }) });
        this.loadTreks();
        this.loadDashboard();
      } catch (e) {
        alert(e.message || 'Booking failed');
      }
    },
    async loadDashboard() {
      const data = await apiFetch('/api/user/dashboard');
      this.myBookings = data.my_bookings || [];
    },
    async loadProfile() {
      const p = await apiFetch('/api/user/profile');
      this.profileName = p.full_name;
      this.profileContact = p.contact_number;
      this.profileForm = { full_name: p.full_name, contact_number: p.contact_number || '' };
    },
    async saveProfile() {
      await apiFetch('/api/user/profile', { method: 'PUT', body: JSON.stringify(this.profileForm) });
      this.editingProfile = false;
      this.loadProfile();
    },
  },
  mounted() {
    Promise.all([this.loadTreks(), this.loadDashboard(), this.loadProfile()])
      .catch(e => console.error('Load failed (expected until backend is implemented):', e.message));
  },
}).mount('#app');
