const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return { trekId: Number(document.getElementById('app').dataset.trekId), trekName: '', participants: [], error: '' };
  },
  methods: {
    async loadParticipants() {
      const data = await apiFetch(`/api/staff/treks/${this.trekId}/participants`);
      this.participants = data;
      const trek = await apiFetch(`/api/treks/${this.trekId}`);
      this.trekName = trek.trek_name;
    },
  },
  mounted() {
    this.loadParticipants().catch(e => { this.error = e.message || 'Unable to load participants.'; });
  },
}).mount('#app');
