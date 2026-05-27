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
      (payload && typeof payload === "object" && (Array.isArray(payload.detail) ? payload.detail.map(d => d.msg).join("; ") : (payload.detail || payload.message))) ||
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
      notas: "",
    });
  }
  renderCarrito();
  window.RutaByteAuthGuard.saveDraftCart(carrito);
}

function removeFromCart(productoId) {
  carrito = carrito.filter((c) => c.producto_id !== productoId);
  renderCarrito();
  window.RutaByteAuthGuard.saveDraftCart(carrito);
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
  window.RutaByteAuthGuard.saveDraftCart(carrito);
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
        <div class="carrito-item" style="border-bottom: 1px solid var(--border-color, #e2e8f0); padding-bottom: 10px; margin-bottom: 10px;">
          <div class="carrito-info" style="flex: 1;">
            <strong>${escapeHtml(item.nombre)}</strong>
            <div style="font-size: 0.85rem; color: var(--text-muted, #64748b);">${formatPrice(item.precio)} x ${item.cantidad} = ${formatPrice(subtotal)}</div>
            
            <!-- Notes input with 150 limit -->
            <input
              type="text"
              class="carrito-item-nota"
              data-id="${item.producto_id}"
              placeholder="Nota especial (máx 150 caracteres)"
              value="${escapeHtml(item.notas || '')}"
              maxlength="150"
              style="width: 95%; margin-top: 6px; padding: 4px 8px; font-size: 0.8rem; border: 1px solid #cbd5e1; border-radius: 6px;"
            />
          </div>
          <div class="carrito-controls" style="display: flex; align-items: center; gap: 8px;">
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
      notas: c.notas || null,
    }));

    await apiRequest(PEDIDOS_URL, {
      method: "POST",
      body: JSON.stringify({ mesa_id, items }),
    });

    showAlert("Pedido creado correctamente.", "success");
    carrito = [];
    renderCarrito();
    window.RutaByteAuthGuard.clearDraftCart(); // Clear draft cart upon successful submission!
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
        const puedeAvanzar = estado !== "ENTREGADO" && estado !== "PAGADO" && estado !== "CANCELADO";
        const siguiente = estado === "EN_PREPARACION" ? "Marcar Listo" : estado === "LISTO" ? "Marcar Entregado" : "";
        const canTransfer = estado !== "PAGADO" && estado !== "CANCELADO";
        return `
          <tr>
            <td>${p.id}</td>
            <td>${escapeHtml(getMesaIdentificador(p.mesa_id))}</td>
            <td><span class="${ESTADO_CLASSES[estado] || "tag"}">${ESTADO_LABELS[estado] || estado}</span></td>
            <td>${new Date(p.creado_en).toLocaleString("es-CO")}</td>
            <td>
              <button class="table-action btn-ghost" type="button" data-action="toggle-detalle" data-id="${p.id}">Ver detalles</button>
              ${puedeAvanzar ? `<button class="table-action table-action--success" type="button" data-action="avanzar" data-id="${p.id}" style="margin-left: 5px;">${siguiente}</button>` : '<span class="tag tag--inactive" style="margin-left: 5px;">Finalizado</span>'}
              ${canTransfer ? `<button class="table-action" type="button" data-action="open-transferir" data-id="${p.id}" style="margin-left: 5px; background: var(--accent); color: white; border: none; border-radius: 8px; padding: 4px 8px; font-size: 0.8rem; font-weight: bold; cursor: pointer;">Transferir Mesa</button>` : ""}
            </td>
          </tr>
          <tr id="detalle-row-${p.id}" style="display: none; background: var(--surface-soft);">
            <td colspan="5">
              <div id="detalle-content-${p.id}" style="padding: 1rem; display: grid; gap: 0.5rem; border: 1px solid var(--border); border-radius: 12px; font-size: 0.9rem;">
                Cargando detalles...
              </div>
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

async function toggleDetalles(pedidoId) {
  const row = document.getElementById(`detalle-row-${pedidoId}`);
  const content = document.getElementById(`detalle-content-${pedidoId}`);
  
  if (row.style.display === "none") {
    row.style.display = "table-row";
    content.innerHTML = "<div>Cargando detalles...</div>";
    
    try {
      const pedido = await apiRequest(`${PEDIDOS_URL}/${pedidoId}`);
      if (!pedido.detalles || !pedido.detalles.length) {
        content.innerHTML = "<div>El pedido no contiene ítems.</div>";
        return;
      }
      
      let html = `
        <div style="font-weight: bold; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
          <span>Detalle de Ítems (Pedido #${pedidoId})</span>
          ${parseFloat(pedido.descuento || 0) > 0 ? `<span style="color: #16a34a; font-weight: bold;">Descuento: ${formatPrice(pedido.descuento)} (${pedido.tipo_descuento === 'PORCENTAJE' ? pedido.descuento_valor + '%' : '$' + pedido.descuento_valor})</span>` : ""}
        </div>
        <table style="width: 100%; border-collapse: collapse;">
          <thead>
            <tr style="text-align: left; font-size: 0.8rem; color: var(--muted); border-bottom: 1px solid var(--border);">
              <th style="padding: 0.5rem;">PRODUCTO</th>
              <th style="padding: 0.5rem;">CANTIDAD</th>
              <th style="padding: 0.5rem;">PRECIO</th>
              <th style="padding: 0.5rem;">NOTAS</th>
              <th style="padding: 0.5rem; text-align: right;">ACCIONES</th>
            </tr>
          </thead>
          <tbody>
      `;
      
      pedido.detalles.forEach((d) => {
        const prod = productosCache.find(p => p.id === d.producto_id);
        const name = prod ? prod.nombre : `Producto ID ${d.producto_id}`;
        const canCancelItem = !d.cancelado && pedido.estado !== "PAGADO" && pedido.estado !== "CANCELADO";
        
        html += `
          <tr style="border-bottom: 1px solid rgba(0,0,0,0.05); ${d.cancelado ? 'opacity: 0.5; text-decoration: line-through;' : ''}">
            <td style="padding: 0.5rem; font-weight: 500;">${escapeHtml(name)}</td>
            <td style="padding: 0.5rem;">${d.cantidad}</td>
            <td style="padding: 0.5rem;">${formatPrice(d.precio_unitario)}</td>
            <td style="padding: 0.5rem; font-style: italic; color: var(--muted);">${escapeHtml(d.notas || '-')}</td>
            <td style="padding: 0.5rem; text-align: right;">
              ${canCancelItem ? `<button class="table-action table-action--danger" type="button" data-action="anular-item" data-pedido-id="${pedidoId}" data-detalle-id="${d.id}" style="color: #ef4444; border: 1px solid #ef4444; border-radius: 6px; padding: 2px 6px; font-size: 0.8rem; font-weight: bold; cursor: pointer; background: transparent;">Anular</button>` : ""}
              ${d.cancelado ? `<span style="color: #ef4444; font-weight: bold; font-size: 0.8rem;">[ANULADO] ${escapeHtml(d.justificacion_cancelacion || '')}</span>` : ""}
            </td>
          </tr>
        `;
      });
      
      html += `
          </tbody>
        </table>
      `;
      content.innerHTML = html;
    } catch (error) {
      content.innerHTML = `<div style="color: #ef4444;">Error al cargar detalles: ${escapeHtml(error.message)}</div>`;
    }
  } else {
    row.style.display = "none";
  }
}

async function anularItem(pedidoId, detalleId) {
  const justificacion = window.prompt("Escriba la justificación detallada para anular este producto:");
  if (justificacion === null) return; // User cancelled
  
  if (!justificacion.trim()) {
    showAlert("Debe ingresar una justificación escrita válida.");
    return;
  }
  
  try {
    await apiRequest(`${PEDIDOS_URL}/${pedidoId}/detalles/${detalleId}/cancelar`, {
      method: "POST",
      body: JSON.stringify({ justificacion })
    });
    
    showAlert("Ítem anulado y notificado a cocina.", "success");
    
    // Force refresh the expanded details
    const row = document.getElementById(`detalle-row-${pedidoId}`);
    row.style.display = "none";
    await toggleDetalles(pedidoId);
    await loadPedidos();
  } catch (error) {
    showAlert(error.message);
  }
}

function openTransferirMesa(pedidoId) {
  document.getElementById("transferirPedidoId").value = pedidoId;
  
  const targetSelect = document.getElementById("mesa_destino_id");
  targetSelect.innerHTML = '<option value="">Seleccionar mesa libre</option>';
  
  const freeMesas = mesasCache.filter(m => m.estado === "LIBRE" && m.activa);
  if (!freeMesas.length) {
    showAlert("No hay mesas libres disponibles en tu sede para transferir.");
    return;
  }
  
  freeMesas.forEach(m => {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = m.identificador_mesa;
    targetSelect.appendChild(opt);
  });
  
  document.getElementById("transferirModal").classList.add("modal--open");
}

document.getElementById("closeTransferirModalBtn")?.addEventListener("click", () => {
  document.getElementById("transferirModal").classList.remove("modal--open");
});
document.getElementById("cancelTransferirModalBtn")?.addEventListener("click", () => {
  document.getElementById("transferirModal").classList.remove("modal--open");
});

document.getElementById("transferirForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const pedidoId = document.getElementById("transferirPedidoId").value;
  const mesa_destino_id = document.getElementById("mesa_destino_id").value;
  
  try {
    const response = await apiRequest(`${PEDIDOS_URL}/${pedidoId}/transferir?mesa_destino_id=${mesa_destino_id}`, {
      method: "POST"
    });
    
    showAlert(response.message, "success");
    document.getElementById("transferirModal").classList.remove("modal--open");
    await loadMesas();
    await loadPedidos();
  } catch (error) {
    showAlert(error.message);
  }
});

// ── WebSocket notifications ───────────────────────────────────

function showLiveNotification(message) {
  const toast = document.createElement("div");
  toast.style.cssText = `
    position: fixed; top: 20px; right: 20px; background: #0f172a; color: white;
    padding: 16px 20px; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
    z-index: 100000; max-width: 320px; border-left: 4px solid #3b82f6;
    font-family: sans-serif; font-size: 0.9rem; line-height: 1.4;
    animation: rbSlideIn 0.3s ease forwards;
  `;
  toast.innerHTML = `
    <div style="font-weight: bold; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
      🔔 Notificación en Tiempo Real
    </div>
    <div>${escapeHtml(message)}</div>
  `;
  
  if (!document.getElementById("rbToastAnimation")) {
    const animStyle = document.createElement("style");
    animStyle.id = "rbToastAnimation";
    animStyle.textContent = `
      @keyframes rbSlideIn {
        from { transform: translateX(120%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
      }
    `;
    document.head.appendChild(animStyle);
  }
  
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = "rbSlideIn 0.3s ease reverse forwards";
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

function startWebSocket() {
  const WS_URL = API_BASE_URL.replace(/^http/, "ws") + "/ws/pedidos";
  const ws = new WebSocket(WS_URL);
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (["NUEVO_PEDIDO", "CAMBIO_ESTADO_PEDIDO", "ANULACION_ITEM", "TRANSFERENCIA_PEDIDO", "PAGO_PROCESADO"].includes(data.evento)) {
        showLiveNotification(data.mensaje || `Evento: ${data.evento}`);
        void loadMesas();
        void loadPedidos();
      }
    } catch (err) {
      console.error("[WebSocket] Error parsing message:", err);
    }
  };

  ws.onclose = () => {
    console.log("[WebSocket] Connection closed. Retrying in 5 seconds...");
    setTimeout(startWebSocket, 5000);
  };

  ws.onerror = (err) => {
    console.error("[WebSocket] Error occurred:", err);
  };
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

// Event listener for note changes
pedidoItems.addEventListener("input", (e) => {
  if (e.target.classList.contains("carrito-item-nota")) {
    const id = Number(e.target.dataset.id);
    const item = carrito.find((c) => c.producto_id === id);
    if (item) {
      item.notas = e.target.value;
      window.RutaByteAuthGuard.saveDraftCart(carrito); // Instantly save draft cart
    }
  }
});

pedidosTableBody.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;
  
  const action = btn.dataset.action;
  const id = Number(btn.dataset.id);
  
  if (action === "avanzar") {
    void avanzarEstado(id);
  } else if (action === "toggle-detalle") {
    void toggleDetalles(id);
  } else if (action === "open-transferir") {
    openTransferirMesa(id);
  } else if (action === "anular-item") {
    const pedidoId = Number(btn.dataset.pedidoId);
    const detalleId = Number(btn.dataset.detalleId);
    void anularItem(pedidoId, detalleId);
  }
});

categoriaFilter.addEventListener("change", renderProductos);
confirmarBtn.addEventListener("click", confirmarPedido);

if (authToken) {
  // Load draft cart if available!
  carrito = window.RutaByteAuthGuard.getDraftCart() || [];
  
  void Promise.all([loadMesas(), loadCategorias(), loadProductos()]).then(() => {
    renderCarrito();
    void loadPedidos();
    startWebSocket();
  });
}
