(function () {
  var C = window.AURA_QUIZ;
  if (!C) return;
  var root = document.getElementById("aura-quiz");
  if (!root) return;

  var tally = {};
  var step = 0;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function start() {
    tally = {};
    step = 0;
    render();
  }

  function render() {
    if (step < C.questions.length) renderQuestion();
    else renderResult();
  }

  function renderQuestion() {
    var q = C.questions[step];
    var pct = Math.round((step / C.questions.length) * 100);
    root.innerHTML =
      '<div class="q-bar"><div class="q-fill" style="width:' + pct + '%"></div></div>' +
      '<p class="q-count">' + (step + 1) + ' / ' + C.questions.length + '</p>' +
      '<h3 class="q-text">' + esc(q.q) + '</h3>' +
      '<div class="q-opts">' +
      q.opts.map(function (o, i) {
        return '<button type="button" class="q-opt" data-i="' + i + '">' + esc(o.t) + "</button>";
      }).join("") +
      "</div>";
    root.querySelectorAll(".q-opt").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var color = q.opts[+btn.dataset.i].c;
        tally[color] = (tally[color] || 0) + 1;
        step++;
        render();
      });
    });
  }

  function renderResult() {
    var winner = Object.keys(tally).sort(function (a, b) { return tally[b] - tally[a]; })[0];
    var info = C.colors[winner];
    root.innerHTML =
      '<div class="q-result">' +
      '<span class="q-emoji">' + info.emoji + "</span>" +
      '<h3>' + esc(C.resultLabel) + " " + esc(info.nombre) + "</h3>" +
      '<p>' + esc(info.blurb) + "</p>" +
      (info.url ? '<a class="q-cta" href="' + info.url + '">' + esc(C.seeMore) + "</a>" : "") +
      '<button type="button" class="q-retry">' + esc(C.retry) + "</button>" +
      "</div>";
    root.querySelector(".q-retry").addEventListener("click", start);
  }

  start();
})();
