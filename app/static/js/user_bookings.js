const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      profileName: '', bookings: [], error: '', success: ''
    };
  },
  methods: {
    async loadBookings() {
      this.error = '';
      try {
        const data = await apiFetch('/api/user/dashboard');
        this.bookings = data.my_bookings || [];
      } catch (e) {
        this.error = e.message || 'Failed to load bookings.';
      }
    },
    async loadProfile() {
      try {
        const p = await apiFetch('/api/user/profile');
        this.profileName = p.full_name;
      } catch (_) {
        this.profileName = 'Trekker';
      }
    },
    async cancelBooking(bookingId) {
      this.error = '';
      this.success = '';
      if (!confirm('Cancel this booking?')) {
        return;
      }
      try {
        await apiFetch(`/api/user/bookings/${bookingId}/cancel`, { method: 'POST' });
        await this.loadBookings();
        this.success = 'Booking cancelled successfully.';
      } catch (e) {
        this.error = e.message || 'Cancellation failed.';
      }
    },
  },
  mounted() {
    this.loadProfile();
    this.loadBookings();
  },
}).mount('#app');
