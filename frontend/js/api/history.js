(function () {
  async function listLogs(limit = 50, offset = 0) {
    return window.App.api.get(`/logs?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`);
  }

  window.App = window.App || {};
  window.App.historyApi = {
    listLogs
  };
})();
