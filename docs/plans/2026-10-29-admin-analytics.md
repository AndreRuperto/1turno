# Admin Analytics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add full-funnel analytics (pageviews, clicks, scroll, section time, referrers) with a password-protected admin dashboard styled like the turnos site.

**Architecture:** Replace `http-server` with Express (~100 lines) that serves static files and exposes `/api/event` (public) + `/admin` routes (protected). Postgres on Railway stores all events in a single `events` table. A lightweight client-side tracker (~80 lines) collects events via `sendBeacon`. The admin dashboard is a single HTML page with vanilla JS charts matching the turnos dark theme.

**Tech Stack:** Express, pg (node-postgres), crypto (HMAC auth), vanilla JS/CSS (no new frontend deps)

---

### Task 1: Express Server

**Files:**
- Create: `server.js`
- Modify: `package.json`

**Step 1: Install dependencies**

Run: `npm install express pg`
Expected: package.json updated with express and pg

**Step 2: Create server.js**

```js
const express = require('express');
const path = require('path');
const crypto = require('crypto');
const { Pool } = require('pg');

const app = express();
const PORT = process.env.PORT || 3000;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD || 'changeme';
const SECRET = process.env.SECRET || crypto.randomBytes(32).toString('hex');

// Postgres
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Init DB
pool.query(`
  CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL,
    page TEXT,
    target TEXT,
    referrer TEXT,
    utm_source TEXT,
    device TEXT,
    session_id TEXT,
    value JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
  )
`).catch(err => console.error('DB init error:', err));

// Create indexes for common queries
pool.query(`
  CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
  CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at);
  CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
  CREATE INDEX IF NOT EXISTS idx_events_page ON events(page);
