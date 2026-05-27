const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";

const ALGORITMOS_URL = `${API_BASE_URL.replace(/\/$/, "")}/admin/algoritmos`;
const authToken = window.RutaByteAuthGuard?.requireAuth?.();

const alertSlot = document.getElementById("alertSlot");
const runAllBtn = document.getElementById("runAllBtn");
const runVorazBtn = document.getElementById("runVorazBtn");
const runMochilaBtn = document.getElementById("runMochilaBtn");
const runRecursividadBtn = document.getElementById("runRecursividadBtn");
const vorazResult = document.getElementById("vorazResult");
const mochilaResult = document.getElementById("mochilaResult");
const recursividadResult = document.getElementById("recursividadResult");

const productosDemo = [
  { nombre: "Coca-Cola", stock: 2, umbral: 10, costo_compra: 3000, ganancia: 1500, valor: 8 },
  { nombre: "Papas", stock: 1, umbral: 5, costo_compra: 5000, ganancia: 2500, valor: 10 },
  { nombre: "Aguardiente", stock: 0, umbral: 4, costo_compra: 12000, ganancia: 9000, valor: 18 },
  { nombre: "Agua", stock: 7, umbral: 8, costo_compra: 1500, ganancia: 800, valor: 3 },
];

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
      (payload && typeof payload === "object" && (Array.isArray(payload.detail) ? payload.detail.map(d => d.msg).join("; ") : (payload.detail || payload.message || payload.error))) ||
      `Error HTTP ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

function pretty(data) {
  return JSON.stringify(data, null, 2);
}

async function runVoraz() {
  vorazResult.textContent = "Ejecutando...";
  const payload = { presupuesto: 20000, productos: productosDemo };
  const result = await apiRequest(`${ALGORITMOS_URL}/voraz`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  vorazResult.textContent = pretty(result);
}

async function runMochila() {
  mochilaResult.textContent = "Ejecutando...";
  const payload = { presupuesto: 20000, productos: productosDemo };
  const result = await apiRequest(`${ALGORITMOS_URL}/mochila`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  mochilaResult.textContent = pretty(result);
}

async function runRecursividad() {
  recursividadResult.textContent = "Ejecutando...";
  const payload = {
    numeros: [1, 2, 3, 4, 5],
    numero: 6,
    datos_anidados: ["Bebidas", ["Coca-Cola", "Agua"], ["Comida", ["Papas", "Perro Caliente"]]],
  };
  const result = await apiRequest(`${ALGORITMOS_URL}/recursividad`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  recursividadResult.textContent = pretty(result);
}

async function safely(fn) {
  try {
    await fn();
    showAlert("Algoritmo ejecutado correctamente.", "success");
  } catch (error) {
    showAlert(error.message);
  }
}

runVorazBtn?.addEventListener("click", () => safely(runVoraz));
runMochilaBtn?.addEventListener("click", () => safely(runMochila));
runRecursividadBtn?.addEventListener("click", () => safely(runRecursividad));
runAllBtn?.addEventListener("click", async () => {
  await safely(async () => {
    await runVoraz();
    await runMochila();
    await runRecursividad();
  });
});
