(function () {
  var C = window.AURA_COUNTER;
  if (!C) return;
  var root = document.getElementById("aura-counter");
  if (!root) return;

  var KEY = "aura_contador_" + (C.key || "x");
  var total = parseInt(localStorage.getItem(KEY), 10);
  if (!isFinite(total)) total = 0;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function fmt(n) {
    return n.toLocaleString(C.numfmt || "es-AR");
  }

  function save() {
    try { localStorage.setItem(KEY, String(total)); } catch (e) {}
  }

  function render(msg) {
    var numEl = root.querySelector("#c-num");
    var msgEl = root.querySelector("#c-msg");
    numEl.textContent = fmt(total);
    numEl.className = "c-num" + (total < 0 ? " neg" : total > 0 ? " pos" : "");
    msgEl.textContent = msg || C.intro;
    numEl.classList.remove("bump");
    void numEl.offsetWidth;
    numEl.classList.add("bump");
  }

  var presetsHtml = (C.presets || [])
    .map(function (p) {
      return '<button type="button" class="c-preset" data-pts="' + p + '">+' + fmt(p) + "</button>";
    })
    .join("");

  root.innerHTML =
    '<div class="c-label">' + esc(C.label) + "</div>" +
    '<div class="c-num" id="c-num">0</div>' +
    '<div class="c-msg" id="c-msg">' + esc(C.intro) + "</div>" +
    '<button type="button" class="c-btn" id="c-btn">' + esc(C.cta) + "</button>" +
    '<div class="c-presets" id="c-presets">' + presetsHtml + "</div>" +
    '<button type="button" class="c-reset" id="c-reset">' + esc(C.reset) + "</button>";

  // No solo el texto: si el total guardado es negativo, la clase .neg tiene
  // que aplicarse ya en la carga, no recien despues del primer clic.
  var numEl0 = root.querySelector("#c-num");
  numEl0.textContent = fmt(total);
  numEl0.className = "c-num" + (total < 0 ? " neg" : total > 0 ? " pos" : "");

  root.querySelector("#c-btn").addEventListener("click", function () {
    var ev = C.events[Math.floor(Math.random() * C.events.length)];
    total += ev.pts;
    save();
    render((ev.pts > 0 ? "+" : "") + fmt(ev.pts) + " — " + ev.t);
  });

  root.querySelector("#c-presets").addEventListener("click", function (e) {
    var btn = e.target.closest(".c-preset");
    if (!btn) return;
    var pts = parseInt(btn.dataset.pts, 10);
    total += pts;
    save();
    render("+" + fmt(pts) + " — " + C.presetNote + ".");
  });

  root.querySelector("#c-reset").addEventListener("click", function () {
    total = 0;
    save();
    render();
  });
})();
