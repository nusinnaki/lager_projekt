(function () {
  async function handleLoginSubmit(event) {
    event.preventDefault();

    const username = document.querySelector("#login-username")?.value?.trim() || "";
    const password = document.querySelector("#login-password")?.value || "";
    const message = document.querySelector("#login-message");

    try {
      const data = await window.App.authApi.login(username, password);
      if (data?.access_token) {
        window.App.api.setToken(data.access_token);
      }
      if (message) {
        message.textContent = "Login erfolgreich.";
        message.className = "message success";
      }
    } catch (err) {
      if (message) {
        message.textContent = err.message || "Login fehlgeschlagen.";
        message.className = "message error";
      }
    }
  }

  function initLogin() {
    const form = document.querySelector("#login-form");
    if (form) {
      form.addEventListener("submit", handleLoginSubmit);
    }
  }

  window.App = window.App || {};
  window.App.loginFeature = {
    initLogin
  };
})();
