(function () {
  var C = window.FAMOSOS;
  var API = "/api/famosos/";
  var LOC = "?loc=" + encodeURIComponent(C.loc);
  var estado = null;
  var offline = false;
  var bloqueado = false;
  var pendiente = null;
  var RAPIDO = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var ESPERA = RAPIDO ? 350 : 1100;

  function $(s) { return document.querySelector(s); }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function num(n) {
    return (n < 0 ? "−" : "") + Math.abs(n).toLocaleString(C.numfmt);
  }
  function mapa() {
    var m = {};
    C.figuras.forEach(function (f) { m[f.id] = f; });
    return m;
  }
  function semilla() {
    return C.figuras.map(function (f) {
      return { id: f.id, aura: C.aura_inicial, ganados: 0, perdidos: 0 };
    });
  }
  function aviso() {
    var a = $("#aviso");
    if (a) a.hidden = false;
  }

  function cargarEstado() {
    return fetch(API + "estado" + LOC, { headers: { accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        if (!d || !d.figuras || !d.figuras.length) throw 0;
        var m = mapa();
        estado = d.figuras.filter(function (c) { return m[c.id]; });
        if (!estado.length) throw 0;
      })
      .catch(function () {
        offline = true;
        estado = semilla();
        aviso();
      });
  }

  function robo(aGana, aPierde) {
    var esperado = 1 / (1 + Math.pow(10, (aPierde - aGana) / 400));
    return Math.max(1, Math.round(C.k * (1 - esperado)));
  }

  /* ---------------- votar ---------------- */
  var par = [];
  var M = mapa();

  function elegirPar() {
    var a = estado[Math.floor(Math.random() * estado.length)];
    var resto = estado.filter(function (c) { return c.id !== a.id; });
    resto.sort(function (x, y) {
      return Math.abs(x.aura - a.aura) - Math.abs(y.aura - a.aura);
    });
    var cerca = resto.slice(0, Math.min(8, resto.length));
    var b = cerca[Math.floor(Math.random() * cerca.length)];
    par = Math.random() < 0.5 ? [a, b] : [b, a];
  }

  function pintar(i) {
    var c = par[i], f = M[c.id];
    var el = $("#c" + i);
    el.className = "card";
    el.innerHTML =
      '<span class="delta" id="d' + i + '"></span>' +
      '<span class="anio">' + esc(f.anios) + "</span>" +
      '<span class="emoji">' + f.emoji + "</span>" +
      '<span class="nombre">' + esc(f.nombre) + "</span>" +
      '<span class="oficio">' + esc(f.oficio) + "</span>" +
      '<span class="meta"><b>' + num(c.aura) + "</b> " + esc(C.t.de_aura_label) + "</span>" +
      '<span class="pick">' + esc(C.t.cta) + "</span>";
  }

  function nuevo() {
    if (pendiente) { clearTimeout(pendiente); pendiente = null; }
    bloqueado = false;
    elegirPar();
    pintar(0);
    pintar(1);
    var b = $("#avance");
    if (b) b.className = "avance";
  }

  function programarSiguiente() {
    var b = $("#avance");
    if (b) {
      b.className = "avance corriendo";
      b.style.animationDuration = ESPERA + "ms";
    }
    pendiente = setTimeout(nuevo, ESPERA);
  }

  function trackMilestones() {
    try {
      var n = (parseInt(localStorage.getItem("aura_battles_famosos"), 10) || 0) + 1;
      localStorage.setItem("aura_battles_famosos", String(n));
      if (!window.gtag) return;
      if (n === 5) gtag("event", "famosos_5_battles", { loc: C.loc, count: 5 });
      if (n === 10) gtag("event", "famosos_10_battles", { loc: C.loc, count: 10 });
    } catch (e) { }
  }

  function votar(i) {
    if (bloqueado) return;
    bloqueado = true;
    var g = par[i], p = par[1 - i];
    var pts = robo(g.aura, p.aura);

    g.aura += pts; g.ganados++;
    p.aura -= pts; p.perdidos++;

    $("#c" + i).classList.add("gano");
    $("#c" + (1 - i)).classList.add("perdio");
    var du = $("#d" + i), dd = $("#d" + (1 - i));
    du.textContent = "+" + pts; du.className = "delta up";
    dd.textContent = "−" + pts; dd.className = "delta down";

    $("#resultado").innerHTML =
      "<b>" + M[g.id].emoji + " " + esc(M[g.id].nombre) + "</b> " + esc(C.t.robo) +
      ' <span class="pts">' + pts + "</span> " + esc(C.t.de_aura) +
      " <b>" + esc(M[p.id].nombre) + "</b>";
    programarSiguiente();
    trackMilestones();

    if (offline) return;
    fetch(API + "voto", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ loc: C.loc, ganador: g.id, perdedor: p.id })
    })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        if (!d || !d.ok) return;
        g.aura = d.ganador.aura;
        p.aura = d.perdedor.aura;
      })
      .catch(function () { });
  }

  function iniciarVotar() {
    [0, 1].forEach(function (i) {
      $("#c" + i).addEventListener("click", function () { votar(i); });
    });
    cargarEstado().then(nuevo);
  }

  /* ---------------- ranking + feed ---------------- */
  function hace(ts) {
    var s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
    var u = C.t.tiempo;
    if (s < 60) return u.seg.replace("%s", s);
    if (s < 3600) return u.min.replace("%s", Math.floor(s / 60));
    if (s < 86400) return u.hora.replace("%s", Math.floor(s / 3600));
    return u.dia.replace("%s", Math.floor(s / 86400));
  }

  function iniciarRanking() {
    cargarEstado().then(function () {
      var lista = estado.slice().sort(function (a, b) { return b.aura - a.aura; });
      var ul = $("#tabla");
      ul.classList.remove("skeleton");
      ul.innerHTML = lista
        .map(function (c, i) {
          var f = M[c.id];
          return (
            '<li class="fila">' +
            '<span class="pos">' + (i + 1) + "</span>" +
            '<span class="quien"><span class="e">' + f.emoji + "</span>" +
            '<span><span class="n">' + esc(f.nombre) + "</span>" +
            '<span class="anio">' + esc(f.anios) + "</span></span></span>" +
            '<span class="puntos' + (c.aura < 0 ? " neg" : "") + '">' + num(c.aura) + "</span>" +
            "</li>"
          );
        })
        .join("");
    });

    var feed = $("#feed");
    if (!feed) return;
    fetch(API + "duelos" + LOC, { headers: { accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        var items = (d.duelos || []).filter(function (x) {
          return M[x.ganador] && M[x.perdedor];
        });
        feed.classList.remove("skeleton");
        if (!items.length) {
          feed.innerHTML = '<li class="vacio">' + esc(C.t.vacio) + "</li>";
          return;
        }
        feed.innerHTML = items
          .map(function (x) {
            var g = M[x.ganador], p = M[x.perdedor];
            return (
              '<li class="duelo"><span class="g">' + g.emoji + " " + esc(g.nombre) +
              "</span> " + esc(C.t.robo) + ' <span class="robo">' + x.puntos + "</span> " +
              esc(C.t.de_aura) + ' <span class="p">' + esc(p.nombre) + "</span>" +
              '<span class="cuando">' + hace(x.ts) + "</span></li>"
            );
          })
          .join("");
      })
      .catch(function () {
        feed.classList.remove("skeleton");
        feed.innerHTML = '<li class="vacio">' + esc(C.t.vacio) + "</li>";
      });
  }

  if (C.pagina === "votar") iniciarVotar();
  else iniciarRanking();
})();
