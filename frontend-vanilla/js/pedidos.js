const API_BASE_URL =
  window.RUTABYTE_API_BASE_URL ||
  document.body?.dataset.apiBaseUrl ||
  "http://127.0.0.1:8000";
const PEDIDOS_URL = `${API_BASE_URL.replace(/\/$/, "")}/mesero/pedidos`;
const PRODUCTOS_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/productos`;
const CATEGORIAS_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/categorias`;
const MESAS_URL = `${API_BASE_URL.replace(/\/$/, "")}/api/mesas`;

const alertSlot = document.getElementById("alertSlot");
const mesaSelect = document.getElementById("mesa_id");
const categoriaFilter = document.getElementById("categoria_filter");
const productosGrid = document.getElementById("productosGrid");
const pedidoItems = document.getElementById("pedidoItems");
const pedidoTotalEl = document.getElementById("pedidoTotal");
const confirmarBtn = document.getElementById("confirmarPedidoBtn");
const pedidosTableBody = document.getElementById("pedidosTableBody");

const authToken = window.RutaByteAuthGuard?.requireAuth?.();

let productosCache = [];
let categoriasCache = [];
let mesasCache = [];
let carrito = []; // { producto_id, nombre, precio, cantidad, notas }

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
    if (alertSlot.contains(alert)) alert.remove();
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

function formatPrice(value) {
  return Number(value).toLocaleString("es-CO", { style: "currency", currency: "COP", minimumFractionDigits: 0 });
}

async function apiRequest(url, options = {}) {
  const token = getToken();
  if (!token) throw new Error("No se encontro un JWT.");

  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, { ...options, headers });
  const ct = response.headers.get("content-type") || "";
  const payload = ct.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      (payload && typeof payload === "object" && (payload.detail || payload.message)) ||
      `Error HTTP ${response.status}`;
    throw new Error(message);
  }
  return payload;
}

function getList(payload) {
  if (Array.isArray(payload)) return payload;
  const containers = [payload?.data, payload?.items, payload?.result];
  for (const c of containers) {
    if (Array.isArray(c)) return c;
  }
  return [];
}

// ── Carga de datos ─────────────────────────────────────────

async function loadMesas() {
  try {
    mesasCache = getList(await apiRequest(MESAS_URL));
    mesaSelect.innerHTML = '<option value="">Seleccionar mesa</option>';
    mesasCache.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = `${m.identificador_mesa} (${m.estado})`;
      mesaSelect.appendChild(opt);
    });
  } catch { mesasCache = []; }
}

async function loadCategorias() {
  try {
    categoriasCache = getList(await apiRequest(CATEGORIAS_URL));
    categoriaFilter.innerHTML = '<option value="">Todas</option>';
    categoriasCache.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.id;
      opt.textContent = c.nombre;
      categoriaFilter.appendChild(opt);
    });
  } catch { categoriasCache = []; }
}

async function loadProductos() {
  try {
    productosCache = getList(await apiRequest(PRODUCTOS_URL));
    renderProductos();
  } catch { productosCache = []; }
}

function getCategoriaNombre(catId) {
  const cat = categoriasCache.find((c) => c.id === catId);
  return cat ? cat.nombre : "";
}

function renderProductos() {
  const filtro = categoriaFilter.value;
  const lista = filtro
    ? productosCache.filter((p) => String(p.categoria_id) === filtro)
    : productosCache;

  if (!lista.length) {
    productosGrid.innerHTML = '<p class="empty-state">No hay productos disponibles.</p>';
    return;
  }

  productosGrid.innerHTML = lista
    .map(
      (p) => `
        <button class="producto-card" type="button" data-id="${p.id}">
          <span class="producto-nombre">${escapeHtml(p.nombre)}</span>
          <span class="producto-cat">${escapeHtml(getCategoriaNombre(p.categoria_id))}</span>
          <span class="producto-precio">${formatPrice(p.precio)}</span>
        </button>
      `
    )
    .join("");
}

// ── Carrito ────────────────────────────────────────────────

function addToCart(productoId) {
  const producto = productosCache.find((p) => p.id === productoId);
  if (!producto) return;

  const existing = carrito.find((c) => c.producto_id === productoId);
  if (existing) {
    existing.cantidad += 1;
  } else {
    carrito.push({
      producto_id: producto.id,
      nombre: producto.nombre,
      precio: Number(producto.precio),
      cantidad: 1,
      notas: null,
    });
  }
  renderCarrito();
}

function removeFromCart(productoId) {
  carrito = carrito.filter((c) => c.producto_id !== productoId);
  renderCarrito();
}

function updateQuantity(productoId, delta) {
  const item = carrito.find((c) => c.producto_id === productoId);
  if (!item) return;
  item.cantidad += delta;
  if (item.cantidad <= 0) {
    removeFromCart(productoId);
    return;
  }
  renderCarrito();
}

