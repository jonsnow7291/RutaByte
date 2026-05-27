
const API_BASE_URL = window.RUTABYTE_API_BASE_URL || document.body?.dataset.apiBaseUrl || "http://127.0.0.1:8000";
const REPORTES_URL = `${API_BASE_URL.replace(/\/$/, "")}/reportes/ventas`;
const EXPORT_CSV_URL = `${API_BASE_URL.replace(/\/$/, "")}/reportes/ventas/export/csv`;
const GRAFICAS_URL = `${API_BASE_URL.replace(/\/$/, "")}/reportes/ventas-graficas`;
const SEDES_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/sedes`;
const ADMIN_SEDES_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/sedes`;
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

const ventasDiaChart = document.getElementById("ventasDiaChart");
const productosTopChart = document.getElementById("productosTopChart");
const gananciaProductoChart = document.getElementById("gananciaProductoChart");
const ventasSedeChart = document.getElementById("ventasSedeChart");
const metodosPagoChart = document.getElementById("metodosPagoChart");
const stockBajoChart = document.getElementById("stockBajoChart");

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

function getCurrentSedeId() {
  return Number(getStoredValue(["sede_id"]) || 0);
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
    const message = (payload && typeof payload === "object" && (Array.isArray(payload.detail) ? payload.detail.map(d => d.msg).join("; ") : (payload.detail || payload.message || payload.error))) || `Error HTTP ${response.status}`;
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
  reporteSede.innerHTML = getRoleId() === 1
    ? '<option value="">Todas las sedes</option>'
    : '<option value="">Mi sede</option>';

  try {
    let data;
    try {
      data = await apiRequest(getRoleId() === 1 ? ADMIN_SEDES_URL : SEDES_URL);
    } catch {
      data = await apiRequest(SEDES_URL);
    }

    sedesCache = Array.isArray(data) ? data : [];
    sedesCache.forEach((sede) => {
      const option = document.createElement('option');
      option.value = sede.id;
      option.textContent = sede.nombre || `Sede ${sede.id}`;
      reporteSede.append(option);
    });

    if (getRoleId() !== 1) {
      const sedeId = getCurrentSedeId();
      if (sedeId) reporteSede.value = String(sedeId);
      reporteSede.disabled = true;
    }
  } catch (error) {
    console.warn(error.message);
  }
}


function clearCanvas(canvas, emptyMessage = "Sin datos para graficar") {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#64748b";
  ctx.font = "14px Arial";
  ctx.textAlign = "center";
  ctx.fillText(emptyMessage, width / 2, height / 2);
}

function drawBarChart(canvas, data, labelKey, valueKey, formatter = (value) => String(value)) {
  if (!canvas) return;
  if (!Array.isArray(data) || !data.length) {
    clearCanvas(canvas);
    return;
  }

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 42;
  const chartHeight = height - padding * 2;
  const chartWidth = width - padding * 2;
  const maxValue = Math.max(...data.map((item) => Number(item[valueKey] || 0)), 1);
  const barWidth = Math.max(18, chartWidth / data.length - 12);

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#dbe7f5";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  data.forEach((item, index) => {
    const value = Number(item[valueKey] || 0);
    const barHeight = (value / maxValue) * chartHeight;
    const x = padding + index * (chartWidth / data.length) + 6;
    const y = height - padding - barHeight;

    ctx.fillStyle = "#f97316";
    ctx.fillRect(x, y, barWidth, barHeight);

    ctx.fillStyle = "#0f172a";
    ctx.font = "11px Arial";
    ctx.textAlign = "center";
    ctx.fillText(formatter(value), x + barWidth / 2, Math.max(14, y - 6));

    const label = String(item[labelKey] || "-").slice(0, 12);
    ctx.fillStyle = "#64748b";
    ctx.fillText(label, x + barWidth / 2, height - 16);
  });
}

