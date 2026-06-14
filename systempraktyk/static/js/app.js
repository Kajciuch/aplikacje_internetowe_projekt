/* ============================================================================
   System Obsługi Praktyk — frontend
   Dynamiczne formularze (dziennik, harmonogram), walidacja po stronie klienta.
   Etapy: 3 (operacje na listach), 10 (frontend/UX).
   ============================================================================ */

(function () {
  "use strict";

  // -------- Dynamiczne wiersze (dziennik / harmonogram) ---------------------
  // Korzystamy z <template id="..."> wewnątrz formularzy.
  document.querySelectorAll(".add-row").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var tplId = btn.dataset.template;
      var tpl = document.getElementById(tplId);
      var target = document.getElementById(btn.dataset.target);
      if (!tpl || !target) return;

      var node = tpl.content.cloneNode(true);

      // Dla dziennika auto-podpowiedź numeru dnia (kolejny).
      if (tplId === "tpl-dziennik-row") {
        var liczba = target.querySelectorAll(".dyn-row").length + 1;
        if (liczba > 120) {
          alert("Dziennik praktyki może mieć maksymalnie 120 dni.");
          return;
        }
        var dzienInput = node.querySelector('input[name="wpis_dzien[]"]');
        if (dzienInput && !dzienInput.value) dzienInput.value = liczba;
      }
      target.appendChild(node);
    });
  });

  // Usuwanie wiersza (delegacja zdarzeń).
  document.addEventListener("click", function (e) {
    if (e.target.classList && e.target.classList.contains("del-row")) {
      var row = e.target.closest(".dyn-row");
      if (row) row.remove();
    }
  });

  // -------- Suma dni w harmonogramie (live) --------------------------------
  function przelicz_sume_harm() {
    var sumaEl = document.getElementById("harm-suma");
    if (!sumaEl) return;
    var suma = 0;
    document.querySelectorAll('input[name="harm_dni[]"]').forEach(function (i) {
      suma += parseInt(i.value || "0", 10) || 0;
    });
    sumaEl.textContent = suma;
    sumaEl.style.color = suma === 120 ? "var(--ok)" : "var(--warn)";
  }
  document.addEventListener("input", function (e) {
    if (e.target.name === "harm_dni[]") przelicz_sume_harm();
  });
  document.addEventListener("click", function (e) {
    if (e.target.classList && (e.target.classList.contains("add-row")
                               || e.target.classList.contains("del-row"))) {
      setTimeout(przelicz_sume_harm, 0);
    }
  });
  przelicz_sume_harm();

  // -------- Walidacja przed wysłaniem (klient) -----------------------------
  document.querySelectorAll("form[data-validate]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      var bledy = [];
      form.querySelectorAll("[required]").forEach(function (pole) {
        if (!pole.value.trim()) {
          bledy.push("Uzupełnij pole: " + (pole.dataset.label || pole.name));
          pole.style.borderColor = "var(--err)";
        }
      });
      var email = form.querySelector('input[type="email"]');
      if (email && email.value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.value)) {
        bledy.push("Nieprawidłowy adres e-mail.");
        email.style.borderColor = "var(--err)";
      }
      if (bledy.length) {
        e.preventDefault();
        alert("Sprawdź formularz:\n• " + bledy.join("\n• "));
      }
    });
  });

  // -------- Potwierdzenie usunięcia ----------------------------------------
  document.querySelectorAll("[data-confirm]").forEach(function (el) {
    el.addEventListener("click", function (e) {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });
})();
