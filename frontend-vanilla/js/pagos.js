const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";

const PEDIDOS_PENDIENTES_URL = `${API_BASE_URL.replace(/\/$/, "")}/cajero/pagos/pendientes`;
const PAGOS_URL = `${API_BASE_URL.replace(/\/$/, "")}/cajero/pagos`;

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

const alertSlot = document.getElementById("alertSlot");
const pagosTableBody = document.getElementById("pagosTableBody");
const pagosRecientesTableBody = document.getElementById("pagosRecientesTableBody");
const refreshPagosBtn = document.getElementById("refreshPagosBtn");

const summaryRole = document.getElementById("summaryRole");
const summarySede = document.getElementById("summarySede");
const summaryPendientes = document.getElementById("summaryPendientes");
const summaryTotal = document.getElementById("summaryTotal");

const pagoModal = document.getElementById("pagoModal");
const pagoForm = document.getElementById("pagoForm");
const closePagoModalBtn = document.getElementById("closePagoModalBtn");
const cancelPagoModalBtn = document.getElementById("cancelPagoModalBtn");
const pagoTotal = document.getElementById("pagoTotal");
const metodoPago = document.getElementById("metodo_pago");
const referenciaPago = document.getElementById("referencia_pago");
const montoEfectivo = document.getElementById("monto_efectivo");
const comprobanteModal = document.getElementById("comprobanteModal");
const comprobanteBadge = document.getElementById("comprobanteBadge");
const comprobanteSubtitulo = document.getElementById("comprobanteSubtitulo");
const comprobantePreview = document.getElementById("comprobantePreview");
const closeComprobanteModalBtn = document.getElementById("closeComprobanteModalBtn");
const cancelComprobanteModalBtn = document.getElementById("cancelComprobanteModalBtn");
const printComprobanteBtn = document.getElementById("printComprobanteBtn");

let pedidosPendientesCache = [];
let pagosRecientesCache = [];
let currentPedidoId = null;
let currentPedidoTotal = 0;
let currentComprobanteHtml = "";
let currentComprobanteTitulo = "Comprobante";

function getStoredValue(keys) {
  for (const key of keys) {
    const value = sessionStorage.getItem(key);
    if (value) return value;
  }
  return null;
}

function getRoleId() {
  return Number(getStoredValue(["rol_id", "role_id"]) || 0);
}

function getRoleName(roleId) {
  return { 1: "ADMIN", 2: "CAJERO", 3: "MESERO" }[Number(roleId)] || "USUARIO";
}

function getCurrentSedeId() {
  return Number(getStoredValue(["sede_id"]) || 0);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatCurrency(value) {
  return Number(value || 0).toLocaleString("es-CO", {
    style: "currency",
    currency: "COP",
    minimumFractionDigits: 0,
  });
}

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("es-CO");
}

function showAlert(message, type = "error") {
  const alert = document.createElement("div");
  alert.className = `alert alert--${type}`;
  alert.setAttribute("role", "alert");
  alert.textContent = message;
  alertSlot.replaceChildren(alert);

  window.clearTimeout(showAlert.timeoutId);
  showAlert.timeoutId = window.setTimeout(() => {
    if (alertSlot.contains(alert)) alert.remove();
  }, 5000);
}

