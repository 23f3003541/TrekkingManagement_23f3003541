const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      stats: { total_treks: 0, total_users: 0, total_staff: 0, total_bookings: 0 },
      recentBookings: [],
    };
  },
  async mounted() {
    try {
      // GET /api/admin/dashboard -> { total_treks, total_users, total_staff, total_bookings }
      this.stats = await apiFetch('/api/admin/dashboard');
      // GET /api/admin/bookings -> list of bookings; show latest 5 here
      const bookings = await apiFetch('/api/admin/bookings');
      this.recentBookings = bookings.slice(0, 5);
    } catch (e) {
      console.error('Dashboard load failed (expected until models/auth are implemented):', e.message);
    }
  },
}).mount('#app');
