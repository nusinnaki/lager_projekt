(function () {
  const path = location.pathname.split("/").pop();
  if (path !== "lager.html") return;

  const params = new URLSearchParams(location.search);
  const SITE = (params.get("site") || "").toLowerCase().trim();
  const API = `http://127.0.0.1:8000/api/${SITE}`;

  const pageTitle = document.getElementById("pageTitle");
  const workerSelect = document.getElementById("workerSelect");
  const productSelect = document.getElementById("productSelect");
  const qtyInput = document.getElementById("qtyInput");
  const msg = document.getElementById("msg");

  const scanBtn = document.getElementById("scanBtn");
  const scanPreview = document.getElementById("scanPreview");
  const takeBtn = document.getElementById("takeBtn");
  const loadBtn = document.getElementById("loadBtn");

  const overlay = document.getElementById("scannerOverlay");
  const closeScanBtn = document.getElementById("closeScanBtn");
  const video = document.getElementById("scanVideo");

  const stockTableBody = document.querySelector("#stockTable tbody");

  let scanStream = null;
  let scanTimer = null;
  let detector = null;

  function setMsg(t) { msg.textContent = t || ""; }

  function titleCase(s) {
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  }

  async function loadWorkers() {
    const res = await fetch(`${API}/workers`);
    const data = await res.json();
    workerSelect.innerHTML = `<option value="" selected disabled>Select worker</option>`;
    for (const w of data) {
      const opt = document.createElement("option");
      opt.value = String(w.id ?? w.name);
      opt.textContent = w.name;
      workerSelect.appendChild(opt);
    }
  }

  async function loadProducts() {
    const res = await fetch(`${API}/products`);
    const data = await res.json();
    productSelect.innerHTML = `<option value="" selected disabled>Select from the list</option>`;
    for (const p of data) {
      const opt = document.createElement("option");
      opt.value = String(p.id);
      opt.textContent = p.product_name ?? p.name ?? "";
      productSelect.appendChild(opt);
    }
  }

  async function loadStock() {
    const res = await fetch(`${API}/stock`);
    const data = await res.json();
    stockTableBody.innerHTML = "";
    for (const row of data) {
      const tr = document.createElement("tr");
      const tdName = document.createElement("td");
      const tdQty = document.createElement("td");
      tdQty.className = "right";
      tdName.textContent = row.product_name ?? row.name ?? "";
      tdQty.textContent = String(row.quantity ?? 0);
      tr.appendChild(tdName);
      tr.appendChild(tdQty);
      stockTableBody.appendChild(tr);
    }
  }

  async function resolveAndSelect(code) {
    const res = await fetch(`${API}/resolve?code=${encodeURIComponent(code)}`);
    if (!res.ok) {
      scanPreview.value = `Unknown code: ${code}`;
      return;
    }
    const p = await res.json();
    productSelect.value = String(p.id);
    scanPreview.value = `${p.product_name} (${p.internal_id})`;
  }

  function stopScanner() {
    if (scanTimer) { clearInterval(scanTimer); scanTimer = null; }
    if (scanStream) { for (const t of scanStream.getTracks()) t.stop(); scanStream = null; }
    overlay.style.display = "none";
  }

  async function startScanner() {
    if (!("BarcodeDetector" in window)) {
      scanPreview.value = "Scanner not supported in this browser";
      return;
    }
    detector = new BarcodeDetector({ formats: ["qr_code"] });
    overlay.style.display = "flex";

    scanStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "environment" },
      audio: false
    });
    video.srcObject = scanStream;

    scanTimer = setInterval(async () => {
      try {
        const codes = await detector.detect(video);
        if (!codes || codes.length === 0) return;
        const raw = (codes[0].rawValue || "").trim();
        if (!raw) return;
        stopScanner();
        await resolveAndSelect(raw);
      } catch (_) {}
    }, 250);
  }

async function submitAction(action) {
  setMsg("");

  const workerText = workerSelect.options[workerSelect.selectedIndex]?.textContent || "";
  const productText = productSelect.options[productSelect.selectedIndex]?.textContent || "";
  const quantity = Number(qtyInput.value || 0);

  const worker = workerSelect.value;
  const product_id = productSelect.value;

  if (!worker || !product_id || !quantity || quantity <= 0) {
    setMsg("Missing worker, product, or quantity");
    return;
  }

  const preview =
    `Confirm action:\n\n` +
    `Action: ${action.toUpperCase()}\n` +
    `Worker: ${workerText}\n` +
    `Product: ${productText}\n` +
    `Quantity: ${quantity}\n`;

  const ok = window.confirm(preview);
  if (!ok) {
    setMsg("Cancelled");
    return;
  }

  const payload = { worker, product_id: Number(product_id), quantity };

  const res = await fetch(`${API}/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    setMsg(`Error: ${res.status} ${text}`);
    return;
  }

  setMsg("Saved");
  await loadStock();
}


  if (!SITE) {
    pageTitle.textContent = "Invalid site";
    setMsg("Missing ?site=konstanz or ?site=sindelfingen");
    return;
  }

  pageTitle.textContent = `${titleCase(SITE)} Lager`;

  scanBtn.addEventListener("click", startScanner);
  closeScanBtn.addEventListener("click", stopScanner);
  overlay.addEventListener("click", (e) => { if (e.target === overlay) stopScanner(); });

  takeBtn.addEventListener("click", () => submitAction("take"));
  loadBtn.addEventListener("click", () => submitAction("load"));

  (async () => {
    await loadWorkers();
    await loadProducts();
    await loadStock();
  })();
})();
