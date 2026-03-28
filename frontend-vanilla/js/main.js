const statusText = document.getElementById("status");
const actionBtn = document.getElementById("actionBtn");

actionBtn.addEventListener("click", () => {
  statusText.textContent = "JavaScript conectado correctamente.";
});
