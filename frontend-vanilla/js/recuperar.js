const API_BASE_URL = window.RUTABYTE_API_BASE_URL || "http://127.0.0.1:8000";

const solicitarForm = document.getElementById("solicitarForm");
const resetForm = document.getElementById("resetForm");
const solicitarMsg = document.getElementById("solicitarMsg");
const resetMsg = document.getElementById("resetMsg");

let recoveryToken = null;

function showMsg(el, message, isError = true) {
  el.textContent = message;
  el.style.color = isError ? "" : "#065f46";
}

solicitarForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMsg(solicitarMsg, "");

  const correo = solicitarForm.correo.value.trim();
  if (!correo) {
    showMsg(solicitarMsg, "Ingresa tu correo electronico.");
    return;
  }

  const submitBtn = solicitarForm.querySelector("button[type='submit']");
  submitBtn.disabled = true;
  submitBtn.textContent = "Verificando...";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/recuperar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ correo }),
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.detail || "Error al solicitar recuperacion.");
    }

    recoveryToken = payload.token || null;

    solicitarForm.style.display = "none";
    resetForm.style.display = "";
    document.getElementById("nueva_contrasena").focus();
  } catch (error) {
    showMsg(solicitarMsg, error.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Continuar";
  }
});

resetForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMsg(resetMsg, "");

  const nueva_contrasena = resetForm.nueva_contrasena.value;
  const confirmar = resetForm.confirmar_contrasena.value;

  if (!nueva_contrasena || !confirmar) {
    showMsg(resetMsg, "Completa todos los campos.");
    return;
  }

  if (nueva_contrasena.length < 6) {
    showMsg(resetMsg, "La contrasena debe tener al menos 6 caracteres.");
    return;
  }

  if (nueva_contrasena !== confirmar) {
    showMsg(resetMsg, "Las contrasenas no coinciden.");
    return;
  }

  if (!recoveryToken) {
    showMsg(resetMsg, "No se encontro un token de recuperacion. Vuelve a intentarlo.");
    return;
  }

  const submitBtn = resetForm.querySelector("button[type='submit']");
  submitBtn.disabled = true;
  submitBtn.textContent = "Guardando...";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: recoveryToken, nueva_contrasena }),
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(payload.detail || "Error al cambiar la contrasena.");
    }

    recoveryToken = null;
    showMsg(resetMsg, "Contrasena actualizada. Redirigiendo al login...", false);
    setTimeout(() => {
      window.location.href = "index.html";
    }, 2000);
  } catch (error) {
    showMsg(resetMsg, error.message);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Cambiar contrasena";
  }
});