async function apiRequest(url, options = {}) {
  if (!authToken) throw new Error("No se encontro un JWT.");

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${authToken}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json().catch(() => ({}))
    : await response.text();

  if (!response.ok) {
    const message =
      (payload && typeof payload === "object" && (payload.detail || payload.message || payload.error)) ||
      `Error HTTP ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

function getList(payload) {
  if (Array.isArray(payload)) return payload;
  const containers = [payload?.data, payload?.items, payload?.result, payload?.pedidos, payload?.pagos];
  for (const candidate of containers) {
    if (Array.isArray(candidate)) return candidate;
  }
  return [];
}

function renderSummary() {
  summaryRole.textContent = getRoleName(getRoleId());
  summarySede.textContent = getCurrentSedeId() ? `Sede ${getCurrentSedeId()}` : "Sin sede";
  summaryPendientes.textContent = String(pedidosPendientesCache.length);
  const total = pedidosPendientesCache.reduce((acc, item) => acc + Number(item.total || 0), 0);
  summaryTotal.textContent = formatCurrency(total);
}

function renderPendientes() {
  if (!pedidosPendientesCache.length) {
    pagosTableBody.innerHTML =
      '<tr><td class="empty-state" colspan="5">No hay pedidos pendientes por cobrar.</td></tr>';
    renderSummary();
    return;
  }

  pagosTableBody.innerHTML = pedidosPendientesCache
    .map((pedido) => {
      const pedidoId = pedido.id ?? pedido.pedido_id;
      const mesa = pedido.mesa_nombre || pedido.mesa || `Mesa ${pedido.mesa_id ?? "-"}`;
      const estado = pedido.estado || "ENTREGADO";
      const total = Number(pedido.total || pedido.total_pedido || 0);

      return `
        <tr>
          <td>#${escapeHtml(pedidoId)}</td>
          <td>${escapeHtml(mesa)}</td>
          <td><span class="status-pill">${escapeHtml(estado)}</span></td>
          <td>${formatCurrency(total)}</td>
          <td>
            <button
              class="action-btn"
              type="button"
              data-action="cobrar"
              data-id="${escapeHtml(pedidoId)}"
              data-total="${escapeHtml(total)}"
            >
              Cobrar
            </button>
          </td>
        </tr>
      `;
    })
    .join("");

  renderSummary();
}

function renderPagosRecientes() {
  if (!pagosRecientesCache.length) {
    pagosRecientesTableBody.innerHTML =
      '<tr><td class="empty-state" colspan="7">No hay pagos registrados todavia.</td></tr>';
    return;
  }

  pagosRecientesTableBody.innerHTML = pagosRecientesCache
    .map((pago) => {
      const fecha = pago.fecha || pago.creado_en || pago.created_at;
      const pedido = pago.pedido_id || pago.id_pedido || "-";
      const mesa = pago.mesa_nombre || pago.mesa || `Mesa ${pago.mesa_id ?? "-"}`;
      const metodo = pago.metodo_pago || pago.metodo || "-";
      const total = Number(pago.monto_total || pago.total || pago.valor || pago.monto || 0);
      const detalle = pago.referencia || pago.detalle || "-";
      const pagoId = pago.id ?? "";

      return `
        <tr>
          <td>${escapeHtml(formatDateTime(fecha))}</td>
          <td>#${escapeHtml(pedido)}</td>
          <td>${escapeHtml(mesa)}</td>
          <td>${escapeHtml(metodo)}</td>
          <td>${formatCurrency(total)}</td>
          <td>${escapeHtml(detalle)}</td>
          <td>
            <button
              class="action-btn action-btn--secondary"
              type="button"
              data-action="reimprimir"
              data-pago-id="${escapeHtml(pagoId)}"
            >
              Reimprimir
            </button>
          </td>
        </tr>
      `;
    })
    .join("");
}

function getComprobanteLines(pago) {
  const comprobante = String(pago?.comprobante || "").trim();
  if (!comprobante) return [];
  return comprobante
    .split(/\r?\n| - /)
    .map((line) => line.trim())
    .filter(Boolean);
}

function buildComprobanteHtml(pago, tipo = "ORIGINAL") {
  const fecha = pago?.fecha || pago?.creado_en || pago?.created_at;
  const pedido = pago?.pedido_id || pago?.id_pedido || "-";
  const mesa = pago?.mesa_nombre || pago?.mesa || `Mesa ${pago?.mesa_id ?? "-"}`;
  const sede = pago?.sede_id ? `Sede ${pago.sede_id}` : "Sede no especificada";
  const metodo = pago?.metodo_pago || pago?.metodo || "-";
  const total = Number(pago?.monto_total || pago?.total || pago?.valor || pago?.monto || 0);
  const subtotal = Number(pago?.subtotal_base || 0);
  const impuesto = Number(pago?.impuesto_total || 0);
  const efectivo = pago?.monto_efectivo == null ? null : Number(pago.monto_efectivo || 0);
  const tarjeta = pago?.monto_tarjeta == null ? null : Number(pago.monto_tarjeta || 0);
  const referencia = pago?.referencia || "Sin referencia";
  const esReimpresion = tipo === "REIMPRESION";
  const emitidoLabel = esReimpresion ? "Reimpreso" : "Emitido";
  const emitidoFecha = esReimpresion ? new Date().toISOString() : fecha;
  const lines = getComprobanteLines(pago);

  return `
    <article class="receipt-document ${esReimpresion ? "is-reprint" : "is-original"}">
      <div class="receipt-watermark">${esReimpresion ? "REIMPRESION" : "ORIGINAL"}</div>
      <header class="receipt-header">
        <div>
          <span class="receipt-kicker">RutaByte</span>
          <h3>Comprobante de pago</h3>
          <p>${escapeHtml(sede)}</p>
        </div>
        <strong class="receipt-type ${esReimpresion ? "receipt-type--reprint" : ""}">${esReimpresion ? "REIMPRESION" : "ORIGINAL"}</strong>
      </header>

      <dl class="receipt-grid">
        <div><dt>Comprobante</dt><dd>#${escapeHtml(pago?.id ?? "-")}</dd></div>
        <div><dt>Pedido</dt><dd>#${escapeHtml(pedido)}</dd></div>
        <div><dt>Mesa</dt><dd>${escapeHtml(mesa)}</dd></div>
        <div><dt>Metodo</dt><dd>${escapeHtml(metodo)}</dd></div>
        <div><dt>Fecha de pago</dt><dd>${escapeHtml(formatDateTime(fecha))}</dd></div>
        <div><dt>${emitidoLabel}</dt><dd>${escapeHtml(formatDateTime(emitidoFecha))}</dd></div>
      </dl>

      <div class="receipt-amounts">
        <div><span>Subtotal base</span><strong>${formatCurrency(subtotal)}</strong></div>
        <div><span>Impuesto</span><strong>${formatCurrency(impuesto)}</strong></div>
        ${efectivo !== null ? `<div><span>Efectivo</span><strong>${formatCurrency(efectivo)}</strong></div>` : ""}
        ${tarjeta !== null ? `<div><span>Tarjeta</span><strong>${formatCurrency(tarjeta)}</strong></div>` : ""}
        <div class="receipt-total"><span>Total pagado</span><strong>${formatCurrency(total)}</strong></div>
      </div>

      <section class="receipt-detail">
        <h4>Detalle</h4>
        <p>${escapeHtml(referencia)}</p>
        ${lines.length ? `<ul>${lines.map((line) => `<li>${escapeHtml(line)}</li>`).join("")}</ul>` : ""}
      </section>

      ${esReimpresion ? '<p class="receipt-note">Documento generado como reimpresion del comprobante original.</p>' : '<p class="receipt-note">Documento original emitido al confirmar el pago.</p>'}
    </article>
  `;
}

function openComprobanteModal(pago, tipo = "ORIGINAL") {
  if (!pago) {
    showAlert("No se encontro el comprobante solicitado.");
    return;
  }

  const esReimpresion = tipo === "REIMPRESION";
  comprobanteBadge.textContent = esReimpresion ? "REIMPRESION" : "ORIGINAL";
  comprobanteBadge.classList.toggle("eyebrow--warning", esReimpresion);
  comprobanteSubtitulo.textContent = esReimpresion
    ? "Esta copia incluye una marca visual de reimpresion."
    : "Comprobante original generado al confirmar el pago.";
  currentComprobanteTitulo = `${esReimpresion ? "Reimpresion" : "Comprobante"} pago ${pago.id ?? ""}`.trim();
  currentComprobanteHtml = buildComprobanteHtml(pago, tipo);
  comprobantePreview.innerHTML = currentComprobanteHtml;
  comprobanteModal.classList.add("is-open");
  comprobanteModal.setAttribute("aria-hidden", "false");
}

function closeComprobanteModal() {
  comprobanteModal.classList.remove("is-open");
  comprobanteModal.setAttribute("aria-hidden", "true");
  comprobantePreview.innerHTML = "";
  currentComprobanteHtml = "";
}

function printCurrentComprobante() {
  if (!currentComprobanteHtml) return;
  const printWindow = window.open("", "_blank", "width=860,height=900");
  if (!printWindow) {
    showAlert("El navegador bloqueo la ventana de impresion.");
    return;
  }

  printWindow.document.write(`
    <!doctype html>
    <html lang="es">
      <head>
        <meta charset="UTF-8" />
        <title>${escapeHtml(currentComprobanteTitulo)}</title>
        <style>${getReceiptPrintStyles()}</style>
      </head>
      <body>${currentComprobanteHtml}</body>
    </html>
  `);
  printWindow.document.close();
  printWindow.focus();
  printWindow.print();
}

function getReceiptPrintStyles() {
  return `
    * { box-sizing: border-box; }
    body { margin: 0; padding: 24px; color: #0f172a; font-family: Arial, sans-serif; background: #fff; }
    .receipt-document { position: relative; max-width: 760px; margin: 0 auto; padding: 28px; border: 1px solid #dbe7f5; overflow: hidden; }
    .receipt-watermark { position: absolute; inset: 40% auto auto 50%; transform: translate(-50%, -50%) rotate(-24deg); font-size: 4.5rem; font-weight: 900; color: rgba(15, 23, 42, 0.07); letter-spacing: 8px; white-space: nowrap; }
    .receipt-header, .receipt-grid, .receipt-amounts, .receipt-detail, .receipt-note { position: relative; z-index: 1; }
    .receipt-header { display: flex; justify-content: space-between; gap: 18px; border-bottom: 2px solid #e5edf7; padding-bottom: 18px; margin-bottom: 18px; }
    .receipt-kicker { color: #f97316; font-weight: 800; text-transform: uppercase; }
    h3 { margin: 6px 0; font-size: 2rem; }
    p { margin: 0; }
    .receipt-type { align-self: flex-start; padding: 10px 14px; border: 1px solid #abefc6; color: #027a48; }
    .receipt-type--reprint { border-color: #fed7aa; color: #c2410c; }
    .receipt-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin: 0 0 18px; }
    dt { color: #64748b; font-size: .82rem; font-weight: 700; text-transform: uppercase; }
    dd { margin: 4px 0 0; font-weight: 800; }
    .receipt-amounts { border-top: 1px solid #e5edf7; border-bottom: 1px solid #e5edf7; padding: 12px 0; display: grid; gap: 10px; }
    .receipt-amounts div { display: flex; justify-content: space-between; gap: 16px; }
    .receipt-total { font-size: 1.25rem; padding-top: 10px; border-top: 1px dashed #cfe0f2; }
    .receipt-detail { margin-top: 18px; }
    .receipt-detail h4 { margin: 0 0 8px; }
    .receipt-detail ul { margin: 10px 0 0; padding-left: 18px; }
    .receipt-note { margin-top: 18px; padding: 12px; background: #fff8f4; color: #9a3412; font-weight: 700; }
  `;
}

function openPagoModal() {
  pagoModal.classList.add("is-open");
  pagoModal.setAttribute("aria-hidden", "false");
}

function closePagoModal() {
  pagoModal.classList.remove("is-open");
  pagoModal.setAttribute("aria-hidden", "true");
  pagoForm.reset();
  currentPedidoId = null;
  currentPedidoTotal = 0;
  pagoTotal.textContent = formatCurrency(0);
  metodoPago.value = "EFECTIVO";
}

function applyMetodoPagoUi() {
  const metodo = metodoPago.value;
  const montoField = montoEfectivo.closest(".field");

  if (metodo === "MIXTO") {
    montoField.style.display = "grid";
    montoEfectivo.value = "";
    montoEfectivo.placeholder = "Ingresa el valor en efectivo";
  } else {
    montoField.style.display = "none";
    montoEfectivo.value = "";
  }
}

async function loadPendientes() {
  try {
    const payload = await apiRequest(PEDIDOS_PENDIENTES_URL);
    pedidosPendientesCache = getList(payload);
    renderPendientes();
  } catch (error) {
    pedidosPendientesCache = [];
    pagosTableBody.innerHTML = `<tr><td class="empty-state" colspan="5">${escapeHtml(error.message)}</td></tr>`;
    renderSummary();
  }
}

async function loadPagosRecientes() {
  try {
    const payload = await apiRequest(PAGOS_URL);
    pagosRecientesCache = getList(payload);
    renderPagosRecientes();
  } catch (error) {
    pagosRecientesCache = [];
    pagosRecientesTableBody.innerHTML =
      `<tr><td class="empty-state" colspan="7">${escapeHtml(error.message)}</td></tr>`;
  }
}

async function submitPago(event) {
  event.preventDefault();

  if (!currentPedidoId) {
    showAlert("No se encontro el pedido a cobrar.");
    return;
  }

  const metodo = metodoPago.value;
  const referencia = referenciaPago.value.trim() || "";
  const total = Number(currentPedidoTotal || 0);

  let monto_efectivo = 0;
  let monto_tarjeta = 0;

  if (metodo === "EFECTIVO") {
    monto_efectivo = total;
  } else if (metodo === "TARJETA") {
    monto_tarjeta = total;
  } else if (metodo === "MIXTO") {
    const rawEfectivo = String(montoEfectivo.value || "0").replace(/\D/g, "");
    const efectivoIngresado = parseFloat(rawEfectivo) || 0;

    if (!efectivoIngresado || efectivoIngresado <= 0 || efectivoIngresado >= total) {
      showAlert("Para pago mixto, el monto en efectivo debe ser mayor que 0 y menor al total.");
      return;
    }

    monto_efectivo = efectivoIngresado;
    monto_tarjeta = total - efectivoIngresado;
  }

  const payload = {
    pedido_id: currentPedidoId,
    metodo_pago: metodo,
    monto_efectivo,
    monto_tarjeta,
    referencia,
  };

  try {
    const result = await apiRequest(PAGOS_URL, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    showAlert(result?.message || "Pago registrado correctamente.", "success");
    closePagoModal();
    openComprobanteModal(result, "ORIGINAL");
    await loadPendientes();
    await loadPagosRecientes();
  } catch (error) {
    showAlert(error.message);
  }
}

let isShiftOpen = false;

async function checkActiveShift() {
  try {
    const response = await fetch(`${API_BASE_URL}/cajero/turnos/activo`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
    });

    if (response.status === 404) {
      isShiftOpen = false;
      showAlert("¡ATENCIÓN! No tienes un turno de caja abierto. Por favor, abre tu turno antes de cobrar.", "error");
      pagosTableBody.innerHTML = `<tr><td colspan="5" style="text-align: center; padding: 2.5rem 1.5rem;">
        <p style="color: #ef4444; font-weight: bold; margin: 0 0 1.25rem; font-size: 1.1rem;">Debes abrir un turno de caja para operar y procesar cobros.</p>
        <a href="turnos.html" class="btn btn-primary" style="display: inline-flex; align-items: center; justify-content: center; text-decoration: none; font-weight: 700; gap: 8px;">
          🎟️ Ir a Turnos de Caja
        </a>
      </td></tr>`;
      return false;
    }

    if (!response.ok) {
      throw new Error("Error al validar el estado del turno de caja");
    }

    isShiftOpen = true;
    return true;
  } catch (error) {
    console.error(error);
    showAlert(error.message);
    return false;
  }
}

pagosTableBody?.addEventListener("click", async (event) => {
  const button = event.target.closest('[data-action="cobrar"]');
  if (!button) return;

  const shiftOpen = await checkActiveShift();
  if (!shiftOpen) return;

  currentPedidoId = Number(button.dataset.id);
  currentPedidoTotal = Number(button.dataset.total || 0);
  pagoTotal.textContent = formatCurrency(currentPedidoTotal);

  metodoPago.value = "EFECTIVO";
  referenciaPago.value = "";
  montoEfectivo.value = "";

  // Reset discount inputs
  document.getElementById("descuento_valor").value = "0";
  document.getElementById("admin_username").value = "";
  document.getElementById("admin_password").value = "";

  applyMetodoPagoUi();
  openPagoModal();
});

pagosRecientesTableBody?.addEventListener("click", (event) => {
  const button = event.target.closest('[data-action="reimprimir"]');
  if (!button) return;

  const pagoId = Number(button.dataset.pagoId || 0);
  const pago = pagosRecientesCache.find((item) => Number(item.id) === pagoId);
  openComprobanteModal(pago, "REIMPRESION");
});

document.getElementById("btnAplicarDescuento")?.addEventListener("click", async () => {
  if (!currentPedidoId) return;

  const tipo_descuento = document.getElementById("tipo_descuento").value;
  const rawDescuento = String(document.getElementById("descuento_valor").value || "0").replace(/\D/g, "");
  const descuento_valor = parseFloat(rawDescuento) || 0;
  const admin_username = document.getElementById("admin_username").value.trim();
  const admin_password = document.getElementById("admin_password").value;

  if (descuento_valor <= 0) {
    showAlert("El valor del descuento debe ser mayor que 0.");
    return;
  }
  if (!admin_username || !admin_password) {
    showAlert("Debe ingresar las credenciales del Administrador para autorizar.");
    return;
  }

  const payload = {
    tipo_descuento,
    descuento_valor,
    admin_username,
    admin_password,
  };

  try {
    const updatedPedido = await apiRequest(`${PAGOS_URL}/${currentPedidoId}/descuento`, {
      method: "POST",
      body: JSON.stringify(payload),
    });

    // Successfully applied! Recalculate total.
    let itemsTotal = 0;
    if (updatedPedido && updatedPedido.detalles) {
      updatedPedido.detalles.forEach((d) => {
        if (!d.cancelado) {
          itemsTotal += parseFloat(d.cantidad) * parseFloat(d.precio_unitario);
        }
      });
    }
    const newTotal = Math.max(itemsTotal - parseFloat(updatedPedido.descuento || 0), 0);

    currentPedidoTotal = newTotal;
    pagoTotal.textContent = formatCurrency(newTotal);

    // Update in cache and redraw
    const cachedIdx = pedidosPendientesCache.findIndex((p) => (p.id ?? p.pedido_id) === currentPedidoId);
    if (cachedIdx !== -1) {
      pedidosPendientesCache[cachedIdx].total = newTotal;
    }
    renderPendientes();

    showAlert("Descuento manual aplicado y auditado con éxito.", "success");

    // Clear admin credentials fields
    document.getElementById("admin_username").value = "";
    document.getElementById("admin_password").value = "";
  } catch (error) {
    showAlert(error.message);
  }
});

metodoPago?.addEventListener("change", applyMetodoPagoUi);
closePagoModalBtn?.addEventListener("click", closePagoModal);
cancelPagoModalBtn?.addEventListener("click", closePagoModal);
closeComprobanteModalBtn?.addEventListener("click", closeComprobanteModal);
cancelComprobanteModalBtn?.addEventListener("click", closeComprobanteModal);
printComprobanteBtn?.addEventListener("click", printCurrentComprobante);
refreshPagosBtn?.addEventListener("click", async () => {
  const shiftOpen = await checkActiveShift();
  if (shiftOpen) {
    await Promise.all([loadPendientes(), loadPagosRecientes()]);
    showAlert("Datos actualizados.", "success");
  }
});
pagoModal?.addEventListener("click", (event) => {
  if (event.target === pagoModal) closePagoModal();
});
comprobanteModal?.addEventListener("click", (event) => {
  if (event.target === comprobanteModal) closeComprobanteModal();
});
pagoForm?.addEventListener("submit", submitPago);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && pagoModal?.classList.contains("is-open")) {
    closePagoModal();
  }
  if (event.key === "Escape" && comprobanteModal?.classList.contains("is-open")) {
    closeComprobanteModal();
  }
});

async function init() {
  if (!authToken) return;
  renderSummary();
  const shiftOpen = await checkActiveShift();
  if (shiftOpen) {
    await Promise.all([loadPendientes(), loadPagosRecientes()]);
  }
}

init();

function setupCurrencyInput(input) {
  if (!input) return;
  input.type = "text";
  input.inputMode = "numeric";
  
  input.addEventListener("input", (e) => {
    let cursorPosition = e.target.selectionStart;
    const originalLength = e.target.value.length;
    const clean = e.target.value.replace(/\D/g, "");
    
    if (clean) {
      const formatted = clean.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
      e.target.value = formatted;
      const newLength = e.target.value.length;
      cursorPosition = cursorPosition + (newLength - originalLength);
      e.target.setSelectionRange(cursorPosition, cursorPosition);
    } else {
      e.target.value = "";
    }
  });
}

// Bind listeners
setupCurrencyInput(montoEfectivo);
setupCurrencyInput(document.getElementById("descuento_valor"));