`).catch(() => {});

app.use(express.json({ limit: '10kb' }));

// --- Auth helpers ---
function makeToken() {
  const expires = Date.now() + 24 * 60 * 60 * 1000;
  const sig = crypto.createHmac('sha256', SECRET).update(String(expires)).digest('hex');
  return `${expires}.${sig}`;
}

function checkToken(token) {
  if (!token) return false;
  const [expires, sig] = token.split('.');
  if (Date.now() > Number(expires)) return false;
  const expected = crypto.createHmac('sha256', SECRET).update(expires).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(sig, 'hex'), Buffer.from(expected, 'hex'));
}

function parseCookies(header) {
  const cookies = {};
  (header || '').split(';').forEach(c => {
    const [k, v] = c.trim().split('=');
    if (k) cookies[k] = v;
  });
  return cookies;
}

function requireAdmin(req, res, next) {
  const cookies = parseCookies(req.headers.cookie);
  if (checkToken(cookies.admin_token)) return next();
  res.status(401).json({ error: 'unauthorized' });
}

// --- Public: Event tracking ---
app.post('/api/event', async (req, res) => {
  const events = Array.isArray(req.body) ? req.body : [req.body];
  if (events.length > 50) return res.status(400).json({ error: 'too many events' });

  try {
    const values = [];
    const params = [];
    let i = 1;
    for (const e of events) {
      values.push(`($${i++},$${i++},$${i++},$${i++},$${i++},$${i++},$${i++},$${i++})`);
      params.push(
        String(e.type || 'unknown').slice(0, 50),
        (e.page || '').slice(0, 200),
        (e.target || '').slice(0, 200),
        (e.referrer || '').slice(0, 500),
        (e.utm_source || '').slice(0, 100),
        (e.device || '').slice(0, 20),
        (e.session_id || '').slice(0, 50),
        e.value ? JSON.stringify(e.value) : null
      );
    }
    await pool.query(
      `INSERT INTO events (type,page,target,referrer,utm_source,device,session_id,value) VALUES ${values.join(',')}`,
      params
    );
    res.status(204).end();
  } catch (err) {
    console.error('Track error:', err.message);
    res.status(500).json({ error: 'db error' });
  }
});

// --- Admin: Login ---
app.post('/admin/login', (req, res) => {
  if (req.body.password === ADMIN_PASSWORD) {
    const token = makeToken();
    res.setHeader('Set-Cookie', `admin_token=${token}; Path=/admin; HttpOnly; SameSite=Strict; Max-Age=86400${process.env.NODE_ENV === 'production' ? '; Secure' : ''}`);
    res.json({ ok: true });
  } else {
    res.status(401).json({ error: 'wrong password' });
  }
});

// --- Admin: Data API ---
app.get('/admin/api/summary', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';

  try {
    const [visitors, pageviews, avgTime, bounceRate] = await Promise.all([
      pool.query(`SELECT COUNT(DISTINCT session_id) as n FROM events WHERE type='pageview' AND created_at > NOW() - $1::interval`, [interval]),
      pool.query(`SELECT COUNT(*) as n FROM events WHERE type='pageview' AND created_at > NOW() - $1::interval`, [interval]),
      pool.query(`SELECT AVG((value->>'seconds')::float) as n FROM events WHERE type='page_exit' AND created_at > NOW() - $1::interval`, [interval]),
      pool.query(`
        SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE cnt = 1) / NULLIF(COUNT(*), 0), 1) as n
        FROM (SELECT session_id, COUNT(*) as cnt FROM events WHERE type='pageview' AND created_at > NOW() - $1::interval GROUP BY session_id) s
      `, [interval])
    ]);
    res.json({
      visitors: Number(visitors.rows[0].n),
      pageviews: Number(pageviews.rows[0].n),
      avg_time: Math.round(Number(avgTime.rows[0].n) || 0),
      bounce_rate: Number(bounceRate.rows[0].n) || 0
    });
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/referrers', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';
  try {
    const r = await pool.query(`
      SELECT COALESCE(NULLIF(referrer,''), 'direto') as source, COUNT(*) as visits, COUNT(DISTINCT session_id) as sessions
      FROM events WHERE type='pageview' AND created_at > NOW() - $1::interval
      GROUP BY source ORDER BY visits DESC LIMIT 20
    `, [interval]);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/utm', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';
  try {
    const r = await pool.query(`
      SELECT COALESCE(NULLIF(utm_source,''), 'none') as source, COUNT(DISTINCT session_id) as sessions
      FROM events WHERE type='pageview' AND created_at > NOW() - $1::interval
      GROUP BY source ORDER BY sessions DESC LIMIT 10
    `, [interval]);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/devices', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';
  try {
    const r = await pool.query(`
      SELECT COALESCE(NULLIF(device,''), 'unknown') as device, COUNT(DISTINCT session_id) as sessions
      FROM events WHERE type='pageview' AND created_at > NOW() - $1::interval
      GROUP BY device ORDER BY sessions DESC
    `, [interval]);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/pages', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';
  try {
    const r = await pool.query(`
      SELECT page, COUNT(*) as views, COUNT(DISTINCT session_id) as sessions
      FROM events WHERE type='pageview' AND created_at > NOW() - $1::interval
      GROUP BY page ORDER BY views DESC
    `, [interval]);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/scroll', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';
  try {
    const r = await pool.query(`
      SELECT page, (value->>'depth')::int as depth, COUNT(*) as n
      FROM events WHERE type='scroll' AND created_at > NOW() - $1::interval
      GROUP BY page, depth ORDER BY page, depth
    `, [interval]);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/clicks', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';
  try {
    const r = await pool.query(`
      SELECT target, COUNT(*) as clicks
      FROM events WHERE type='click' AND created_at > NOW() - $1::interval
      GROUP BY target ORDER BY clicks DESC LIMIT 30
    `, [interval]);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/sections', requireAdmin, async (req, res) => {
  const range = req.query.range || '24h';
  const intervals = { '24h': '24 hours', '7d': '7 days', '30d': '30 days', 'all': '100 years' };
  const interval = intervals[range] || '24 hours';
  try {
    const r = await pool.query(`
      SELECT target as section, ROUND(AVG((value->>'seconds')::float)) as avg_time, COUNT(DISTINCT session_id) as visitors
      FROM events WHERE type='section_time' AND created_at > NOW() - $1::interval
      GROUP BY target ORDER BY visitors DESC
    `, [interval]);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

app.get('/admin/api/live', requireAdmin, async (req, res) => {
  try {
    const r = await pool.query(`
      SELECT type, page, target, device, created_at FROM events ORDER BY created_at DESC LIMIT 50
    `);
    res.json(r.rows);
  } catch (err) { res.status(500).json({ error: err.message }); }
});

// --- Admin: Dashboard HTML ---
app.get('/admin', (req, res) => {
  const cookies = parseCookies(req.headers.cookie);
  if (checkToken(cookies.admin_token)) {
    res.sendFile(path.join(__dirname, 'admin.html'));
  } else {
    res.sendFile(path.join(__dirname, 'admin-login.html'));
  }
});

// --- Static files (must be last) ---
app.use(express.static('.', { maxAge: process.env.NODE_ENV === 'production' ? '1h' : 0 }));

app.listen(PORT, () => console.log(`turnos listening on :${PORT}`));
```

