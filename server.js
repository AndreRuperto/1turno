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
