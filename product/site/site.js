/* Landing page: TH/EN content toggle (Thai default, remembered in this browser) and the
   workflow-stage bar's current marker. Headings and controls stay English. */
(function () {
  "use strict";

  function store(k, v) {
    try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { /* storage blocked */ }
    return null;
  }
  function setLang(l) {
    if (l !== "th" && l !== "en") return;
    document.documentElement.lang = l;
    document.querySelectorAll(".lang button").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.getAttribute("data-lang") === l));
    });
    store("mwd.lang", l);
  }
  var fromHash = /(?:^|[#&])lang=(th|en)\b/.exec(location.hash);
  setLang(fromHash ? fromHash[1] : (store("mwd.lang") === "en" ? "en" : "th"));
  document.querySelector(".lang").addEventListener("click", function (e) {
    var b = e.target.closest("button[data-lang]");
    if (b) setLang(b.getAttribute("data-lang"));
  });

  var links = Array.prototype.slice.call(document.querySelectorAll(".stages a"));
  var sections = links.map(function (a) { return document.getElementById(a.getAttribute("data-stage")); });
  function mark() {
    var y = window.scrollY + window.innerHeight * 0.35, current = -1;
    sections.forEach(function (s, i) { if (s && s.getBoundingClientRect().top + window.scrollY <= y) current = i; });
    links.forEach(function (a, i) {
      if (i === current) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
    });
  }
  window.addEventListener("scroll", mark, { passive: true });
  mark();
})();
