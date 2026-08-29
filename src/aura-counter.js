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
    return n.toLocaleString("es-AR");
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

  root.innerHTML =
    '<div class="c-label">' + esc(C.label) + "</div>" +
    '<div class="c-num" id="c-num">0</div>' +
    '<div class="c-msg" id="c-msg">' + esc(C.intro) + "</div>" +
    '<button type="button" class="c-btn" id="c-btn">' + esc(C.cta) + "</button>" +
    '<button type="button" class="c-reset" id="c-reset">' + esc(C.reset) + "</button>";

  root.querySelector("#c-num").textContent = fmt(total);

  root.querySelector("#c-btn").addEventListener("click", function () {
    var ev = C.events[Math.floor(Math.random() * C.events.length)];
    total += ev.pts;
    save();
    render((ev.pts > 0 ? "+" : "") + fmt(ev.pts) + " — " + ev.t);
  });

  root.querySelector("#c-reset").addEventListener("click", function () {
    total = 0;
    save();
    render();
  });
})();
