(function () {
  var C = window.DUELOS;
  var API = "/api/aura/";
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
  function num(n) { return (n < 0 ? "−" : "") + Math.abs(n).toLocaleString("es-AR"); }

  function semilla() {
    return C.candidatos.map(function (c) {
      return { id: c.id, emoji: c.emoji, nombre: c.nombre, aura: C.aura_inicial, ganados: 0, perdidos: 0 };
    });
  }

  function mostrarAviso() {
    var a = $("#aviso");
    if (a) a.hidden = false;
  }

  function cargarEstado() {
    return fetch(API + "estado" + LOC, { headers: { accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        if (!d || !d.candidatos || !d.candidatos.length) throw 0;
        // keep copy from the build, numbers from the server
        var copia = {};
        C.candidatos.forEach(function (c) { copia[c.id] = c; });
        estado = d.candidatos
          .filter(function (c) { return copia[c.id]; })
          .map(function (c) {
            return {
              id: c.id,
              emoji: copia[c.id].emoji,
              nombre: copia[c.id].nombre,
              aura: c.aura,
              ganados: c.ganados || 0,
              perdidos: c.perdidos || 0
            };
          });
        if (!estado.length) throw 0;
      })
      .catch(function () {
        offline = true;
        estado = semilla();
        mostrarAviso();
      });
  }

  /* ---------------- aura math (mirrors the server) ---------------- */
  function robo(aGana, aPierde) {
    var esperado = 1 / (1 + Math.pow(10, (aPierde - aGana) / 400));
    return Math.max(1, Math.round(C.k * (1 - esperado)));
  }

  /* ---------------- página: votar ---------------- */
  var par = [];

  function elegirPar() {
    var pool = estado.slice();
    var a = pool[Math.floor(Math.random() * pool.length)];
    var resto = pool.filter(function (c) { return c.id !== a.id; });
    resto.sort(function (x, y) { return Math.abs(x.aura - a.aura) - Math.abs(y.aura - a.aura); });
    var cerca = resto.slice(0, Math.min(8, resto.length));
    var b = cerca[Math.floor(Math.random() * cerca.length)];
    par = Math.random() < 0.5 ? [a, b] : [b, a];
  }

  function pintarCarta(i) {
    var c = par[i];
    var el = $("#c" + i);
    el.className = "card";
    el.innerHTML =
      '<span class="delta" id="d' + i + '"></span>' +
      '<span class="emoji">' + c.emoji + "</span>" +
      '<span class="nombre">' + esc(c.nombre) + "</span>" +
      '<span class="meta"><b>' + num(c.aura) + "</b> de aura</span>" +
      '<span class="pick">' + esc(C.t.cta) + "</span>";
  }

  function nuevoDuelo() {
    if (pendiente) { clearTimeout(pendiente); pendiente = null; }
    bloqueado = false;
    elegirPar();
    pintarCarta(0);
    pintarCarta(1);
    var b = $("#avance");
    if (b) b.className = "avance";
  }

  function programarSiguiente() {
    var b = $("#avance");
    if (b) {
      b.className = "avance corriendo";
      b.style.animationDuration = ESPERA + "ms";
    }
    pendiente = setTimeout(nuevoDuelo, ESPERA);
  }

  function trackMilestones() {
    try {
      var n = (parseInt(localStorage.getItem("aura_battles_duelos"), 10) || 0) + 1;
      localStorage.setItem("aura_battles_duelos", String(n));
      if (!window.gtag) return;
      if (n === 5) gtag("event", "duelos_5_battles", { loc: C.loc, count: 5 });
      if (n === 10) gtag("event", "duelos_10_battles", { loc: C.loc, count: 10 });
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
      "<b>" + g.emoji + " " + esc(g.nombre) + "</b> " + esc(C.t.robo) +
      ' <span class="pts">' + pts + "</span> " + esc(C.t.de_aura) +
      " <b>" + p.emoji + "</b>";
    programarSiguiente();
    trackMilestones();

    if (!offline) {
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
  }

  function iniciarVotar() {
    [0, 1].forEach(function (i) {
      var el = $("#c" + i);
      el.addEventListener("click", function () { votar(i); });
    });
    cargarEstado().then(nuevoDuelo);
  }

  /* ---------------- página: ranking ---------------- */
  function iniciarRanking() {
    cargarEstado().then(function () {
      var lista = estado.slice().sort(function (a, b) { return b.aura - a.aura; });
      var ul = $("#tabla");
      ul.classList.remove("skeleton");
      ul.innerHTML = lista
        .map(function (c, i) {
          return (
            '<li class="fila">' +
            '<span class="pos">' + (i + 1) + "</span>" +
            '<span class="quien"><span class="e">' + c.emoji + "</span>" +
            '<span class="n">' + esc(c.nombre) + "</span></span>" +
            '<span class="puntos' + (c.aura < 0 ? " neg" : "") + '">' + num(c.aura) + "</span>" +
            "</li>"
          );
        })
        .join("");
    });
  }

  /* ---------------- página: historial ---------------- */
  function hace(ts) {
    var s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
    if (s < 60) return "hace " + s + " s";
    if (s < 3600) return "hace " + Math.floor(s / 60) + " min";
    if (s < 86400) return "hace " + Math.floor(s / 3600) + " h";
    return "hace " + Math.floor(s / 86400) + " d";
  }

  function iniciarHistorial() {
    var copia = {};
    C.candidatos.forEach(function (c) { copia[c.id] = c; });
    var ul = $("#feed");

    fetch(API + "duelos" + LOC, { headers: { accept: "application/json" } })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        var items = (d.duelos || []).filter(function (x) { return copia[x.ganador] && copia[x.perdedor]; });
        ul.classList.remove("skeleton");
        if (!items.length) { ul.innerHTML = '<li class="vacio">' + esc(C.t.vacio) + "</li>"; return; }
        ul.innerHTML = items
          .map(function (x) {
            var g = copia[x.ganador], p = copia[x.perdedor];
            return (
              '<li class="duelo">' +
              '<span class="g">' + g.emoji + " " + esc(g.nombre) + "</span> " +
              esc(C.t.robo) + ' <span class="robo">' + x.puntos + "</span> " +
              esc(C.t.de_aura) + ' <span class="p">' + p.emoji + " " + esc(p.nombre) + "</span>" +
              '<span class="cuando">' + hace(x.ts) + "</span>" +
              "</li>"
            );
          })
          .join("");
      })
      .catch(function () {
        ul.classList.remove("skeleton");
        ul.innerHTML = '<li class="vacio">' + esc(C.t.vacio) + "</li>";
        mostrarAviso();
      });
  }

  if (C.pagina === "votar") iniciarVotar();
  else if (C.pagina === "ranking") iniciarRanking();
  else iniciarHistorial();
})();
