const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";

const INVENTARIO_URL = `${API_BASE_URL.replace(/\/$/, "")}/cajero/inventario`;
const INVENTARIO_ENTRADAS_URL = `${INVENTARIO_URL}/entradas`;
const INVENTARIO_MOVIMIENTOS_URL = `${INVENTARIO_URL}/movimientos`;
const PRODUCTOS_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/productos`;

// intentamos primero la ruta de admin y luego la publica
const SEDES_URLS = [
  `${API_BASE_URL.replace(/\/$/, "")}/admin/sedes`,
  `${API_BASE_URL.replace(/\/$/, "")}/api/sedes`,
];

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

const alertSlot = document.getElementById("alertSlot");
const filterSede = document.getElementById("filterSede");
const filterTexto = document.getElementById("filterTexto");
const filterCritico = document.getElementById("filterCritico");
const inventarioTableBody = document.getElementById("inventarioTableBody");
const movimientosTableBody = document.getElementById("movimientosTableBody");
const openEntradaModalBtn = document.getElementById("openEntradaModalBtn");
const closeEntradaModalBtn = document.getElementById("closeEntradaModalBtn");
const cancelEntradaModalBtn = document.getElementById("cancelEntradaModalBtn");
const refreshInventarioBtn = document.getElementById("refreshInventarioBtn");
const entradaModal = document.getElementById("entradaModal");
const entradaForm = document.getElementById("entradaForm");
const entradaSede = document.getElementById("entradaSede");
const entradaProducto = document.getElementById("entradaProducto");
const entradaCantidad = document.getElementById("entradaCantidad");
const entradaUmbral = document.getElementById("entradaUmbral");
const summaryRole = document.getElementById("summaryRole");
const summarySede = document.getElementById("summarySede");
const summaryCriticos = document.getElementById("summaryCriticos");
const summaryMovimientos = document.getElementById("summaryMovimientos");

let inventarioCache = [];
let movimientosCache = [];
let productosCache = [];
let sedesCache = [];

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
  const containers = [
    payload?.data,
    payload?.items,
    payload?.result,
    payload?.inventario,
    payload?.movimientos,
    payload?.sedes,
    payload?.productos,
  ];
  for (const candidate of containers) {
    if (Array.isArray(candidate)) return candidate;
  }
  return [];
}

function getProductoNombre(item) {
  // 1. Intenta directo desde backend
  const nombreDirecto =
    item?.producto_nombre ||
    item?.nombre_producto ||
    item?.producto?.nombre ||
    item?.nombre;

  if (nombreDirecto && nombreDirecto !== "Producto") return nombreDirecto;

  // 2. Buscar ID en diferentes formatos
  const productoId =
    item?.producto_id ||
    item?.id_producto ||
    item?.producto?.id;

  if (!productoId) return "Producto";

  // 3. Buscar en cache
  const producto = productosCache.find(
    (p) => Number(p.id) === Number(productoId)
  );

  return producto?.nombre || "Producto";
}

function getProductoCodigo(item) {
  const codigoDirecto =
    item?.codigo ||
    item?.producto_codigo ||
    item?.producto?.codigo;

  if (codigoDirecto) return codigoDirecto;

  const productoId = Number(item?.producto_id || item?.id_producto || item?.producto?.id || 0);
  const producto = productosCache.find((p) => Number(p.id) === productoId);

  return producto?.codigo || `PROD-${productoId || "-"}`;
}

function getStock(item) {
  return Number(item?.stock ?? item?.stock_actual ?? item?.cantidad ?? 0);
}

function getUmbral(item) {
  return Number(item?.umbral ?? item?.umbral_critico ?? item?.stock_minimo ?? 0);
}

function isCritical(item) {
  const stock = getStock(item);
  const umbral = getUmbral(item);
  return stock <= umbral;
}

function getSedeNameById(id) {
  const sede = sedesCache.find((item) => Number(item.id) === Number(id));
  return sede?.nombre || `Sede ${id}`;
}

function renderSummary() {
  const selectedSedeId = Number(filterSede.value || getCurrentSedeId() || 0);
  summaryRole.textContent = getRoleName(getRoleId());
  summarySede.textContent = selectedSedeId ? getSedeNameById(selectedSedeId) : "Sin sede";
  summaryCriticos.textContent = String(inventarioCache.filter(isCritical).length);
  summaryMovimientos.textContent = String(movimientosCache.length);
}

function renderInventario() {
  const query = filterTexto.value.trim().toLowerCase();
  const critico = filterCritico.value;

  const filtered = inventarioCache.filter((item) => {
    const hayTexto =
      !query ||
      getProductoNombre(item).toLowerCase().includes(query) ||
      getProductoCodigo(item).toLowerCase().includes(query);

    const critical = isCritical(item);
    const cumpleCritico = !critico || (critico === "critico" ? critical : !critical);
    return hayTexto && cumpleCritico;
  });

  if (!filtered.length) {
    inventarioTableBody.innerHTML =
      '<tr><td class="empty-state" colspan="6">No hay registros de inventario para mostrar.</td></tr>';
    renderSummary();
    return;
  }

  inventarioTableBody.innerHTML = filtered
    .map((item) => {
      const critical = isCritical(item);
      const stock = getStock(item);
      const umbral = getUmbral(item);
      return `
      <tr>
        <td>${escapeHtml(getProductoCodigo(item))}</td>
        <td>${escapeHtml(getProductoNombre(item))}</td>
        <td>${stock}</td>
        <td>${umbral}</td>
        <td><span class="stock-pill ${critical ? "stock-pill--critical" : "stock-pill--ok"}">${critical ? "Stock bajo" : "Normal"}</span></td>
        <td>${escapeHtml(formatDateTime(item?.actualizado_en || item?.updated_at || item?.updatedAt))}</td>
      </tr>
    `;
    })
    .join("");

  renderSummary();
}

function renderMovimientos() {
  if (!movimientosCache.length) {
    movimientosTableBody.innerHTML =
      '<tr><td class="empty-state" colspan="6">No hay movimientos registrados.</td></tr>';
    renderSummary();
    return;
  }

  movimientosTableBody.innerHTML = movimientosCache
    .map((item) => {
      const tipo = String(item?.tipo || item?.tipo_movimiento || "AJUSTE").toUpperCase();
      const cssType =
        tipo === "ENTRADA"
          ? "movement-pill--entrada"
          : tipo === "SALIDA"
            ? "movement-pill--salida"
            : "movement-pill--ajuste";

      return `
      <tr>
        <td>${escapeHtml(formatDateTime(item?.fecha || item?.created_at || item?.creado_en))}</td>
        <td>${escapeHtml(getProductoNombre(item))}</td>
        <td><span class="movement-pill ${cssType}">${escapeHtml(tipo)}</span></td>
        <td>${escapeHtml(item?.cantidad ?? item?.delta ?? 0)}</td>
        <td>${escapeHtml(item?.usuario_nombre || item?.usuario_id || "-")}</td>
        <td>${escapeHtml(item?.motivo || item?.detalle || "-")}</td>
      </tr>
    `;
    })
    .join("");

  renderSummary();
}

function populateSedes() {
  const roleId = getRoleId();
  const currentSedeId = getCurrentSedeId();
  const isAdmin = roleId === 1;

  const sedeOptions = isAdmin
    ? sedesCache
    : sedesCache.filter((item) => Number(item.id) === Number(currentSedeId));

  filterSede.innerHTML = isAdmin
    ? '<option value="">Todas / seleccionar</option>'
    : '<option value="">Mi sede</option>';

  entradaSede.innerHTML = '<option value="">Seleccionar sede</option>';

  sedeOptions.forEach((sede) => {
    const optionFilter = document.createElement("option");
    optionFilter.value = String(sede.id);
    optionFilter.textContent = sede.nombre;
    filterSede.appendChild(optionFilter);

    const optionModal = document.createElement("option");
    optionModal.value = String(sede.id);
    optionModal.textContent = sede.nombre;
    entradaSede.appendChild(optionModal);
  });

  if (currentSedeId) {
    if (!isAdmin) {
      filterSede.value = String(currentSedeId);
    }
    entradaSede.value = String(currentSedeId);
  } else if (isAdmin && sedesCache.length) {
    filterSede.value = "";
    entradaSede.value = String(sedesCache[0].id);
  }

  filterSede.disabled = !isAdmin;
  entradaSede.disabled = !isAdmin && Boolean(currentSedeId);
}

function populateProductos() {
  entradaProducto.innerHTML = '<option value="">Seleccionar producto</option>';
  productosCache.forEach((producto) => {
    const option = document.createElement("option");
    option.value = String(producto.id);
    option.textContent = `${producto.codigo || `PROD-${producto.id}`} · ${producto.nombre}`;
    entradaProducto.appendChild(option);
  });
}

async function loadSedes() {
  sedesCache = [];

  for (const url of SEDES_URLS) {
    try {
      const payload = await apiRequest(url);
      const lista = getList(payload);
      if (lista.length) {
        sedesCache = lista;
        break;
      }
    } catch {
      // seguimos probando la siguiente ruta
    }
  }

  // fallback para cajero/admin con sede guardada
  if (!sedesCache.length) {
    const currentSedeId = getCurrentSedeId();
    if (currentSedeId) {
      sedesCache = [{ id: currentSedeId, nombre: `Sede ${currentSedeId}` }];
    }
  }

  populateSedes();

  if (!sedesCache.length) {
    showAlert("No fue posible cargar las sedes.");
  }
}

async function loadProductos() {
  try {
    productosCache = getList(await apiRequest(PRODUCTOS_URL));
  } catch (error) {
    productosCache = [];
    showAlert(`No fue posible cargar productos: ${error.message}`);
  }
  populateProductos();
}

async function loadInventario() {
  inventarioTableBody.innerHTML = '<tr><td class="empty-state" colspan="6">Cargando inventario...</td></tr>';

  try {
    const params = new URLSearchParams();
    const roleId = getRoleId();
    const sedeId = filterSede.value || getCurrentSedeId();

    if (roleId === 1 && !sedeId) {
      inventarioCache = [];
      inventarioTableBody.innerHTML =
        '<tr><td class="empty-state" colspan="6">Selecciona una sede para consultar el inventario.</td></tr>';
      renderSummary();
      return;
    }

    if (sedeId) params.set("sede_id", sedeId);

    const payload = await apiRequest(
      `${INVENTARIO_URL}${params.toString() ? `?${params.toString()}` : ""}`
    );
    inventarioCache = getList(payload);
    renderInventario();
  } catch (error) {
    inventarioCache = [];
    inventarioTableBody.innerHTML = `<tr><td class="empty-state" colspan="6">${escapeHtml(error.message)}</td></tr>`;
    renderSummary();
  }
}

async function loadMovimientos() {
  movimientosTableBody.innerHTML = '<tr><td class="empty-state" colspan="6">Cargando movimientos...</td></tr>';
  try {
    const params = new URLSearchParams();
    const sedeId = filterSede.value || getCurrentSedeId();
    if (sedeId) params.set("sede_id", sedeId);

    const payload = await apiRequest(
      `${INVENTARIO_MOVIMIENTOS_URL}${params.toString() ? `?${params.toString()}` : ""}`
    );
    movimientosCache = getList(payload);
    renderMovimientos();
  } catch (error) {
    movimientosCache = [];
    movimientosTableBody.innerHTML = `<tr><td class="empty-state" colspan="6">${escapeHtml(error.message)}</td></tr>`;
    renderSummary();
  }
}

function openModal() {
  populateSedes();
  entradaModal.classList.add("is-open");
  entradaModal.setAttribute("aria-hidden", "false");

  const currentSedeId = getCurrentSedeId();
  if (currentSedeId) {
    entradaSede.value = String(currentSedeId);
  } else if (getRoleId() === 1 && sedesCache.length) {
    entradaSede.value = String(sedesCache[0].id);
  }
}

function closeModal() {
  entradaModal.classList.remove("is-open");
  entradaModal.setAttribute("aria-hidden", "true");
  entradaForm.reset();

  if (getCurrentSedeId()) {
    entradaSede.value = String(getCurrentSedeId());
  }
}

async function submitEntrada(event) {
  event.preventDefault();

  const sede_id = Number(entradaSede.value || getCurrentSedeId());
  const producto_id = Number(entradaProducto.value);
  const cantidad = Number(entradaCantidad.value);

  const payload = {
    producto_id,
    cantidad,
    motivo: entradaForm.motivo.value.trim() || null,
  };

  if (entradaUmbral.value !== "") {
    payload.umbral_minimo = Number(entradaUmbral.value);
  }

  if (!sede_id || !payload.producto_id || !payload.cantidad) {
    showAlert("Completa sede, producto y cantidad.");
    return;
  }

  try {
    const result = await apiRequest(`${INVENTARIO_ENTRADAS_URL}?sede_id=${sede_id}`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showAlert(result?.message || "Entrada registrada correctamente.", "success");
    closeModal();
    await Promise.all([loadInventario(), loadMovimientos()]);
  } catch (error) {
    showAlert(error.message);
  }
}

function guardRoleAccess() {
  const roleId = getRoleId();
  if (![1, 2].includes(roleId)) {
    showAlert("Este modulo solo esta disponible para Cajero y Admin.");
    if (openEntradaModalBtn) openEntradaModalBtn.disabled = true;
    const submitBtn = entradaForm?.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;
  }
}

async function init() {
  if (!authToken) return;
  guardRoleAccess();
  await Promise.all([loadSedes(), loadProductos()]);
  await Promise.all([loadInventario(), loadMovimientos()]);
}

filterSede?.addEventListener("change", async () => {
  await Promise.all([loadInventario(), loadMovimientos()]);
});
filterTexto?.addEventListener("input", renderInventario);
filterCritico?.addEventListener("change", renderInventario);
openEntradaModalBtn?.addEventListener("click", openModal);
closeEntradaModalBtn?.addEventListener("click", closeModal);
cancelEntradaModalBtn?.addEventListener("click", closeModal);
refreshInventarioBtn?.addEventListener("click", async () => {
  await Promise.all([loadInventario(), loadMovimientos()]);
  showAlert("Inventario actualizado.", "success");
});
entradaModal?.addEventListener("click", (event) => {
  if (event.target === entradaModal) closeModal();
});
entradaForm?.addEventListener("submit", submitEntrada);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && entradaModal?.classList.contains("is-open")) {
    closeModal();
  }
});

init();