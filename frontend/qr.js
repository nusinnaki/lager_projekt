(function () {
  const productSelect = document.getElementById("productSelect");
  const productPickBtn = document.getElementById("productPickBtn");

  const qrScanBtn = document.getElementById("qrScanBtn");
  const qrStopBtn = document.getElementById("qrStopBtn");
  const qrScanBox = document.getElementById("qrScanBox");
  const msgEl = document.getElementById("msg");

  function setMsg(t) { if (msgEl) msgEl.textContent = t || ""; }

  function normalizePayload(s) {
    s = String(s || "").trim();
    const m = s.match(/(\d+)/);
    return m ? m[1] : "";
  }

  function selectProductById(idStr) {
    if (!productSelect) return false;

    const target = String(idStr);

    for (const opt of productSelect.options) {
      if (String(opt.value) === target) {
        productSelect.value = target;
        productSelect.dispatchEvent(new Event("change"));
        return true;
      }
    }
    return false;
  }

  function ensureProductDropdownOpen() {
    if (!productSelect) return;
    productSelect.focus();
    productSelect.click();
  }

  if (productPickBtn) {
    productPickBtn.addEventListener("click", ensureProductDropdownOpen);
  }

  let scanner = null;
  let running = false;

  async function startScan() {
    if (!window.Html5Qrcode) {
      setMsg("Scanner library missing.");
      return;
    }
    if (running) return;

    qrScanBox.style.display = "block";
    qrStopBtn.style.display = "inline-block";
    setMsg("");

    scanner = new Html5Qrcode("qrReader");

    try {
      running = true;
      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 260, height: 260 } },
        (decodedText) => {
          const v = normalizePayload(decodedText);
          if (!v) return;

          const ok = selectProductById(v);
          setMsg(ok ? `Selected product id ${v}` : `Scanned ${v}, but not in product list`);

          stopScan();
        },
        () => {}
      );
    } catch (e) {
      running = false;
      setMsg(String(e && e.message ? e.message : e));
      try { await scanner.stop(); } catch {}
      try { scanner.clear(); } catch {}
      scanner = null;
      qrScanBox.style.display = "none";
      qrStopBtn.style.display = "none";
    }
  }

  async function stopScan() {
    if (!scanner || !running) {
      qrScanBox.style.display = "none";
      qrStopBtn.style.display = "none";
      return;
    }
    try { await scanner.stop(); } catch {}
    try { scanner.clear(); } catch {}
    scanner = null;
    running = false;
    qrScanBox.style.display = "none";
    qrStopBtn.style.display = "none";
  }

  if (qrScanBtn) qrScanBtn.addEventListener("click", startScan);
  if (qrStopBtn) qrStopBtn.addEventListener("click", stopScan);
})();
