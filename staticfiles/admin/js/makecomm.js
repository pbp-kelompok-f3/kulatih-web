document.addEventListener("DOMContentLoaded", function() {
  const toast = document.getElementById("toast-container");
  if (toast) {
    toast.style.opacity = 0;
    toast.style.transition = "opacity 0.5s ease";
    setTimeout(() => (toast.style.opacity = 1), 50); // fade-in

    setTimeout(() => {
      toast.style.opacity = 0;
      setTimeout(() => toast.remove(), 500);
    }, 3000);
  }
});
