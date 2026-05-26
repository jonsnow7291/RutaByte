const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";
const AUDITORIA_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/auditoria`;

const alertSlot = document.getElementById("alertSlot");
const tableBody = document.getElementById("auditoriaTableBody");
const filterForm = document.getElementById("filterForm");
const resetFiltersBtn = document.getElementById("resetFiltersBtn");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

function getToken() {
  return authToken;
}

function showAlert(message, type = "error") {
  const alert = document.createElement("div");
  alert.className = `alert alert--${type}`;
  alert.setAttribute("role", "alert");
  alert.textContent = message;

  alertSlot.replaceChildren(alert);

  window.clearTimeout(showAlert.timeoutId);
  showAlert.timeoutId = window.setTimeout(() => {
    if (alertSlot.contains(alert)) {
      alert.remove();
    }
  }, 5000);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}

async function apiRequest(url, options = {}) {
  const token = getToken();
  if (!token) {
    throw new Error("No se encontro un JWT.");
  }

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const payload = await parseResponse(response);

  if (!response.ok) {
    const message =
      (payload && typeof payload === "object" && (payload.detail || payload.message || payload.error)) ||
      (typeof payload === "string" && payload.trim()) ||
      `La API respondio con error HTTP ${response.status}.`;
    throw new Error(message);
  }

  return payload;
}

function renderEmptyState() {
  tableBody.innerHTML = `
    <tr>
      <td class="empty-state" colspan="5">
        No se encontraron registros de auditoria.
      </td>
    </tr>
  `;
}

function renderAuditoria(logs) {
  if (!logs || !logs.length) {
    renderEmptyState();
    return;
  }

  const rows = logs.map((log) => {
    const logId = log.id || "-";
    const usuarioId = log.usuario_id != null ? log.usuario_id : "Invitado (Desconocido)";
    const tipo = escapeHtml(log.tipo_evento ?? "-");
    const ip = escapeHtml(log.direccion_ip ?? "N/A");
    const fecha = new Date(log.creado_en).toLocaleString("es-CO");

    const badgeClass = tipo === "LOGIN_EXITOSO" ? "tag tag--active" : "tag tag--warning";

    return `
      <tr>
        <td><strong>${logId}</strong></td>
        <td>${usuarioId}</td>
        <td><span class="${badgeClass}">${tipo}</span></td>
        <td><code>${ip}</code></td>
        <td>${fecha}</td>
      </tr>
    `;
  });

  tableBody.innerHTML = "";
  tableBody.insertAdjacentHTML("beforeend", rows.filter(Boolean).join(""));
}

async function loadAuditoria(params = {}) {
  if (!authToken) {
    return;
  }

  try {
    tableBody.innerHTML = `
      <tr>
        <td class="empty-state" colspan="5">Cargando registros de auditoria...</td>
      </tr>
    `;

    // Construct URL with query parameters
    const url = new URL(AUDITORIA_URL);
    Object.keys(params).forEach(key => {
      if (params[key] !== null && params[key] !== undefined && params[key] !== "") {
        url.searchParams.append(key, params[key]);
      }
    });

    const payload = await apiRequest(url.toString());
    renderAuditoria(payload);
  } catch (error) {
    renderEmptyState();
    showAlert(error.message);
  }
}

function handleFilterSubmit(event) {
  event.preventDefault();

  const tipo_evento = document.getElementById("tipo_evento").value;
  const fecha_inicio_raw = document.getElementById("fecha_inicio").value;
  const fecha_fin_raw = document.getElementById("fecha_fin").value;

  const params = {};

  if (tipo_evento) {
    params.tipo_evento = tipo_evento;
  }

  if (fecha_inicio_raw) {
    // Append T00:00:00 to query the entire day starting from 12:00 AM
    params.fecha_inicio = `${fecha_inicio_raw}T00:00:00`;
  }

  if (fecha_fin_raw) {
    // Append T23:59:59 to query up to the end of the day 11:59 PM
    params.fecha_fin = `${fecha_fin_raw}T23:59:59`;
  }

  void loadAuditoria(params);
}

function resetFilters() {
  filterForm.reset();
  void loadAuditoria();
}

filterForm.addEventListener("submit", handleFilterSubmit);
resetFiltersBtn.addEventListener("click", resetFilters);

if (authToken) {
  void loadAuditoria();
}
