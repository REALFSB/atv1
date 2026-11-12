/* DataTrack · comportamento das telas de autenticação.
   A validação aqui é só conforto de uso: o servidor valida tudo de novo. */
(function () {
  "use strict";

  // Mostrar / ocultar senha
  document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
    var input = document.getElementById(btn.getAttribute("data-toggle-password"));
    if (!input) return;
    btn.addEventListener("click", function () {
      var show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.setAttribute("aria-pressed", String(show));
      btn.setAttribute("aria-label", show ? "Ocultar senha" : "Mostrar senha");
      input.focus();
    });
  });

  var EMAIL = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

  function messageFor(input, form) {
    var v = input.value.trim();
    if (input.required && !v) {
      return { email: "Informe o e-mail.", password: input.autocomplete === "new-password" ? "Crie uma senha." : "Informe a senha.",
               name: "Informe seu nome.", confirm: "Confirme a senha." }[input.name] || "Campo obrigatório.";
    }
    if (input.type === "email" && v && !EMAIL.test(v)) return "Informe um e-mail válido.";
    if (input.minLength > 0 && v && input.value.length < input.minLength) {
      return "A senha precisa ter pelo menos " + input.minLength + " caracteres.";
    }
    var match = input.getAttribute("data-match");
    if (match && form.elements[match] && input.value !== form.elements[match].value) {
      return "As senhas não conferem.";
    }
    return "";
  }

  function show(input, msg) {
    var field = input.closest(".field");
    var box = document.querySelector('[data-error-for="' + input.name + '"]');
    if (box) box.textContent = msg;
    if (field) field.classList.toggle("field--invalid", !!msg);
    if (msg) input.setAttribute("aria-invalid", "true"); else input.removeAttribute("aria-invalid");
  }

  document.querySelectorAll("form[data-validate]").forEach(function (form) {
    var inputs = Array.prototype.filter.call(form.elements, function (el) {
      return el.tagName === "INPUT" && el.type !== "hidden";
    });
    inputs.forEach(function (input) {
      input.addEventListener("blur", function () { if (input.value) show(input, messageFor(input, form)); });
      input.addEventListener("input", function () {
        if (input.getAttribute("aria-invalid")) show(input, messageFor(input, form));
      });
    });
    form.addEventListener("submit", function (e) {
      var first = null;
      inputs.forEach(function (input) {
        var msg = messageFor(input, form);
        show(input, msg);
        if (msg && !first) first = input;
      });
      if (first) { e.preventDefault(); first.focus(); }
    });
  });
})();
