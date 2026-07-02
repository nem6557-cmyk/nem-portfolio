/* =========================================================================
   Portfolio interactions
   - Hero: a looping "simulation readout" of Project 2. An arm holds a pose,
     the winding heats, torque derates, and the arm sags. A teal ghost marks
     the ideal held pose; the amber arm is what the thermal model actually does.
   ========================================================================= */

(function () {
  "use strict";

  var REDUCED = window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var PAL = {
    bg:    "#0B1220",
    grid:  "rgba(79,209,197,0.05)",
    ref:   "rgba(232,237,244,0.14)",
    sim:   "#4FD1C5",
    real:  "#FF8A5B",
    warn:  "#FFC24B",
    ink:   "#E8EDF4",
    muted: "#8A97AC",
    steel: "#3A4A66"
  };

  // ---- smooth interpolation over keyframes ------------------------------
  function smoothstep(t) { return t * t * (3 - 2 * t); }
  function track(keys, u) {
    // keys: array of [u, value], sorted. Interpolate with smoothstep.
    for (var i = 0; i < keys.length - 1; i++) {
      var a = keys[i], b = keys[i + 1];
      if (u >= a[0] && u <= b[0]) {
        var f = (u - a[0]) / (b[0] - a[0] || 1);
        return a[1] + (b[1] - a[1]) * smoothstep(f);
      }
    }
    return keys[keys.length - 1][1];
  }

  var AMBIENT = 25, PEAK = 112, DERATE = 90, TAU_PEAK = 6.0, TAU_FLOOR = 2.4;

  // temperature and sag angle (deg) across one normalized cycle u in [0,1)
  var T_KEYS = [[0, AMBIENT], [0.30, 88], [0.52, PEAK], [0.70, PEAK], [1.0, AMBIENT]];
  var A_KEYS = [[0, 0], [0.34, 0], [0.56, 38], [0.70, 38], [0.93, 0], [1.0, 0]];

  function tauAvail(T) {
    if (T <= DERATE) return TAU_PEAK;
    var f = (T - DERATE) / (PEAK - DERATE);
    return Math.max(TAU_FLOOR, TAU_PEAK - (TAU_PEAK - TAU_FLOOR) * f);
  }

  function statusFor(u) {
    if (u < 0.34) return { txt: "HOLDING", cls: "sim" };
    if (u < 0.56) return { txt: "DERATING", cls: "real" };
    if (u < 0.72) return { txt: "SAG LIMIT", cls: "warn" };
    return { txt: "RECOVERING", cls: "sim" };
  }

  function drawArm(ctx, base, l1, l2, ang1, ang2, color, payloadColor, ghost) {
    var ex = base.x + l1 * Math.cos(ang1);
    var ey = base.y + l1 * Math.sin(ang1);
    var tx = ex + l2 * Math.cos(ang1 + ang2);
    var ty = ey + l2 * Math.sin(ang1 + ang2);

    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.globalAlpha = ghost ? 0.42 : 1;

    // links
    ctx.strokeStyle = color;
    ctx.lineWidth = ghost ? 3 : 7;
    ctx.beginPath();
    ctx.moveTo(base.x, base.y);
    ctx.lineTo(ex, ey);
    ctx.lineTo(tx, ty);
    ctx.stroke();

    if (!ghost) {
      // inner highlight
      ctx.strokeStyle = "rgba(255,255,255,0.18)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(base.x, base.y);
      ctx.lineTo(ex, ey);
      ctx.lineTo(tx, ty);
      ctx.stroke();
    }

    // joints
    ctx.globalAlpha = ghost ? 0.5 : 1;
    ctx.fillStyle = PAL.bg;
    ctx.strokeStyle = color;
    ctx.lineWidth = ghost ? 2 : 3;
    [[base.x, base.y], [ex, ey]].forEach(function (p) {
      ctx.beginPath();
      ctx.arc(p[0], p[1], ghost ? 4 : 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
    });

    // payload
    ctx.beginPath();
    ctx.arc(tx, ty, ghost ? 7 : 11, 0, Math.PI * 2);
    if (ghost) {
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.stroke();
    } else {
      ctx.fillStyle = payloadColor;
      ctx.fill();
      ctx.strokeStyle = "rgba(0,0,0,0.25)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  function initSim() {
    var canvas = document.getElementById("sim-canvas");
    if (!canvas) return;
    var ctx = canvas.getContext("2d");
    var wrap = canvas.parentElement;

    var el = {
      T: document.getElementById("ro-temp"),
      tau: document.getElementById("ro-tau"),
      ang: document.getElementById("ro-ang"),
      st: document.getElementById("ro-status")
    };

    var W = 0, H = 0, DPR = Math.min(window.devicePixelRatio || 1, 2);

    function resize() {
      var r = wrap.getBoundingClientRect();
      W = r.width; H = r.height;
      canvas.width = Math.round(W * DPR);
      canvas.height = Math.round(H * DPR);
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    }

    function frame(u) {
      var T = track(T_KEYS, u);
      var ang = track(A_KEYS, u);      // degrees of shoulder sag
      var rad = ang * Math.PI / 180;
      var tau = tauAvail(T);
      var st = statusFor(u);

      ctx.clearRect(0, 0, W, H);

      // background grid
      ctx.strokeStyle = PAL.grid;
      ctx.lineWidth = 1;
      var step = 32;
      for (var x = (W % step) / 2; x < W; x += step) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
      }
      for (var y = (H % step) / 2; y < H; y += step) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
      }

      var base = { x: W * 0.29, y: H * 0.42 };
      var l1 = Math.min(W, H) * 0.29;
      var l2 = Math.min(W, H) * 0.25;

      // horizontal reference line (ideal hold height)
      ctx.strokeStyle = PAL.ref;
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(base.x, base.y);
      ctx.lineTo(base.x + l1 + l2 + 16, base.y);
      ctx.stroke();
      ctx.setLineDash([]);

      // motor mount (short, so it does not collide with the readout)
      ctx.fillStyle = PAL.steel;
      var mH = Math.min(46, H * 0.17);
      ctx.beginPath();
      roundRect(ctx, base.x - 15, base.y - 3, 30, mH, 5);
      ctx.fill();

      // ghost ideal pose (teal), then real (amber)
      drawArm(ctx, base, l1, l2, 0, 0, PAL.sim, PAL.sim, true);
      drawArm(ctx, base, l1, l2, rad, rad * 0.5, PAL.real, PAL.real, false);

      // slim thermometer, right edge
      var tx0 = W - 22, tyTop = H * 0.16, tyBot = H * 0.80, tw = 7;
      ctx.strokeStyle = "rgba(232,237,244,0.18)";
      ctx.lineWidth = 1;
      roundRect(ctx, tx0, tyTop, tw, tyBot - tyTop, 4);
      ctx.stroke();
      var frac = Math.max(0, Math.min(1, (T - AMBIENT) / (PEAK - AMBIENT)));
      var fillH = (tyBot - tyTop) * frac;
      var hot = T >= DERATE;
      ctx.fillStyle = hot ? PAL.real : PAL.sim;
      roundRect(ctx, tx0, tyBot - fillH, tw, fillH, 4);
      ctx.fill();
      // derate tick
      var dFrac = (DERATE - AMBIENT) / (PEAK - AMBIENT);
      var dY = tyBot - (tyBot - tyTop) * dFrac;
      ctx.strokeStyle = PAL.warn;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(tx0 - 4, dY); ctx.lineTo(tx0 + tw + 4, dY); ctx.stroke();

      // readouts
      if (el.T) el.T.textContent = T.toFixed(0) + " C";
      if (el.tau) el.tau.textContent = tau.toFixed(1) + " Nm";
      if (el.ang) el.ang.textContent = ang.toFixed(0) + " deg";
      if (el.st) {
        el.st.textContent = st.txt;
        el.st.className = "v " + st.cls;
      }
    }

    function roundRect(c, x, y, w, h, r) {
      if (h < 0) { y += h; h = -h; }
      r = Math.min(r, w / 2, h / 2);
      c.beginPath();
      c.moveTo(x + r, y);
      c.arcTo(x + w, y, x + w, y + h, r);
      c.arcTo(x + w, y + h, x, y + h, r);
      c.arcTo(x, y + h, x, y, r);
      c.arcTo(x, y, x + w, y, r);
      c.closePath();
    }

    resize();
    window.addEventListener("resize", resize);
    if (window.ResizeObserver) new ResizeObserver(resize).observe(wrap);

    var CYCLE = 9500;
    if (REDUCED) {
      frame(0.60);   // representative hot, sagged frame
      return;
    }
    var start = null;
    function loop(ts) {
      if (start === null) start = ts;
      var u = ((ts - start) % CYCLE) / CYCLE;
      frame(u);
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  }

  // ---- nav toggle -------------------------------------------------------
  function initNav() {
    var btn = document.querySelector(".nav-toggle");
    var links = document.querySelector(".nav-links");
    if (!btn || !links) return;
    btn.addEventListener("click", function () {
      links.classList.toggle("open");
    });
    links.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { links.classList.remove("open"); });
    });
  }

  // ---- scroll reveal ----------------------------------------------------
  function initReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) return;
    if (REDUCED || !("IntersectionObserver" in window)) {
      items.forEach(function (i) { i.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    items.forEach(function (i) { io.observe(i); });
  }

  // ---- year -------------------------------------------------------------
  function initYear() {
    var y = document.getElementById("year");
    if (y) y.textContent = new Date().getFullYear();
  }

  function boot() {
    initNav();
    initReveal();
    initYear();
    initSim();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();

/* elevated nav state after scroll */
(function () {
  var nav = document.querySelector(".nav");
  if (!nav) return;
  function onScroll() { nav.classList.toggle("scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
