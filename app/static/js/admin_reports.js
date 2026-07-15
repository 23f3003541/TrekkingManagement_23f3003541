const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      summaryCards: [
        { label: 'Total Treks', value: 0 },
        { label: 'Total Users', value: 0 },
        { label: 'Total Staff', value: 0 },
        { label: 'Total Bookings', value: 0 },
      ],
      summary: {
        total_treks: 0,
        total_users: 0,
      },
      bookings: [],
      error: '',
    };
  },
  methods: {
    barStyle(value) {
      const max = Math.max(this.summary.total_treks, this.summary.total_users, 1);
      const pct = Math.round((value / max) * 100);
      return { width: pct + '%' };
    },
    async loadReportData() {
      this.error = '';
      try {
        const [summary, bookings] = await Promise.all([
          apiFetch('/api/admin/dashboard'),
          apiFetch('/api/admin/bookings'),
        ]);
        this.summaryCards[0].value = summary.total_treks;
        this.summaryCards[1].value = summary.total_users;
        this.summaryCards[2].value = summary.total_staff;
        this.summaryCards[3].value = summary.total_bookings;
        this.summary = summary;
        this.bookings = bookings;
      } catch (e) {
        this.error = e.message || 'Report load failed.';
      }
    },
  },
  mounted() {
    this.loadReportData();
  },
}).mount('#app');
