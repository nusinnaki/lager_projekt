(function () {
  const params = new URLSearchParams(window.location.search);
  const SITE = (params.get("site") || "konstanz").toLowerCase().trim();

  if (!SITE) {
    throw new Error("Missing ?site=konstanz or ?site=sindelfingen");
  }

  // Explicit backend origin (FastAPI on 8000)
  const API_BASE = "http://127.0.0.1:8000";
  const API = `${API_BASE}/api/${SITE}`;

  async function readError(res) {
    try {
      return await res.text();
    } catch {
      return "";
    }
  }

  async function apiGet(path) {
    const res = await fetch(`${API}${path}`, {
      method: "GET",
      headers: {
        "Accept": "application/json"
      }
    });

    if (!res.ok) {
      const msg = await readError(res);
      throw new Error(`GET ${path} -> ${res.status} ${msg}`);
    }

    return res.json();
  }

  async function apiPost(path, body) {
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json"
      },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      const msg = await readError(res);
      throw new Error(`POST ${path} -> ${res.status} ${msg}`);
    }

    try {
      return await res.json();
    } catch {
      return {};
    }
  }

  async function adminFetch(path, method, body) {
    const token = (sessionStorage.getItem("admin_token") || "").trim();
    if (!token) {
      throw new Error("Missing admin token");
    }

    const res = await fetch(`${API}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Admin-Token": token
      },
      body: body ? JSON.stringify(body) : undefined
    });

    if (!res.ok) {
      const msg = await readError(res);
      throw new Error(`${method} ${path} -> ${res.status} ${msg}`);
    }

    try {
      return await res.json();
    } catch {
      return {};
    }
  }

  window.App = window.App || {};
  window.App.SITE = SITE;
  window.App.API = API;
  window.App.apiGet = apiGet;
  window.App.apiPost = apiPost;
  window.App.adminFetch = adminFetch;
})();