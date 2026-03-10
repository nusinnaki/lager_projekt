(function () {
  async function listHistory() {
    return window.App.api.get("/history");
  }

  window.App = window.App || {};
  window.App.historyApi = {
    listHistory
  };
})();
