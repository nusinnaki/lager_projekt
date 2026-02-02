(function () {
  const { adminFetch, apiGet } = window.App || {};

  const openAdmin = document.getElementById("openAdmin");
  const adminGate = document.getElementById("adminGate");
  const adminToken = document.getElementById("adminToken");
  const adminLogin = document.getElementById("adminLogin");
  const adminLogout = document.getElementById("adminLogout");
  const adminMsg = document.getElementById("adminMsg");
  const adminPanel = document.getElementById("adminPanel");

  const wAddName = document.getElementById("wAddName");
  const wAddBtn = document.getElementById("wAddBtn");

  const wRenameSelect = document.getElementById("wRenameSelect");
  const wRenameName = document.getElementById("wRenameName");
  const wRenameBtn = document.getElementById("wRenameBtn");

  const wRemoveSelect = document.getElementById("wRemoveSelect");
  const wRemoveBtn = document.getElementById("wRemoveBtn");

  const wReactivateSelect = document.getElementById("wReactivateSelect");
  const wReactivateBtn = document.getElementById("wReactivateBtn");

  const pAddKind = document.getElementById("pAddKind");
  const pAddNc = document.getElementById("pAddNc");
  const pAddMk = document.getElementById("pAddMk");
  const pAddPn = document.getElementById("pAddPn");
  const pAddBtn = document.getElementById("pAddBtn");

  const pAddNetcomFields = document.getElementById("pAddNetcomFields");
  const pAddWerkzeugFields = document.getElementById("pAddWerkzeugFields");

  const pRemoveSelect = document.getElementById("pRemoveSelect");
  const pRemoveBtn = document.getElementById("pRemoveBtn");

  function setAdminMsg(t) { if (adminMsg) adminMsg.textContent = t || ""; }
  function getToken() { return (sessionStorage.getItem("admin_token") || "").trim(); }
  function setToken(t) { sessionStorage.setItem("admin_token", (t || "").trim()); }
  function clearToken() { sessionStorage.removeItem("admin_token"); }

  function hidePanel() { if (adminPanel) adminPanel.style.display = "none"; }
  function showPanel() { if (adminPanel) adminPanel.style.display = "block"; }

  function fillSelect(sel, items, placeholder) {
    if (!sel) return;
    sel.innerHTML = "";

    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.disabled = true;
    opt0.selected = true;
    opt0.textContent = placeholder;
    sel.appendChild(opt0);

    for (const it of items) {
      const opt = document.createElement("option");
      opt.value = String(it.id);
      opt.textContent = it.name;
      sel.appendChild(opt);
    }
  }

  function updateProductAddFormVisibility() {
    const kind = (pAddKind && pAddKind.value ? pAddKind.value : "").trim().toLowerCase();

    if (pAddNetcomFields) pAddNetcomFields.style.display = (kind === "netcom") ? "block" : "none";
    if (pAddWerkzeugFields) pAddWerkzeugFields.style.display = (kind === "werkzeug") ? "block" : "none";

    if (kind !== "netcom") {
      if (pAddNc) pAddNc.value = "";
      if (pAddMk) pAddMk.value = "";
    }
    if (kind !== "werkzeug") {
      if (pAddPn) pAddPn.value = "";
    }
  }

  async function reloadWorkerLists() {
    const workers = await apiGet("/workers");
    const active = workers.filter(w => w.active);
    const inactive = workers.filter(w => !w.active);

    fillSelect(wRenameSelect, workers.map(w => ({ id: w.id, name: w.name })), "Select worker");
    fillSelect(wRemoveSelect, active.map(w => ({ id: w.id, name: w.name })), "Select active worker");
    fillSelect(wReactivateSelect, inactive.map(w => ({ id: w.id, name: w.name })), "Select inactive worker");
  }

  async function reloadProductLists() {
  const products = await apiGet("/products");
  const active = products.filter(p => p.active);

  fillSelect(
    pRemoveSelect,
    active.map(p => {
      let label;
      if (p.kind === "netcom") {
        label = `Netcom: ${p.materialkurztext}`;
      } else if (p.kind === "werkzeug") {
        label = `Werkzeug: ${p.product_name}`;
      } else {
        label = String(p.id);
      }

      return { id: p.id, name: label };
    }),
    "Select active product"
  );
}


  async function unlock() {
    setAdminMsg("");
    try {
      const tok = (adminToken && adminToken.value ? adminToken.value : "").trim();
      if (!tok) throw new Error("Missing token");
      setToken(tok);

      await adminFetch("/admin/ping", "GET");

      if (adminToken) adminToken.value = "";
      showPanel();
      await reloadWorkerLists();
      await reloadProductLists();
      updateProductAddFormVisibility();
      setAdminMsg("Unlocked");
    } catch (e) {
      clearToken();
      hidePanel();
      setAdminMsg(String(e.message || e));
    }
  }

  function lock() {
    clearToken();
    hidePanel();
    setAdminMsg("Locked");
  }

  async function addWorker() {
    setAdminMsg("");
    const name = (wAddName && wAddName.value ? wAddName.value : "").trim();
    if (!name) { setAdminMsg("Missing new name"); return; }

    try {
      await adminFetch("/admin/workers", "POST", { name });
      if (wAddName) wAddName.value = "";
      await reloadWorkerLists();
      setAdminMsg("Worker added");
    } catch (e) {
      setAdminMsg(String(e.message || e));
    }
  }

  async function renameWorker() {
    setAdminMsg("");
    const id = Number(wRenameSelect && wRenameSelect.value ? wRenameSelect.value : 0);
    const name = (wRenameName && wRenameName.value ? wRenameName.value : "").trim();
    if (!id || !name) { setAdminMsg("Missing worker or new name"); return; }

    try {
      await adminFetch(`/admin/workers/${id}/rename`, "PATCH", { name });
      if (wRenameName) wRenameName.value = "";
      await reloadWorkerLists();
      setAdminMsg("Worker renamed");
    } catch (e) {
      setAdminMsg(String(e.message || e));
    }
  }

  async function removeWorker() {
    setAdminMsg("");
    const id = Number(wRemoveSelect && wRemoveSelect.value ? wRemoveSelect.value : 0);
    if (!id) { setAdminMsg("Missing worker"); return; }

    try {
      await adminFetch(`/admin/workers/${id}/active`, "PATCH", { active: false });
      await reloadWorkerLists();
      setAdminMsg("Worker deactivated");
    } catch (e) {
      setAdminMsg(String(e.message || e));
    }
  }

  async function reactivateWorker() {
    setAdminMsg("");
    const id = Number(wReactivateSelect && wReactivateSelect.value ? wReactivateSelect.value : 0);
    if (!id) { setAdminMsg("Missing worker"); return; }

    try {
      await adminFetch(`/admin/workers/${id}/active`, "PATCH", { active: true });
      await reloadWorkerLists();
      setAdminMsg("Worker reactivated");
    } catch (e) {
      setAdminMsg(String(e.message || e));
    }
  }

  async function addProduct() {
    setAdminMsg("");

    const kind = (pAddKind && pAddKind.value ? pAddKind.value : "").trim().toLowerCase();
    if (!kind) { setAdminMsg("Select category"); return; }

    const nc_nummer = (pAddNc && pAddNc.value ? pAddNc.value : "").trim();
    const materialkurztext = (pAddMk && pAddMk.value ? pAddMk.value : "").trim();
    const product_name = (pAddPn && pAddPn.value ? pAddPn.value : "").trim();

    if (kind === "netcom") {
      if (!nc_nummer || !materialkurztext) { setAdminMsg("Missing NC Nummer or Materialkurztext"); return; }
    } else if (kind === "werkzeug") {
      if (!product_name) { setAdminMsg("Missing Produkt Name"); return; }
    } else {
      setAdminMsg("Invalid category");
      return;
    }

    try {
      await adminFetch("/admin/products", "POST", { kind, nc_nummer, materialkurztext, product_name });

      if (pAddKind) pAddKind.value = "";
      if (pAddNc) pAddNc.value = "";
      if (pAddMk) pAddMk.value = "";
      if (pAddPn) pAddPn.value = "";
      updateProductAddFormVisibility();

      await reloadProductLists();
      setAdminMsg("Product added");
    } catch (e) {
      setAdminMsg(String(e.message || e));
    }
  }

  async function removeProduct() {
    setAdminMsg("");
    const id = Number(pRemoveSelect && pRemoveSelect.value ? pRemoveSelect.value : 0);
    if (!id) { setAdminMsg("Missing product"); return; }

    try {
      await adminFetch(`/admin/products/${id}/active`, "PATCH", { active: false });
      await reloadProductLists();
      setAdminMsg("Product deactivated");
    } catch (e) {
      setAdminMsg(String(e.message || e));
    }
  }

  if (openAdmin && adminGate) {
    openAdmin.addEventListener("click", () => {
      adminGate.style.display = (adminGate.style.display === "none") ? "block" : "none";
    });
  }

  if (adminLogin) adminLogin.addEventListener("click", unlock);
  if (adminLogout) adminLogout.addEventListener("click", lock);

  if (wAddBtn) wAddBtn.addEventListener("click", addWorker);
  if (wRenameBtn) wRenameBtn.addEventListener("click", renameWorker);
  if (wRemoveBtn) wRemoveBtn.addEventListener("click", removeWorker);
  if (wReactivateBtn) wReactivateBtn.addEventListener("click", reactivateWorker);

  if (pAddBtn) pAddBtn.addEventListener("click", addProduct);
  if (pRemoveBtn) pRemoveBtn.addEventListener("click", removeProduct);

  if (pAddKind) pAddKind.addEventListener("change", updateProductAddFormVisibility);

  hidePanel();
  if (adminGate) adminGate.style.display = "none";
  updateProductAddFormVisibility();

  if (!getToken()) clearToken();
})();
