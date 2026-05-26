const AUTH_TOKEN_KEYS = ["access_token", "token", "jwt", "authToken"];
const AUTH_REDIRECT_URL = "index.html";
const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes
const WARNING_TIMEOUT_MS = 29 * 60 * 1000;    // Show warning after 29 minutes

let warningTimer = null;
let logoutTimer = null;
let isWarningModalOpen = false;

// Inject warning modal styling dynamically
if (typeof document !== "undefined") {
  const style = document.createElement("style");
  style.textContent = `
    .rb-timeout-overlay {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.7); display: flex; align-items: center; justify-content: center;
      z-index: 99999; backdrop-filter: blur(4px); transition: opacity 0.3s ease;
    }
    .rb-timeout-modal {
      background: var(--bg-card, #ffffff); border-radius: 16px; width: 90%; max-width: 440px;
      padding: 28px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2); text-align: center;
      border: 1px solid rgba(226, 232, 240, 0.8); animation: rbPop 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .rb-timeout-title { font-size: 1.3rem; font-weight: 700; color: #ef4444; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; }
    .rb-timeout-desc { font-size: 0.95rem; line-height: 1.5; color: var(--text-muted, #64748b); margin-bottom: 24px; }
    .rb-timeout-buttons { display: flex; gap: 12px; justify-content: center; }
    .rb-timeout-btn {
      padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; border: none; font-size: 0.9rem; transition: all 0.2s ease;
    }
    .rb-timeout-btn--keep { background: #2563eb; color: white; }
    .rb-timeout-btn--keep:hover { background: #1d4ed8; }
    .rb-timeout-btn--logout { background: #f1f5f9; color: #475569; }
    .rb-timeout-btn--logout:hover { background: #e2e8f0; }
    @keyframes rbPop {
      from { transform: scale(0.95); opacity: 0; }
      to { transform: scale(1); opacity: 1; }
    }
  `;
  document.head.appendChild(style);
}

function getStoredAuthToken() {
  for (const key of AUTH_TOKEN_KEYS) {
    const token = sessionStorage.getItem(key);
    if (token) {
      return token.replace(/^Bearer\s+/i, "");
    }
  }
  return null;
}

function logout() {
  // Guarantee in-progress orders are saved by calling a callback or letting the page manage draft carts
  sessionStorage.clear();
  window.location.href = AUTH_REDIRECT_URL;
}

function showWarningModal() {
  if (isWarningModalOpen) return;
  isWarningModalOpen = true;

  const overlay = document.createElement("div");
  overlay.className = "rb-timeout-overlay";
  overlay.id = "rbTimeoutModalOverlay";

  overlay.innerHTML = `
    <div class="rb-timeout-modal">
      <div class="rb-timeout-title">
        ⚠️ Alerta de Inactividad
      </div>
      <div class="rb-timeout-desc">
        Tu sesion expirara en menos de 1 minuto debido a inactividad. ¿Deseas mantener tu sesion abierta y continuar trabajando?
      </div>
      <div class="rb-timeout-buttons">
        <button type="button" class="rb-timeout-btn rb-timeout-btn--logout" id="rbBtnLogoutNow">Cerrar Sesion</button>
        <button type="button" class="rb-timeout-btn rb-timeout-btn--keep" id="rbBtnKeepActive">Mantener Activa</button>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  document.getElementById("rbBtnKeepActive").addEventListener("click", () => {
    overlay.remove();
    isWarningModalOpen = false;
    resetInactivityTimer();
  });

  document.getElementById("rbBtnLogoutNow").addEventListener("click", () => {
    overlay.remove();
    isWarningModalOpen = false;
    logout();
  });

  // Final 1-minute countdown to force log-out if they don't interact
  clearTimeout(logoutTimer);
  logoutTimer = setTimeout(() => {
    if (isWarningModalOpen) {
      overlay.remove();
      isWarningModalOpen = false;
      logout();
    }
  }, 60 * 1000);
}

function resetInactivityTimer() {
  if (isWarningModalOpen) return; // Do not reset while modal is asking user

  clearTimeout(warningTimer);
  clearTimeout(logoutTimer);

  warningTimer = setTimeout(() => {
    showWarningModal();
  }, WARNING_TIMEOUT_MS);
}

function startInactivityWatch() {
  const events = ["mousemove", "mousedown", "keydown", "touchstart", "scroll"];
  events.forEach((evt) => document.addEventListener(evt, resetInactivityTimer));
  resetInactivityTimer();
}

function requireAuth() {
  const token = getStoredAuthToken();
  if (!token) {
    window.location.href = AUTH_REDIRECT_URL;
    return null;
  }

  startInactivityWatch();
  return token;
}

// Persist cart draft per user to ensure state safety across unexpected logouts/expirations
function saveDraftCart(items) {
  const correo = sessionStorage.getItem("correo") || "global";
  localStorage.setItem(`RutaByte_DraftCart_${correo}`, JSON.stringify(items));
}

function getDraftCart() {
  const correo = sessionStorage.getItem("correo") || "global";
  try {
    const data = localStorage.getItem(`RutaByte_DraftCart_${correo}`);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

function clearDraftCart() {
  const correo = sessionStorage.getItem("correo") || "global";
  localStorage.removeItem(`RutaByte_DraftCart_${correo}`);
}

window.RutaByteAuthGuard = {
  getStoredAuthToken,
  requireAuth,
  logout,
  saveDraftCart,
  getDraftCart,
  clearDraftCart,
};