**Step 3: Update package.json**

Change the `start` script and add `express` + `pg` as dependencies:

```json
{
  "name": "turnos",
  "private": true,
  "scripts": {
    "start": "node server.js",
    "dev": "node server.js"
  },
  "dependencies": {
    "express": "^4.21.0",
    "pg": "^8.13.0"
  },
  "devDependencies": {
    "@svg-maps/brazil": "^2.0.0"
  }
}
```

**Step 4: Run and verify server serves static files**

Run: `node server.js`
Expected: "turnos listening on :3000" and site loads at localhost:3000

**Step 5: Commit**

```bash
git add server.js package.json
git commit -m "feat: add Express server with event tracking and admin API"
```

---

### Task 2: Client-Side Tracker

**Files:**
- Create: `js/tracker.js`
- Modify: `index.html`, `2turno.html`, `analise.html`, `politico.html`, `mapa.html` (add script tag)

**Step 1: Create js/tracker.js**

```js
!function(){
  // --- Config ---
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

  // --- Level 1: Automatic ---
  track('pageview');

  // Page exit (time on page)
  var t0 = Date.now();
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') {
      track('page_exit', '', { seconds: Math.round((Date.now() - t0) / 1000) });
      flush();
    }
  });

  // Scroll depth
  var scrolled = {};
  window.addEventListener('scroll', debounce(function() {
    var pct = Math.round(100 * (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight);
    [25, 50, 75, 100].forEach(function(d) {
      if (pct >= d && !scrolled[d]) { scrolled[d] = 1; track('scroll', '', { depth: d }); }
    });
  }, 300), { passive: true });

  // --- Level 2: Clicks ---
  document.addEventListener('click', function(e) {
    var el = e.target.closest('[data-track], a, button, .tile, .theme-toggle, .help-btn, th.sort');
    if (!el) return;

    // Explicit data-track
    if (el.dataset.track) { track('click', el.dataset.track); return; }

    // Cartogram tile
    if (el.closest('.tile')) { var t = el.closest('.tile'); var u = t.querySelector('.u'); track('click', 'mapa.' + (u ? u.textContent : 'tile')); return; }

    // Hemicycle circle
    if (el.tagName === 'circle') { track('click', 'hemiciclo.circle'); return; }

    // Theme toggle
    if (el.closest('.theme-toggle')) { track('click', 'tema.' + (document.documentElement.dataset.theme || 'toggle')); return; }

    // Help button
    if (el.closest('.help-btn')) { track('click', 'ajuda'); return; }

    // Table sort
    if (el.matches('th.sort')) { track('click', 'tabela.sort.' + (el.textContent || '').trim().slice(0, 30)); return; }

    // Nav links
    if (el.closest('.nav-links') && el.tagName === 'A') { track('click', 'nav.' + (el.getAttribute('href') || '').replace('#', '')); return; }

    // External links
    if (el.tagName === 'A' && el.hostname !== location.hostname) { track('click', 'ext.' + el.hostname + el.pathname.slice(0, 50)); return; }

    // Internal links with candidate info
    if (el.tagName === 'A' && el.href) {
      var text = (el.textContent || '').trim().slice(0, 40);
      track('click', 'link.' + text);
    }

    // Details/accordion
    if (el.tagName === 'SUMMARY' || el.closest('summary')) {
      var det = el.closest('details');
      track('click', 'accordion.' + (det ? (det.querySelector('summary').textContent || '').trim().slice(0, 40) : 'unknown'));
    }
  }, true);

  // --- Level 3: Rich interactions ---

  // Section time (IntersectionObserver)
  var sectionTimers = {};
  if (window.IntersectionObserver) {
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        var id = entry.target.id || entry.target.querySelector('h2,h3')?.textContent?.trim().slice(0, 40) || 'unknown';
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

  // Cartogram hover (debounced)
  document.addEventListener('mouseover', debounce(function(e) {
    var tile = e.target.closest('.tile');
    if (tile) {
      var u = tile.querySelector('.u');
      track('hover', 'mapa.' + (u ? u.textContent : 'tile'));
    }
  }, 500));

  // --- Utilities ---
  function debounce(fn, ms) {
    var t;
    return function() {
      var self = this, args = arguments;
      clearTimeout(t);
      t = setTimeout(function() { fn.apply(self, args); }, ms);
    };
  }

  // --- Batch flush ---
  setInterval(flush, BATCH_INTERVAL);
  window.addEventListener('beforeunload', flush);
}();
```

