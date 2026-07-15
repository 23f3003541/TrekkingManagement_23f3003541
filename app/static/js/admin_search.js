const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      tab: 'users',
      query: '',
      users: [],
      staff: [],
      treks: [],
      error: '',
      searchTimer: null,
    };
  },
  methods: {
    async loadCurrentTab() {
      this.error = '';
      try {
        if (this.tab === 'users') {
          const q = this.query ? `?q=${encodeURIComponent(this.query)}` : '';
          this.users = await apiFetch('/api/admin/users' + q);
        } else if (this.tab === 'staff') {
          const q = this.query ? `?q=${encodeURIComponent(this.query)}` : '';
          this.staff = await apiFetch('/api/admin/staff' + q);
        } else {
          const queryText = this.query ? `&q=${encodeURIComponent(this.query)}` : '';
          const data = await apiFetch(`/api/treks?status=&per_page=100${queryText}`);
          this.treks = data.treks || [];
        }
      } catch (e) {
        this.error = e.message || 'Search failed.';
      }
    },
    debounceLoad() {
      clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(() => this.loadCurrentTab(), 250);
    },
  },
  watch: {
    tab() {
      this.loadCurrentTab();
    },
  },
  mounted() {
    this.loadCurrentTab();
  },
}).mount('#app');
