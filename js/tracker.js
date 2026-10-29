!function(){
  var ENDPOINT = '/api/event';
  var BATCH_INTERVAL = 5000;
  var queue = [];
  var sessionId = sessionStorage.getItem('_sid');
  if (!sessionId) { sessionId = crypto.randomUUID(); sessionStorage.setItem('_sid', sessionId); }

  var page = location.pathname.replace(/\/$/, '') || '/';
  var ref = document.referrer;
  var params = new URLSearchParams(location.search);
  var utmSource = params.get('utm_source') || '';
  var device = /Mobi|Android/i.test(navigator.userAgent) ? 'mobile' : (window.innerWidth < 1024 ? 'tablet' : 'desktop');

  function track(type, target, value) {
    queue.push({ type: type, page: page, target: target || '', referrer: ref, utm_source: utmSource, device: device, session_id: sessionId, value: value || null });
  }

  function flush() {
    if (!queue.length) return;
    var batch = queue.splice(0, 50);
    var blob = new Blob([JSON.stringify(batch)], { type: 'application/json' });
    if (navigator.sendBeacon) { navigator.sendBeacon(ENDPOINT, blob); }
    else { fetch(ENDPOINT, { method: 'POST', body: blob, keepalive: true }); }
  }

  track('pageview');

  var t0 = Date.now();
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') {
      track('page_exit', '', { seconds: Math.round((Date.now() - t0) / 1000) });
      flush();
    }
  });

  var scrolled = {};
  window.addEventListener('scroll', debounce(function() {
    var pct = Math.round(100 * (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight);
    [25, 50, 75, 100].forEach(function(d) {
      if (pct >= d && !scrolled[d]) { scrolled[d] = 1; track('scroll', '', { depth: d }); }
    });
  }, 300), { passive: true });

  document.addEventListener('click', function(e) {
    var el = e.target.closest('[data-track], a, button, .tile, .theme-toggle, .help-btn, th.sort');
    if (!el) return;
    if (el.dataset && el.dataset.track) { track('click', el.dataset.track); return; }
    if (el.closest('.tile')) { var t = el.closest('.tile'); var u = t.querySelector('.u'); track('click', 'mapa.' + (u ? u.textContent : 'tile')); return; }
    if (el.tagName === 'circle') { track('click', 'hemiciclo.circle'); return; }
    if (el.closest('.theme-toggle')) { track('click', 'tema.' + (document.documentElement.dataset.theme || 'toggle')); return; }
    if (el.closest('.help-btn')) { track('click', 'ajuda'); return; }
    if (el.matches && el.matches('th.sort')) { track('click', 'tabela.sort.' + (el.textContent || '').trim().slice(0, 30)); return; }
    if (el.closest('.nav-links') && el.tagName === 'A') { track('click', 'nav.' + (el.getAttribute('href') || '').replace('#', '')); return; }
    if (el.tagName === 'A' && el.hostname !== location.hostname) { track('click', 'ext.' + el.hostname + el.pathname.slice(0, 50)); return; }
    if (el.tagName === 'A' && el.href) { var text = (el.textContent || '').trim().slice(0, 40); track('click', 'link.' + text); }
    if (el.tagName === 'SUMMARY' || el.closest('summary')) { var det = el.closest('details'); track('click', 'accordion.' + (det && det.querySelector('summary') ? det.querySelector('summary').textContent.trim().slice(0, 40) : 'unknown')); }
  }, true);

  var sectionTimers = {};
  if (window.IntersectionObserver) {
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        var id = entry.target.id || (entry.target.querySelector('h2,h3') ? entry.target.querySelector('h2,h3').textContent.trim().slice(0, 40) : 'unknown');
        if (entry.isIntersecting) {
          sectionTimers[id] = Date.now();
        } else if (sectionTimers[id]) {
          var secs = Math.round((Date.now() - sectionTimers[id]) / 1000);
          if (secs >= 2) track('section_time', id, { seconds: secs });
          delete sectionTimers[id];
        }
      });
    }, { threshold: 0.3 });
    document.querySelectorAll('section, [id]').forEach(function(el) {
      if (el.id && el.offsetHeight > 100) obs.observe(el);
    });
  }

  document.addEventListener('mouseover', debounce(function(e) {
    var tile = e.target.closest && e.target.closest('.tile');
    if (tile) {
      var u = tile.querySelector('.u');
      track('hover', 'mapa.' + (u ? u.textContent : 'tile'));
    }
  }, 500));

  function debounce(fn, ms) {
    var t;
    return function() {
      var self = this, args = arguments;
      clearTimeout(t);
      t = setTimeout(function() { fn.apply(self, args); }, ms);
    };
  }

  setInterval(flush, BATCH_INTERVAL);
  window.addEventListener('beforeunload', flush);
}();
