const AUTH_TOKEN_KEYS = ["access_token", "token", "jwt", "authToken"];
const AUTH_REDIRECT_URL = "index.html";
const INACTIVITY_TIMEOUT_MS = 60 * 1000; // 1 minuto

let inactivityTimer = null;

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
  sessionStorage.clear();
  window.location.replace(AUTH_REDIRECT_URL);
}

function resetInactivityTimer() {
  clearTimeout(inactivityTimer);
  inactivityTimer = setTimeout(() => {
    alert("Tu sesion ha expirado por inactividad.");
    logout();
  }, INACTIVITY_TIMEOUT_MS);
}

function startInactivityWatch() {
  const events = ["mousemove", "mousedown", "keydown", "touchstart", "scroll"];
  events.forEach((evt) => document.addEventListener(evt, resetInactivityTimer));
  resetInactivityTimer();
}

function requireAuth() {
  const token = getStoredAuthToken();
  if (!token) {
    window.location.replace(AUTH_REDIRECT_URL);
    return null;
  }

  startInactivityWatch();
  return token;
}

window.RutaByteAuthGuard = {
  getStoredAuthToken,
  requireAuth,
};
