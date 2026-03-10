(function () {
  async function listUsers() {
    return window.App.api.get("/admin/users");
  }

  async function listWorkers() {
    return window.App.api.get("/admin/workers");
  }

  window.App = window.App || {};
  window.App.adminApi = {
    listUsers,
    listWorkers
  };
})();