function drawLineChart(canvas, data, labelKey, valueKey) {
  if (!canvas) return;
  if (!Array.isArray(data) || !data.length) {
    clearCanvas(canvas);
    return;
  }

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 42;
  const chartHeight = height - padding * 2;
  const chartWidth = width - padding * 2;
  const maxValue = Math.max(...data.map((item) => Number(item[valueKey] || 0)), 1);

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#dbe7f5";
  ctx.beginPath();
  ctx.moveTo(padding, padding);
  ctx.lineTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();

  ctx.strokeStyle = "#1d4ed8";
  ctx.lineWidth = 3;
  ctx.beginPath();

  data.forEach((item, index) => {
    const x = padding + (data.length === 1 ? chartWidth / 2 : (index / (data.length - 1)) * chartWidth);
    const y = height - padding - (Number(item[valueKey] || 0) / maxValue) * chartHeight;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  data.forEach((item, index) => {
    const x = padding + (data.length === 1 ? chartWidth / 2 : (index / (data.length - 1)) * chartWidth);
    const y = height - padding - (Number(item[valueKey] || 0) / maxValue) * chartHeight;
    ctx.fillStyle = "#1d4ed8";
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#64748b";
    ctx.font = "11px Arial";
    ctx.textAlign = "center";
    ctx.fillText(String(item[labelKey] || "-").slice(5), x, height - 16);
  });
}

function drawPieChart(canvas, data, labelKey, valueKey) {
  if (!canvas) return;
  if (!Array.isArray(data) || !data.length) {
    clearCanvas(canvas);
    return;
  }

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const total = data.reduce((acc, item) => acc + Number(item[valueKey] || 0), 0);
  if (!total) {
    clearCanvas(canvas);
    return;
  }

  const colors = ["#f97316", "#1d4ed8", "#16a34a", "#9333ea", "#dc2626", "#0891b2"];
  let start = -Math.PI / 2;
  const radius = Math.min(width, height) / 3;
  const cx = width / 2 - 40;
  const cy = height / 2;

  ctx.clearRect(0, 0, width, height);

  data.forEach((item, index) => {
    const value = Number(item[valueKey] || 0);
    const slice = (value / total) * Math.PI * 2;
    ctx.fillStyle = colors[index % colors.length];
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, start, start + slice);
    ctx.closePath();
    ctx.fill();
    start += slice;
  });

  data.forEach((item, index) => {
    const y = 36 + index * 24;
    ctx.fillStyle = colors[index % colors.length];
    ctx.fillRect(width - 130, y - 10, 12, 12);
    ctx.fillStyle = "#0f172a";
    ctx.font = "12px Arial";
    ctx.textAlign = "left";
    ctx.fillText(`${item[labelKey]} (${item[valueKey]})`, width - 112, y);
  });
}

function renderGraficas(data) {
  drawLineChart(ventasDiaChart, data?.ventas_por_dia || [], "fecha", "total");
  drawBarChart(productosTopChart, data?.productos_top || [], "producto", "cantidad");
  drawBarChart(gananciaProductoChart, data?.ganancias || [], "producto", "ganancia", formatCurrency);
  drawPieChart(ventasSedeChart, data?.ventas_sede || [], "sede", "total");
  drawPieChart(metodosPagoChart, data?.metodos_pago || [], "metodo", "cantidad");
  drawBarChart(stockBajoChart, data?.stock_bajo || [], "producto", "stock");
}

async function cargarGraficas() {
  try {
    const query = buildQuery();
    const data = await apiRequest(`${GRAFICAS_URL}?${query}`);
    renderGraficas(data);
  } catch (error) {
    [ventasDiaChart, productosTopChart, gananciaProductoChart, ventasSedeChart, metodosPagoChart, stockBajoChart]
      .forEach((canvas) => clearCanvas(canvas, error.message));
  }
}

async function consultarReporte() {
  reportesTableBody.innerHTML = '<tr><td colspan="10">Consultando reporte...</td></tr>';
  try {
    const query = buildQuery();
    const data = await apiRequest(`${REPORTES_URL}?${query}`);
    reportesCache = Array.isArray(data) ? data : [];
    renderReportes();
    await cargarGraficas();
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

const exportMasivoBtn = document.getElementById("exportMasivoBtn");

async function exportarMasivoBackground() {
  try {
    const query = buildQuery();
    const result = await apiRequest(`${API_BASE_URL.replace(/\/$/, "")}/reportes/masivos?${query}`, {
      method: "POST"
    });
    showAlert(result.message || "El reporte se está procesando en segundo plano. Te notificaremos al finalizar.", "success");
  } catch (error) {
    showAlert(error.message);
  }
}

function connectNotifications() {
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${wsProtocol}//${API_BASE_URL.replace(/^https?:\/\//, "")}/ws/pedidos?token=${authToken}`;

  const socket = new WebSocket(wsUrl);

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.evento === "REPORTE_MASIVO_COMPLETO") {
        showToastNotification(data.mensaje, data.archivo_url);
      }
    } catch (e) {
      console.error(e);
    }
  };
}

function showToastNotification(message, actionUrl) {
  let container = document.getElementById("reportToastContainer");
  if (!container) {
    container = document.createElement("div");
    container.id = "reportToastContainer";
    container.style.position = "fixed";
    container.style.bottom = "24px";
    container.style.right = "24px";
    container.style.zIndex = "9999";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "12px";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.style.background = "rgba(22, 163, 74, 0.9)";
  toast.style.color = "#ffffff";
  toast.style.padding = "16px 24px";
  toast.style.borderRadius = "12px";
  toast.style.boxShadow = "0 8px 32px 0 rgba(0, 0, 0, 0.15)";
  toast.style.backdropFilter = "blur(8px)";
  toast.style.fontFamily = "system-ui, sans-serif";
  toast.style.fontSize = "14px";
  toast.style.fontWeight = "500";
  toast.style.transition = "all 0.3s ease";
  toast.style.transform = "translateY(50px)";
  toast.style.opacity = "0";

  toast.innerHTML = `
    <div>${message}</div>
    <a class="btn btn-ghost" href="${actionUrl}" style="margin-top: 8px; display: inline-block; color: white; border: 1px solid white; text-decoration: none; padding: 4px 8px; border-radius: 4px;" download>Descargar Reporte Generado</a>
  `;
  container.appendChild(toast);

  // Animate in
  setTimeout(() => {
    toast.style.transform = "translateY(0)";
    toast.style.opacity = "1";
  }, 10);

  // Remove after 8 seconds
  setTimeout(() => {
    toast.style.transform = "translateY(-50px)";
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 8000);
}

runReportBtn.addEventListener('click', consultarReporte);
exportCsvBtn.addEventListener('click', exportarCsv);
exportMasivoBtn?.addEventListener('click', exportarMasivoBackground);

if (authToken) {
  setDefaultDates();
  void loadSedes();
  connectNotifications();
  [ventasDiaChart, productosTopChart, gananciaProductoChart, ventasSedeChart, metodosPagoChart, stockBajoChart].forEach((canvas) => clearCanvas(canvas));
}
