const { createApp } = Vue;

createApp({
  delimiters: ['[[', ']]'],
  data() {
    return { history: [], exporting: false };
  },
  methods: {
    async loadHistory() {
      // GET /api/user/history -> list of past (Completed/Cancelled) bookings
      this.history = await apiFetch('/api/user/history');
    },
    async exportCsv() {
      this.exporting = true;
      try {
        // Triggers the async Celery job in app/tasks.py (export_booking_history),
        // then polls the task-status endpoint every 2s until it's ready and
        // alerts the user with a real download link (no more empty promises).
        const res = await apiFetch('/api/user/export-history', { method: 'POST' });
        await this.pollExportStatus(res.task_id);
      } catch (e) {
        alert(e.message || 'Could not start export.');
        this.exporting = false;
      }
    },
    async pollExportStatus(taskId, attempt = 0) {
      const status = await apiFetch(`/api/user/export-history/status/${taskId}`);

      if (status.state === 'SUCCESS') {
        this.exporting = false;
        alert('Your trekking history CSV is ready!');
        window.location.href = status.download_url;
        return;
      }
      if (status.state === 'FAILURE') {
        this.exporting = false;
        alert('Export failed: ' + (status.error || 'unknown error'));
        return;
      }
      if (attempt > 30) { // ~1 min of polling — give up gracefully
        this.exporting = false;
        alert('Export is taking longer than expected. Please try again shortly.');
        return;
      }
      setTimeout(() => this.pollExportStatus(taskId, attempt + 1), 2000);
    },
  },
  mounted() {
    this.loadHistory().catch(e => console.error('Load failed (expected until backend is implemented):', e.message));
  },
}).mount('#app');
