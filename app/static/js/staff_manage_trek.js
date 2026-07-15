const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return {
      trekId: Number(document.getElementById('app').dataset.trekId),
      trek: {}, participants: [], editSlots: 0, editStatus: 'Open',
    };
  },
  methods: {
    async load() {
      this.trek = await apiFetch(`/api/treks/${this.trekId}`);
      this.editSlots = this.trek.available_slots;
      this.editStatus = this.trek.status;
      this.participants = await apiFetch(`/api/staff/treks/${this.trekId}/participants`);
    },
    async updateTrek() {
      await apiFetch(`/api/staff/treks/${this.trekId}`, {
        method: 'PATCH',
        body: JSON.stringify({ available_slots: Number(this.editSlots), status: this.editStatus }),
      });
      this.load();
    },
    async markCompleted() {
      if (!confirm('Mark this trek as completed?')) return;
      await apiFetch(`/api/staff/treks/${this.trekId}/complete`, { method: 'POST' });
      this.load();
    },
    async markStarted() {
      if (!confirm('Mark this trek as started?')) return;
      await apiFetch(`/api/staff/treks/${this.trekId}/start`, { method: 'POST' });
      this.load();
    },
  },
  mounted() {
    this.load().catch(e => console.error('Load failed (expected until backend is implemented):', e.message));
  },
}).mount('#app');
