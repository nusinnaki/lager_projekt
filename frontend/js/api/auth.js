(function () {
  async function login(username, password) {
    return window.App.api.post("/auth/login", { username, password });
  }

  async function me() {
    return window.App.api.get("/auth/me");
  }

  async function changePassword(current_password, new_password) {
    return window.App.api.post("/auth/change-password", {
      current_password,
      new_password
    });
  }

  window.App = window.App || {};
  window.App.authApi = {
    login,
    me,
    changePassword
  };
})();
