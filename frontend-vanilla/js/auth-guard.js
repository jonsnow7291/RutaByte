const AUTH_TOKEN_KEYS = ["access_token", "token", "jwt", "authToken"];
const AUTH_REDIRECT_URL = "/frontend-vanilla/index.html";
const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000;

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
  window.location.href = AUTH_REDIRECT_URL;
}

function resetInactivityTimer() {
  clearTimeout(inactivityTimer);
  inactivityTimer = setTimeout(() => {
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

  console.log("requireAuth token:", token);
  console.log("session access_token:", sessionStorage.getItem("access_token"));
  console.log("current url:", window.location.href);

  if (!token) {
    window.location.href = AUTH_REDIRECT_URL;
    return null;
  }

  startInactivityWatch();
  return token;
}

window.RutaByteAuthGuard = {
  getStoredAuthToken,
  requireAuth,
  logout,
};