function renderCarrito() {
  if (!carrito.length) {
    pedidoItems.innerHTML = '<p class="empty-state">Agrega productos al pedido.</p>';
    pedidoTotalEl.textContent = "$0";
    confirmarBtn.disabled = true;
    return;
  }

  let total = 0;
  pedidoItems.innerHTML = carrito
    .map((item) => {
      const subtotal = item.precio * item.cantidad;
      total += subtotal;
      return `
        <div class="carrito-item">
          <div class="carrito-info">
            <strong>${escapeHtml(item.nombre)}</strong>
            <span>${formatPrice(item.precio)} x ${item.cantidad} = ${formatPrice(subtotal)}</span>
          </div>
          <div class="carrito-controls">
            <button type="button" class="qty-btn" data-action="minus" data-id="${item.producto_id}">−</button>
            <span>${item.cantidad}</span>
            <button type="button" class="qty-btn" data-action="plus" data-id="${item.producto_id}">+</button>
            <button type="button" class="qty-btn qty-btn--remove" data-action="remove" data-id="${item.producto_id}">✕</button>
          </div>
        </div>
      `;
    })
    .join("");

  pedidoTotalEl.textContent = formatPrice(total);
  confirmarBtn.disabled = false;
}

// ── Crear pedido ───────────────────────────────────────────

async function confirmarPedido() {
  const mesa_id = Number(mesaSelect.value);
  if (!mesa_id) {
    showAlert("Selecciona una mesa.");
    return;
  }
  if (!carrito.length) {
    showAlert("Agrega al menos un producto.");
    return;
  }

  confirmarBtn.disabled = true;
  confirmarBtn.textContent = "Enviando...";

  try {
    const items = carrito.map((c) => ({
      producto_id: c.producto_id,
      cantidad: c.cantidad,
      notas: c.notas,
    }));

    await apiRequest(PEDIDOS_URL, {
      method: "POST",
      body: JSON.stringify({ mesa_id, items }),
    });

    showAlert("Pedido creado correctamente.", "success");
    carrito = [];
    renderCarrito();
    await loadMesas();
    await loadPedidos();
  } catch (error) {
    showAlert(error.message);
  } finally {
    confirmarBtn.disabled = false;
    confirmarBtn.textContent = "Confirmar Pedido";
  }
}

// ── Lista de pedidos ───────────────────────────────────────

const ESTADO_LABELS = {
  EN_PREPARACION: "En preparacion",
  LISTO: "Listo",
  ENTREGADO: "Entregado",
};

const ESTADO_CLASSES = {
  EN_PREPARACION: "tag tag--warning",
  LISTO: "tag tag--active",
  ENTREGADO: "tag tag--inactive",
};

function getMesaIdentificador(mesaId) {
  const mesa = mesasCache.find((m) => m.id === mesaId);
  return mesa ? mesa.identificador_mesa : String(mesaId);
}

async function loadPedidos() {
  if (!authToken) return;
  try {
    pedidosTableBody.innerHTML = '<tr><td class="empty-state" colspan="5">Cargando pedidos...</td></tr>';
    const pedidos = getList(await apiRequest(PEDIDOS_URL));

    if (!pedidos.length) {
      pedidosTableBody.innerHTML = '<tr><td class="empty-state" colspan="5">No hay pedidos todavia.</td></tr>';
      return;
    }

    pedidosTableBody.innerHTML = pedidos
      .map((p) => {
        const estado = p.estado || "EN_PREPARACION";
        const puedeAvanzar = estado !== "ENTREGADO";
        const siguiente = estado === "EN_PREPARACION" ? "Marcar Listo" : estado === "LISTO" ? "Marcar Entregado" : "";
        return `
          <tr>
            <td>${p.id}</td>
            <td>${escapeHtml(getMesaIdentificador(p.mesa_id))}</td>
            <td><span class="${ESTADO_CLASSES[estado] || "tag"}">${ESTADO_LABELS[estado] || estado}</span></td>
            <td>${new Date(p.creado_en).toLocaleString("es-CO")}</td>
            <td>
              ${puedeAvanzar ? `<button class="table-action table-action--success" type="button" data-action="avanzar" data-id="${p.id}">${siguiente}</button>` : '<span class="tag tag--inactive">Finalizado</span>'}
            </td>
          </tr>
        `;
      })
      .join("");
  } catch (error) {
    pedidosTableBody.innerHTML = '<tr><td class="empty-state" colspan="5">Error al cargar pedidos.</td></tr>';
    showAlert(error.message);
  }
}

async function avanzarEstado(pedidoId) {
  try {
    const result = await apiRequest(`${PEDIDOS_URL}/${pedidoId}/estado`, { method: "PATCH" });
    showAlert(result.message, "success");
    await loadMesas();
    await loadPedidos();
  } catch (error) {
    showAlert(error.message);
  }
}

// ── Eventos ────────────────────────────────────────────────

productosGrid.addEventListener("click", (e) => {
  const card = e.target.closest(".producto-card");
  if (!card) return;
  addToCart(Number(card.dataset.id));
});

pedidoItems.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  const id = Number(btn.dataset.id);
  if (btn.dataset.action === "plus") updateQuantity(id, 1);
  else if (btn.dataset.action === "minus") updateQuantity(id, -1);
  else if (btn.dataset.action === "remove") removeFromCart(id);
});

pedidosTableBody.addEventListener("click", (e) => {
  const btn = e.target.closest('[data-action="avanzar"]');
  if (!btn) return;
  void avanzarEstado(Number(btn.dataset.id));
});

categoriaFilter.addEventListener("change", renderProductos);
confirmarBtn.addEventListener("click", confirmarPedido);

if (authToken) {
  void Promise.all([loadMesas(), loadCategorias(), loadProductos()]).then(() => loadPedidos());
}
