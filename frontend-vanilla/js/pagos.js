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

let pedidosPendientesCache = [];
let pagosRecientesCache = [];
let currentPedidoId = null;
let currentPedidoTotal = 0;

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
      '<tr><td class="empty-state" colspan="6">No hay pagos registrados todavia.</td></tr>';
    return;
  }

  pagosRecientesTableBody.innerHTML = pagosRecientesCache
    .map((pago) => {
      const fecha = pago.fecha || pago.creado_en || pago.created_at;
      const pedido = pago.pedido_id || pago.id_pedido || "-";
      const mesa = pago.mesa_nombre || pago.mesa || `Mesa ${pago.mesa_id ?? "-"}`;
      const metodo = pago.metodo_pago || pago.metodo || "-";
      const total = Number(pago.total || pago.valor || pago.monto || 0);
      const detalle = pago.referencia || pago.detalle || "-";

      return `
        <tr>
          <td>${escapeHtml(formatDateTime(fecha))}</td>
          <td>#${escapeHtml(pedido)}</td>
          <td>${escapeHtml(mesa)}</td>
          <td>${escapeHtml(metodo)}</td>
          <td>${formatCurrency(total)}</td>
          <td>${escapeHtml(detalle)}</td>
        </tr>
      `;
    })
    .join("");
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
      `<tr><td class="empty-state" colspan="6">${escapeHtml(error.message)}</td></tr>`;
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
    const efectivoIngresado = Number(montoEfectivo.value || 0);

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
    await loadPendientes();
    await loadPagosRecientes();
  } catch (error) {
    showAlert(error.message);
  }
}

pagosTableBody?.addEventListener("click", (event) => {
  const button = event.target.closest('[data-action="cobrar"]');
  if (!button) return;

  currentPedidoId = Number(button.dataset.id);
  currentPedidoTotal = Number(button.dataset.total || 0);
  pagoTotal.textContent = formatCurrency(currentPedidoTotal);

  metodoPago.value = "EFECTIVO";
  referenciaPago.value = "";
  montoEfectivo.value = "";
  applyMetodoPagoUi();
  openPagoModal();
});

metodoPago?.addEventListener("change", applyMetodoPagoUi);
closePagoModalBtn?.addEventListener("click", closePagoModal);
cancelPagoModalBtn?.addEventListener("click", closePagoModal);
refreshPagosBtn?.addEventListener("click", async () => {
  await Promise.all([loadPendientes(), loadPagosRecientes()]);
  showAlert("Datos actualizados.", "success");
});
pagoModal?.addEventListener("click", (event) => {
  if (event.target === pagoModal) closePagoModal();
});
pagoForm?.addEventListener("submit", submitPago);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && pagoModal?.classList.contains("is-open")) {
    closePagoModal();
  }
});

async function init() {
  if (!authToken) return;
  renderSummary();
  await Promise.all([loadPendientes(), loadPagosRecientes()]);
}

init();