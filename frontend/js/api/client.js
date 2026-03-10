(function () {
  const API_BASE = "/api";

  function getToken() {
    return (localStorage.getItem("lager_token") || "").trim();
  }

  function setToken(token) {
    localStorage.setItem("lager_token", (token || "").trim());
  }

  function clearToken() {
    localStorage.removeItem("lager_token");
  }

  function authHeaders(extra = {}) {
    const headers = {
      Accept: "application/json",
      ...extra
    };

    const token = getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  }

  async function readJsonSafe(res) {
    try {
      return await res.json();
    } catch {
      return null;
    }
  }

  async function request(path, options = {}) {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: authHeaders(options.headers || {})
    });

    const data = await readJsonSafe(res);

    if (!res.ok) {
      const detail = data?.detail || `${res.status} ${res.statusText}`;
      throw new Error(detail);
    }

    return data;
  }

  async function get(path) {
    return request(path, { method: "GET" });
  }

  async function post(path, body) {
    return request(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
  }

  window.App = window.App || {};
  window.App.api = {
    get,
    post,
    getToken,
    setToken,
    clearToken
  };
})();
