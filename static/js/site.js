/* Easyian site scripts: nav, scroll reveal, service tabs, lead form + hidden captcha. */
(function () {
  "use strict";

  /* ---------- mobile nav ---------- */
  var nav = document.querySelector(".nav");
  var toggle = document.querySelector(".nav-toggle");
  if (nav && toggle) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- scroll reveal ---------- */
  var reveals = document.querySelectorAll("[data-reveal]");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    reveals.forEach(function (el, i) {
      el.classList.add("reveal");
      el.style.transitionDelay = (Number(el.getAttribute("data-reveal")) || 0) * 0.08 + "s";
      io.observe(el);
    });
  }

  /* ---------- service tabs ---------- */
  document.querySelectorAll("[data-tabs]").forEach(function (root) {
    var tabs = root.querySelectorAll("[role=tab]");
    function select(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        t.style.background = on ? t.getAttribute("data-color") : "transparent";
        var panel = document.getElementById(t.getAttribute("aria-controls"));
        if (panel) {
          panel.hidden = !on;
          panel.classList.toggle("show", on);
        }
      });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t); });
      t.addEventListener("keydown", function (e) {
        var dir = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!dir) return;
        var next = tabs[(i + dir + tabs.length) % tabs.length];
        next.focus(); select(next);
      });
    });
    if (tabs.length) select(tabs[0]);
  });

  /* ---------- lead form: hidden captcha (proof of work) ---------- */
  function sha256hex(text) {
    var data = new TextEncoder().encode(text);
    return crypto.subtle.digest("SHA-256", data).then(function (buf) {
      var bytes = new Uint8Array(buf), out = "";
      for (var i = 0; i < bytes.length; i++) out += bytes[i].toString(16).padStart(2, "0");
      return out;
    });
  }

  function solve(challenge, difficulty) {
    var prefix = new Array(difficulty + 1).join("0");
    var n = 0;
    return new Promise(function (resolve) {
      function batch() {
        var jobs = [];
        for (var k = 0; k < 200; k++) {
          (function (nonce) {
            jobs.push(sha256hex(challenge + ":" + nonce).then(function (h) { return h.indexOf(prefix) === 0 ? nonce : -1; }));
          })(n++);
        }
        Promise.all(jobs).then(function (res) {
          var hit = res.filter(function (r) { return r >= 0; });
          if (hit.length) resolve(String(hit[0])); else setTimeout(batch, 0);
        });
      }
      batch();
    });
  }

  function setupLeadForm(form) {
    var challengeInput = form.querySelector("[name=challenge]");
    var powInput = form.querySelector("[name=pow]");
    var status = form.querySelector(".form-status");
    var submitBtn = form.querySelector("[type=submit]");
    var difficulty = Number(form.getAttribute("data-pow")) || 3;
    var solving = null;

    // capture UTM params + page for attribution
    var params = new URLSearchParams(location.search);
    ["utm_source", "utm_medium", "utm_campaign"].forEach(function (k) {
      var el = form.querySelector("[name=" + k + "]");
      if (!el) return;
      var v = params.get(k) || (function () { try { return sessionStorage.getItem(k); } catch (e) { return null; } })();
      if (v) { el.value = v; try { sessionStorage.setItem(k, v); } catch (e) {} }
    });

    function startSolving() {
      if (solving || !window.crypto || !crypto.subtle) return solving;
      solving = solve(challengeInput.value, difficulty).then(function (nonce) {
        powInput.value = nonce;
        return nonce;
      });
      return solving;
    }
    // Only real interaction starts the puzzle — headless form-fillers rarely trigger these.
    ["focusin", "keydown", "pointerdown", "touchstart"].forEach(function (ev) {
      form.addEventListener(ev, startSolving, { once: true, passive: true });
    });

    function showErrors(errors) {
      form.querySelectorAll(".errorlist[data-for]").forEach(function (ul) { ul.innerHTML = ""; });
      Object.keys(errors || {}).forEach(function (field) {
        var ul = form.querySelector('.errorlist[data-for="' + field + '"]');
        if (!ul) ul = form.querySelector('.errorlist[data-for="__all__"]');
        if (!ul) return;
        errors[field].forEach(function (msg) {
          var li = document.createElement("li"); li.textContent = msg; ul.appendChild(li);
        });
      });
    }

    form.addEventListener("submit", function (e) {
      if (!window.fetch || !window.crypto || !crypto.subtle) return; // fall back to normal POST
      e.preventDefault();
      status.className = "form-status";
      status.textContent = "";
      submitBtn.disabled = true;
      var label = submitBtn.textContent;
      submitBtn.textContent = "Sending…";
      Promise.resolve(startSolving()).then(function () {
        return fetch(form.action, {
          method: "POST",
          body: new FormData(form),
          headers: { "X-Requested-With": "XMLHttpRequest", "Accept": "application/json" },
          credentials: "same-origin"
        });
      }).then(function (r) { return r.json(); }).then(function (data) {
        if (data.ok) {
          form.reset();
          showErrors({});
          status.className = "form-status ok";
          status.textContent = data.message;
          if (window.gtag) window.gtag("event", "generate_lead");
        } else {
          showErrors(data.errors);
          status.className = "form-status err";
          status.textContent = data.message || "Please check the highlighted fields.";
          if (data.refresh) setTimeout(function () { location.reload(); }, 2500);
        }
        if (data.challenge) challengeInput.value = data.challenge;
        // every challenge is single-use: solve again for the next attempt
        powInput.value = ""; solving = null;
        if (data.challenge) startSolving();
      }).catch(function () {
        status.className = "form-status err";
        status.textContent = "Network problem — please try again.";
      }).then(function () {
        submitBtn.disabled = false;
        submitBtn.textContent = label;
      });
    });
  }

  document.querySelectorAll("form[data-lead-form]").forEach(setupLeadForm);
})();
