(function () {
  const params = new URLSearchParams(location.search);
  const SITE = (params.get("site") || "konstanz").toLowerCase().trim();
  const API = `http://127.0.0.1:8000/api/${SITE}`;


  function errText(res) {
    return res.text().catch(() => "");
  }

  async function apiGet(path) {
    if (!API) throw new Error("Missing ?site=konstanz or ?site=sindelfingen");
    const res = await fetch(`${API}${path}`);
    if (!res.ok) throw new Error(`${res.status} ${await errText(res)}`);
    return await res.json();
  }

  async function apiPost(path, body) {
    if (!API) throw new Error("Missing ?site=konstanz or ?site=sindelfingen");
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`${res.status} ${await errText(res)}`);
    return await res.json().catch(() => ({}));
  }

  async function adminFetch(path, method, body) {
    if (!API) throw new Error("Missing ?site=konstanz or ?site=sindelfingen");
    const tok = (sessionStorage.getItem("admin_token") || "").trim();
    if (!tok) throw new Error("Missing admin token");

    const res = await fetch(`${API}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Token": tok,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) throw new Error(`${res.status} ${await errText(res)}`);
    return await res.json().catch(() => ({}));
  }

  window.App = window.App || {};
  window.App.SITE = SITE;
  window.App.API = API;
  window.App.apiGet = apiGet;
  window.App.apiPost = apiPost;
  window.App.adminFetch = adminFetch;
})();
