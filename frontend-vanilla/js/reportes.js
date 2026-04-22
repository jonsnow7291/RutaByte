
const API_BASE_URL = window.RUTABYTE_API_BASE_URL || document.body?.dataset.apiBaseUrl || "http://127.0.0.1:8000";
const REPORTES_URL = `${API_BASE_URL.replace(/\/$/, "")}/reportes/ventas`;
const EXPORT_CSV_URL = `${API_BASE_URL.replace(/\/$/, "")}/reportes/ventas/export/csv`;
const SEDES_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/sedes`;
const authToken = window.RutaByteAuthGuard?.requireAuth?.();

const alertSlot = document.getElementById("alertSlot");
const fechaInicio = document.getElementById("fechaInicio");
const fechaFin = document.getElementById("fechaFin");
const reporteSede = document.getElementById("reporteSede");
const runReportBtn = document.getElementById("runReportBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const reportesTableBody = document.getElementById("reportesTableBody");
const summaryFilas = document.getElementById("summaryFilas");
const summaryVenta = document.getElementById("summaryVenta");
const summaryCosto = document.getElementById("summaryCosto");
const summaryGanancia = document.getElementById("summaryGanancia");

let sedesCache = [];
let reportesCache = [];

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

function formatCurrency(value) {
  const number = Number(value || 0);
  return new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(number);
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
  const response = await fetch(url, { ...options, headers });
  if (options.expectBlob) {
    if (!response.ok) throw new Error(`Error HTTP ${response.status}`);
    return response.blob();
  }
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json().catch(() => ({})) : await response.text();
  if (!response.ok) {
    const message = (payload && typeof payload === "object" && (payload.detail || payload.message || payload.error)) || `Error HTTP ${response.status}`;
    throw new Error(message);
  }
  return payload;
}

function buildQuery() {
  const inicio = fechaInicio.value;
  const fin = fechaFin.value;
  if (!inicio || !fin) throw new Error("Debes seleccionar fecha inicio y fecha fin.");
  const params = new URLSearchParams();
  params.set("fecha_inicio", new Date(inicio).toISOString());
  params.set("fecha_fin", new Date(fin).toISOString());
  if (reporteSede.value) params.set("sede_id", reporteSede.value);
  return params.toString();
}

function renderSummary() {
  summaryFilas.textContent = String(reportesCache.length);
  summaryVenta.textContent = formatCurrency(reportesCache.reduce((acc, fila) => acc + Number(fila.venta_total || 0), 0));
  summaryCosto.textContent = formatCurrency(reportesCache.reduce((acc, fila) => acc + Number(fila.costo_total || 0), 0));
  summaryGanancia.textContent = formatCurrency(reportesCache.reduce((acc, fila) => acc + Number(fila.ganancia || 0), 0));
}

function renderReportes() {
  if (!reportesCache.length) {
    reportesTableBody.innerHTML = '<tr><td colspan="10">No se encontraron ventas para el rango consultado.</td></tr>';
    renderSummary();
    return;
  }
  reportesTableBody.innerHTML = reportesCache.map((fila) => `
    <tr>
      <td>${formatDateTime(fila.fecha)}</td>
      <td>${fila.sede}</td>
      <td>${fila.codigo_producto}</td>
      <td>${fila.producto}</td>
      <td>${fila.unidades_vendidas}</td>
      <td>${formatCurrency(fila.precio_compra)}</td>
      <td>${formatCurrency(fila.precio_venta)}</td>
      <td>${formatCurrency(fila.venta_total)}</td>
      <td>${formatCurrency(fila.costo_total)}</td>
      <td>${formatCurrency(fila.ganancia)}</td>
    </tr>
  `).join("");
  renderSummary();
}

async function loadSedes() {
  if (getRoleId() !== 1) return;
  try {
    const data = await apiRequest(SEDES_URL);
    sedesCache = Array.isArray(data) ? data : [];
    sedesCache.forEach((sede) => {
      const option = document.createElement('option');
      option.value = sede.id;
      option.textContent = sede.nombre || `Sede ${sede.id}`;
      reporteSede.append(option);
    });
  } catch (error) {
    console.warn(error.message);
  }
}

async function consultarReporte() {
  reportesTableBody.innerHTML = '<tr><td colspan="10">Consultando reporte...</td></tr>';
  try {
    const query = buildQuery();
    const data = await apiRequest(`${REPORTES_URL}?${query}`);
    reportesCache = Array.isArray(data) ? data : [];
    renderReportes();
  } catch (error) {
    reportesTableBody.innerHTML = `<tr><td colspan="10">${error.message}</td></tr>`;
    showAlert(error.message);
  }
}

async function exportarCsv() {
  try {
    const query = buildQuery();
    const blob = await apiRequest(`${EXPORT_CSV_URL}?${query}`, { expectBlob: true });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `reporte_ventas_${Date.now()}.csv`;
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (error) {
    showAlert(error.message);
  }
}

function setDefaultDates() {
  const now = new Date();
  const start = new Date(now);
  start.setHours(0,0,0,0);
  const end = new Date(now);
  end.setHours(23,59,0,0);
  const toLocalInput = (date) => new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0,16);
  fechaInicio.value = toLocalInput(start);
  fechaFin.value = toLocalInput(end);
}

runReportBtn.addEventListener('click', consultarReporte);
exportCsvBtn.addEventListener('click', exportarCsv);

if (authToken) {
  setDefaultDates();
  loadSedes();
}