**Step 2: Add tracker script to all HTML pages**

Add this line right after the `<script src="js/shared.js"></script>` in each HTML file:

```html
<script src="js/tracker.js"></script>
```

Files to modify:
- `index.html` — find `<script src="js/shared.js"></script>`, add tracker after
- `2turno.html` — same
- `analise.html` — same
- `politico.html` — same
- `mapa.html` — same

Do NOT add to `linkedin-carousel.html` or `admin.html`.

**Step 3: Verify tracker fires in dev tools**

Run: `node server.js`, open localhost:3000
Expected: Network tab shows POST to `/api/event` after 5 seconds with pageview event

**Step 4: Commit**

```bash
git add js/tracker.js index.html 2turno.html analise.html politico.html mapa.html
git commit -m "feat: add client-side event tracker to all pages"
```

---

### Task 3: Admin Login Page

**Files:**
- Create: `admin-login.html`

**Step 1: Create admin-login.html**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin — turnos</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap">
<style>
:root{--bg:#1d1b17;--surface:#2a2722;--fg:#f6f3ec;--muted:#a09888;--accent:#8a6d1c;--line:#333;--serif:'Source Serif 4',Georgia,serif;--sans:'IBM Plex Sans',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:var(--sans);display:flex;align-items:center;justify-content:center;min-height:100vh}
.login{background:var(--surface);border-radius:16px;padding:48px;width:380px;max-width:90vw}
h1{font-family:var(--serif);font-size:28px;margin-bottom:8px}
p{color:var(--muted);font-size:14px;margin-bottom:32px}
label{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:8px}
input{width:100%;padding:12px 16px;background:var(--bg);border:1px solid var(--line);border-radius:8px;color:var(--fg);font-size:16px;font-family:var(--sans);outline:none}
input:focus{border-color:var(--accent)}
button{width:100%;padding:14px;background:var(--accent);color:#fff;border:none;border-radius:8px;font-size:16px;font-weight:600;font-family:var(--sans);cursor:pointer;margin-top:16px}
button:hover{opacity:.9}
.err{color:#cc4a43;font-size:14px;margin-top:12px;display:none}
</style>
</head>
<body>
<div class="login">
  <h1>turnos admin</h1>
  <p>Painel de métricas do site.</p>
  <form id="f">
    <label for="pw">Senha</label>
    <input type="password" id="pw" name="password" autocomplete="current-password" required>
    <button type="submit">Entrar</button>
    <div class="err" id="err">Senha incorreta.</div>
  </form>
</div>
<script>
document.getElementById('f').onsubmit = async function(e) {
  e.preventDefault();
  var r = await fetch('/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password: document.getElementById('pw').value })
  });
  if (r.ok) { location.reload(); }
  else { document.getElementById('err').style.display = 'block'; }
};
</script>
</body>
</html>
```

**Step 2: Commit**

```bash
git add admin-login.html
git commit -m "feat: add admin login page"
```

---

### Task 4: Admin Dashboard Page

**Files:**
- Create: `admin.html`

**Step 1: Create admin.html**

This is the largest file. The dashboard is a single HTML page with inline styles (matching turnos dark theme) and vanilla JS that fetches from the `/admin/api/*` endpoints.

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin — turnos</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Source+Serif+4:opsz,wght@8..60,600;8..60,700&display=swap">
<style>
:root{--bg:#1d1b17;--surface:#2a2722;--fg:#f6f3ec;--muted:#a09888;--accent:#8a6d1c;--line:#333;--lula:#cc4a43;--flavio:#4a74c6;--serif:'Source Serif 4',Georgia,serif;--sans:'IBM Plex Sans',system-ui,sans-serif}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:14px;padding:32px}
.container{max-width:1100px;margin:0 auto}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;border-bottom:1px solid var(--line);padding-bottom:20px}
h1{font-family:var(--serif);font-size:28px}
.range-btns{display:flex;gap:6px}
.range-btns button{background:var(--surface);border:1px solid var(--line);color:var(--muted);padding:6px 14px;border-radius:6px;cursor:pointer;font-family:var(--sans);font-size:13px}
.range-btns button.active{background:var(--accent);color:#fff;border-color:var(--accent)}
h2{font-family:var(--serif);font-size:20px;margin:32px 0 16px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px}
.card{background:var(--surface);border-radius:12px;padding:20px}
.card .label{font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:6px}
.card .value{font-family:var(--serif);font-size:36px;font-weight:700}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
table{width:100%;border-collapse:collapse;background:var(--surface);border-radius:12px;overflow:hidden}
th{text-align:left;padding:10px 14px;font-size:12px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid var(--line)}
td{padding:10px 14px;border-bottom:1px solid var(--line);font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:none}
.bar-row{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.bar-row .name{width:120px;font-size:13px;color:var(--muted);text-align:right;flex:none}
.bar-row .bar{height:24px;border-radius:4px;background:var(--accent);min-width:2px;display:flex;align-items:center;padding:0 8px;font-size:12px;font-weight:600;color:#fff;white-space:nowrap}
.live{background:var(--surface);border-radius:12px;padding:16px;max-height:400px;overflow-y:auto;font-size:13px;font-family:'IBM Plex Sans',monospace}
.live .ev{padding:4px 0;border-bottom:1px solid var(--line);display:flex;gap:12px}
.live .ev:last-child{border-bottom:none}
.live .time{color:var(--muted);width:60px;flex:none}
.live .type{color:var(--accent);width:80px;flex:none;font-weight:600}
.funnel .row{display:flex;align-items:center;gap:12px;margin-bottom:6px}
.funnel .row .sect{width:180px;font-size:13px;text-align:right;flex:none}
.funnel .row .fbar{height:28px;border-radius:4px;background:var(--flavio);display:flex;align-items:center;padding:0 10px;font-size:12px;font-weight:600;color:#fff}
@media(max-width:768px){.cards{grid-template-columns:1fr 1fr}.grid2{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>turnos · admin</h1>
    <div class="range-btns">
      <button data-range="24h" class="active">24h</button>
      <button data-range="7d">7d</button>
      <button data-range="30d">30d</button>
      <button data-range="all">Tudo</button>
    </div>
  </header>

  <!-- Summary cards -->
  <div class="cards">
    <div class="card"><div class="label">Visitantes</div><div class="value" id="vVisitors">—</div></div>
    <div class="card"><div class="label">Pageviews</div><div class="value" id="vPageviews">—</div></div>
    <div class="card"><div class="label">Tempo médio</div><div class="value" id="vTime">—</div></div>
    <div class="card"><div class="label">Bounce rate</div><div class="value" id="vBounce">—</div></div>
  </div>

  <!-- Referrers + Devices -->
  <h2>De onde vêm</h2>
  <div class="grid2">
    <div>
      <h3 style="font-size:14px;color:var(--muted);margin-bottom:12px">UTM Source</h3>
      <div id="utmBars"></div>
    </div>
    <div>
      <h3 style="font-size:14px;color:var(--muted);margin-bottom:12px">Dispositivo</h3>
      <div id="deviceBars"></div>
    </div>
  </div>
  <h3 style="font-size:14px;color:var(--muted);margin:20px 0 12px">Top referrers</h3>
  <table><thead><tr><th>Origem</th><th>Visitas</th><th>Sessões</th></tr></thead><tbody id="refTable"></tbody></table>

  <!-- Pages + Scroll -->
  <h2>O que acessam</h2>
  <div class="grid2">
    <div>
      <h3 style="font-size:14px;color:var(--muted);margin-bottom:12px">Pageviews por página</h3>
      <div id="pageBars"></div>
    </div>
    <div>
      <h3 style="font-size:14px;color:var(--muted);margin-bottom:12px">Scroll depth</h3>
      <div id="scrollBars"></div>
    </div>
  </div>

  <!-- Clicks -->
  <h2>Onde clicam</h2>
  <table><thead><tr><th>Elemento</th><th>Cliques</th></tr></thead><tbody id="clickTable"></tbody></table>

  <!-- Funnel -->
  <h2>Tempo por seção (funil)</h2>
  <div class="funnel" id="funnel"></div>

  <!-- Live -->
  <h2>Tempo real</h2>
  <div class="live" id="live"><em style="color:var(--muted)">Carregando...</em></div>
</div>

<script>
!function(){
  var range = '24h';
  var fmtN = function(n) { return Number(n).toLocaleString('pt-BR'); };

  function api(path) {
    return fetch('/admin/api/' + path + '?range=' + range).then(function(r) {
      if (r.status === 401) { location.reload(); throw new Error('auth'); }
      return r.json();
    });
  }

  function makeBars(container, data, nameKey, valKey, color) {
    var el = document.getElementById(container);
    var max = Math.max.apply(null, data.map(function(d) { return Number(d[valKey]); })) || 1;
    el.innerHTML = data.slice(0, 8).map(function(d) {
      var pct = Math.max(2, (Number(d[valKey]) / max) * 100);
      return '<div class="bar-row"><span class="name">' + d[nameKey] + '</span><div class="bar" style="width:' + pct + '%;background:' + (color || 'var(--accent)') + '">' + fmtN(d[valKey]) + '</div></div>';
    }).join('');
  }

  function load() {
    api('summary').then(function(d) {
      document.getElementById('vVisitors').textContent = fmtN(d.visitors);
      document.getElementById('vPageviews').textContent = fmtN(d.pageviews);
      document.getElementById('vTime').textContent = d.avg_time + 's';
      document.getElementById('vBounce').textContent = d.bounce_rate + '%';
    });

    api('referrers').then(function(rows) {
      document.getElementById('refTable').innerHTML = rows.map(function(r) {
        return '<tr><td>' + r.source + '</td><td>' + fmtN(r.visits) + '</td><td>' + fmtN(r.sessions) + '</td></tr>';
      }).join('');
    });

    api('utm').then(function(rows) { makeBars('utmBars', rows, 'source', 'sessions'); });
    api('devices').then(function(rows) { makeBars('deviceBars', rows, 'device', 'sessions', 'var(--flavio)'); });

    api('pages').then(function(rows) { makeBars('pageBars', rows, 'page', 'views', 'var(--lula)'); });

    api('scroll').then(function(rows) {
      // Group by page, show depth distribution
      var pages = {};
      rows.forEach(function(r) { if (!pages[r.page]) pages[r.page] = {}; pages[r.page][r.depth] = Number(r.n); });
      var el = document.getElementById('scrollBars');
      el.innerHTML = Object.keys(pages).map(function(p) {
        var d = pages[p];
        return '<div style="margin-bottom:8px"><span style="font-size:13px;color:var(--muted)">' + p + '</span>' +
          [25,50,75,100].map(function(depth) {
            return '<span style="display:inline-block;margin-left:8px;font-size:12px;color:var(--fg)">' + depth + '%: ' + (d[depth] || 0) + '</span>';
          }).join('') + '</div>';
      }).join('');
    });

    api('clicks').then(function(rows) {
      document.getElementById('clickTable').innerHTML = rows.map(function(r) {
        return '<tr><td>' + r.target + '</td><td>' + fmtN(r.clicks) + '</td></tr>';
      }).join('');
    });

    api('sections').then(function(rows) {
      var max = Math.max.apply(null, rows.map(function(r) { return Number(r.visitors); })) || 1;
      document.getElementById('funnel').innerHTML = rows.map(function(r) {
        var pct = Math.max(5, (Number(r.visitors) / max) * 100);
        return '<div class="row"><span class="sect">' + r.section + '</span><div class="fbar" style="width:' + pct + '%">' + r.avg_time + 's · ' + fmtN(r.visitors) + ' vis</div></div>';
      }).join('');
    });
  }

  function loadLive() {
    api('live').then(function(rows) {
      document.getElementById('live').innerHTML = rows.map(function(r) {
        var d = new Date(r.created_at);
        var time = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        return '<div class="ev"><span class="time">' + time + '</span><span class="type">' + r.type + '</span><span>' + (r.target || r.page || '') + '</span></div>';
      }).join('');
    });
  }

  // Range buttons
  document.querySelectorAll('.range-btns button').forEach(function(btn) {
    btn.onclick = function() {
      document.querySelector('.range-btns .active').classList.remove('active');
      btn.classList.add('active');
      range = btn.dataset.range;
      load();
    };
  });

  load();
  loadLive();
  setInterval(loadLive, 10000);
}();
</script>
</body>
</html>
```

**Step 2: Verify admin page loads**

Run: Set `ADMIN_PASSWORD=test` env, `node server.js`, go to `localhost:3000/admin`
Expected: Login page appears, entering "test" shows dashboard

**Step 3: Commit**

```bash
git add admin.html admin-login.html
git commit -m "feat: add admin dashboard with analytics views"
```

---

### Task 5: Railway Deployment

**Files:**
- Modify: Railway project settings (UI)

**Step 1: Install npm dependencies locally**

Run: `npm install`
Expected: `node_modules/` created with express and pg

**Step 2: Add Postgres to Railway**

In Railway dashboard:
1. Click "New" → "Database" → "PostgreSQL"
2. Copy the `DATABASE_URL` connection string
3. In the turnos service, add environment variables:
   - `DATABASE_URL` = (the Postgres connection string)
   - `ADMIN_PASSWORD` = (choose a strong password)
   - `SECRET` = (run `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` and paste result)
   - `NODE_ENV` = `production`

**Step 3: Push and deploy**

Run: `git push`
Expected: Railway auto-deploys, runs `npm install` + `node server.js`

**Step 4: Verify production**

1. Visit `https://1e2turnos.up.railway.app` — site works as before
2. Visit `https://1e2turnos.up.railway.app/admin` — login page appears
3. Enter password → dashboard loads
4. Open main site in another tab → events appear in live feed within 10s

**Step 5: Commit package-lock.json**

```bash
git add package-lock.json
git commit -m "chore: add package-lock.json for reproducible builds"
```

---

### Task 6: Gitignore and Cleanup

**Files:**
- Modify: `.gitignore`

**Step 1: Update .gitignore**

Add these lines:

```
node_modules/
.claude/
data/_*.json
.env
```

**Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: update gitignore with env and node_modules"
```
