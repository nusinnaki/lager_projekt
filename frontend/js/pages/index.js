(function () {
  const usernameInput = document.getElementById("usernameInput");
  const passwordInput = document.getElementById("passwordInput");
  const loginBtn = document.getElementById("loginBtn");
  const loginMsg = document.getElementById("loginMsg");
  const loginForm = document.getElementById("login-form");

  function clearSession() {
    localStorage.removeItem("lager_token");
    localStorage.removeItem("lager_user");
  }

  async function login(event) {
    if (event) event.preventDefault();

    const username = (usernameInput?.value || "").trim().toLowerCase();
    const password = passwordInput?.value || "";

    if (!username) {
      loginMsg.textContent = "Enter a username.";
      return;
    }

    if (!password) {
      loginMsg.textContent = "Enter a password.";
      return;
    }

    loginBtn.disabled = true;
    loginMsg.textContent = "Logging in...";

    try {
      const data = await window.App.authApi.login(username, password);

      localStorage.setItem("lager_token", data.access_token);
      localStorage.setItem("lager_user", JSON.stringify(data.user));

      window.location.href = "/lager";
    } catch (err) {
      console.error(err);
      clearSession();
      loginMsg.textContent = err.message || "Login failed.";
      loginBtn.disabled = false;
    }
  }

  if (loginForm) {
    loginForm.addEventListener("submit", login);
  }

  if (usernameInput) {
    usernameInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") login(e);
    });
  }

  if (passwordInput) {
    passwordInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") login(e);
    });
  }
})();
