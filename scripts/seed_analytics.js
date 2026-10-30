/**
 * Seed analytics data — generates 30 days of realistic traffic
 * Run: node scripts/seed_analytics.js
 */
require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Config
const DAYS = 30;
const BASE_DAILY_VISITORS = 120;
const GROWTH_FACTOR = 1.06; // 6% daily growth (viral election content)

// Realistic distributions
const PAGES = [
  { path: '/', weight: 30 },
  { path: '/2turno.html', weight: 25 },
  { path: '/mapa.html', weight: 15 },
  { path: '/analise.html', weight: 10 },
  { path: '/politico.html?id=280002551544', weight: 5 }, // Flávio
  { path: '/politico.html?id=280002542548', weight: 5 }, // Lula
  { path: '/politico.html?id=20002553350', weight: 2 },  // JHC
  { path: '/politico.html?id=130002552296', weight: 2 },  // Cleitinho
  { path: '/politico.html?id=250002541303', weight: 2 },  // Tarcísio
  { path: '/politico.html?id=70002552936', weight: 2 },   // Michelle
  { path: '/politico.html?id=250002532353', weight: 1 },   // Coronel Telhada
  { path: '/politico.html?id=250002535958', weight: 1 },   // Luiz Philippe
];

const REFERRERS = [
  { source: '', weight: 30 },  // direto
  { source: 'https://t.co/abc123', weight: 15 },
  { source: 'https://www.google.com/', weight: 12 },
  { source: 'https://l.instagram.com/', weight: 10 },
  { source: 'https://www.facebook.com/', weight: 8 },
  { source: 'https://www.reddit.com/r/brasil/', weight: 5 },
  { source: 'https://news.ycombinator.com/', weight: 3 },
  { source: 'https://bsky.app/', weight: 3 },
  { source: 'https://www.linkedin.com/', weight: 4 },
  { source: 'https://web.whatsapp.com/', weight: 6 },
  { source: 'https://t.me/', weight: 4 },
];

const UTM_SOURCES = [
  { source: '', weight: 55 },
  { source: 'twitter', weight: 12 },
  { source: 'instagram', weight: 8 },
  { source: 'facebook', weight: 6 },
  { source: 'whatsapp', weight: 7 },
  { source: 'telegram', weight: 4 },
  { source: 'linkedin', weight: 3 },
  { source: 'reddit', weight: 3 },
  { source: 'google', weight: 2 },
];

const DEVICES = [
  { type: 'mobile', weight: 62 },
  { type: 'desktop', weight: 33 },
  { type: 'tablet', weight: 5 },
];

const SCROLL_DEPTHS = [25, 50, 75, 90, 100];

const CLICK_TARGETS = [
  'nav:Presidente', 'nav:Mapa', 'nav:Governadores', 'nav:Senado',
  'nav:Câmara', 'nav:2º turno', 'nav:Análise',
  'theme-toggle', 'back-top',
  'tseLink:Flávio Bolsonaro', 'tseLink:Lula', 'tseLink:Tarcísio',
  'tseLink:Michelle Bolsonaro', 'tseLink:Nikolas Ferreira',
  'details:toggle', 'sort:table',
  'link:2turno.html', 'link:mapa.html', 'link:analise.html',
];

const SECTIONS = [
  'resumo', 'presidente', 'mapa', 'governadores', 'senado',
  'camara', 'congresso', 'estados', 'calendario', 'ressalvas', 'fontes'
];

// Helpers
function pick(arr) {
  const total = arr.reduce((s, x) => s + x.weight, 0);
  let r = Math.random() * total;
  for (const item of arr) {
    r -= item.weight;
    if (r <= 0) return item;
  }
  return arr[0];
}

function randomBetween(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function hourWeight(hour) {
  // Brazilian traffic pattern: peaks at 10h, 14h, 21h
  const weights = [2,1,1,1,1,2,3,5,7,9,10,9,8,9,10,9,8,7,8,10,11,10,7,4];
  return weights[hour];
}

function generateSessionId() {
  return crypto.randomUUID ? crypto.randomUUID().slice(0,8) : Math.random().toString(36).slice(2,10);
}

async function seed() {
  console.log('Connecting to database...');
  await pool.query('DELETE FROM events'); // clean slate
  console.log('Cleared existing events');

  const now = new Date();
  let totalEvents = 0;
  const batchSize = 500;
  let batch = [];

  for (let day = DAYS; day >= 0; day--) {
    const date = new Date(now);
    date.setDate(date.getDate() - day);

    // Weekend gets ~70% traffic, election day (Sunday) gets 3x
    const dow = date.getDay();
    let dayMultiplier = 1;
    if (dow === 0 || dow === 6) dayMultiplier = 0.7;

    // Growth over time
    const growthMultiplier = Math.pow(GROWTH_FACTOR, DAYS - day);

    // Spike on specific days (simulate viral moments)
    const dayOfMonth = date.getDate();
    if (day <= 3) dayMultiplier *= 2.5; // last 3 days = post-election buzz
    else if (day <= 7) dayMultiplier *= 1.8; // election week

    const dailyVisitors = Math.round(BASE_DAILY_VISITORS * dayMultiplier * growthMultiplier);

    for (let v = 0; v < dailyVisitors; v++) {
      const sessionId = generateSessionId();
      const device = pick(DEVICES).type;
      const referrer = pick(REFERRERS).source;
      const utmSource = pick(UTM_SOURCES).source;

      // Pick hour based on traffic pattern
      const hourWeights = Array.from({length: 24}, (_, h) => ({weight: hourWeight(h), hour: h}));
      const hour = pick(hourWeights).hour;
      const minute = randomBetween(0, 59);
      const second = randomBetween(0, 59);

      const ts = new Date(date);
      ts.setHours(hour, minute, second, randomBetween(0, 999));

      // Number of pages this session views (1-6, most view 1-2)
      const pagesViewed = Math.random() < 0.35 ? 1 :
                          Math.random() < 0.55 ? 2 :
                          Math.random() < 0.75 ? 3 : randomBetween(4, 6);

      const visitedPages = new Set();

      for (let p = 0; p < pagesViewed; p++) {
        let page = pick(PAGES).path;
        if (visitedPages.has(page) && PAGES.length > visitedPages.size) {
          // Pick a different page
          for (let attempt = 0; attempt < 5; attempt++) {
            page = pick(PAGES).path;
            if (!visitedPages.has(page)) break;
          }
        }
        visitedPages.add(page);

        const pageTs = new Date(ts.getTime() + p * randomBetween(15, 180) * 1000);

        // Pageview event
        batch.push([
          'pageview', page, '', p === 0 ? referrer : '', utmSource, device, sessionId, null, pageTs
        ]);

        // Scroll depth (70% of pageviews)
        if (Math.random() < 0.7) {
          const maxDepth = SCROLL_DEPTHS[randomBetween(0, SCROLL_DEPTHS.length - 1)];
          batch.push([
            'scroll', page, '', '', '', device, sessionId,
            JSON.stringify({ depth: maxDepth }),
            new Date(pageTs.getTime() + randomBetween(5, 60) * 1000)
          ]);
        }

        // Clicks (40% chance per page)
        if (Math.random() < 0.4) {
          const nClicks = randomBetween(1, 3);
          for (let c = 0; c < nClicks; c++) {
            const target = CLICK_TARGETS[randomBetween(0, CLICK_TARGETS.length - 1)];
            batch.push([
              'click', page, target, '', '', device, sessionId, null,
              new Date(pageTs.getTime() + randomBetween(3, 90) * 1000)
            ]);
          }
        }

        // Section view (on index page, 60% chance)
        if (page === '/' && Math.random() < 0.6) {
          const nSections = randomBetween(1, 5);
          for (let s = 0; s < nSections; s++) {
            const section = SECTIONS[randomBetween(0, SECTIONS.length - 1)];
            batch.push([
              'section_view', page, section, '', '', device, sessionId, null,
              new Date(pageTs.getTime() + randomBetween(5, 120) * 1000)
            ]);
          }
        }

        // Page exit (last page only)
        if (p === pagesViewed - 1) {
          const timeOnPage = randomBetween(8, 300);
          batch.push([
            'page_exit', page, '', '', '', device, sessionId,
            JSON.stringify({ seconds: timeOnPage }),
            new Date(pageTs.getTime() + timeOnPage * 1000)
          ]);
        }
      }
    }

    // Flush batch periodically (keep under PG param limit)
    while (batch.length >= 200) {
      const chunk = batch.splice(0, 200);
      await insertBatch(chunk);
      totalEvents += chunk.length;
    }
    process.stdout.write(`\r  Day -${day}: ${dailyVisitors} visitors | Total events: ${totalEvents}`);
  }

  // Final flush
  if (batch.length > 0) {
    await insertBatch(batch);
    totalEvents += batch.length;
  }

  console.log(`\n\nDone! Inserted ${totalEvents.toLocaleString()} events over ${DAYS} days.`);

  // Quick stats
  const stats = await pool.query(`
    SELECT
      COUNT(*) as total_events,
      COUNT(DISTINCT session_id) as unique_sessions,
      COUNT(*) FILTER (WHERE type='pageview') as pageviews,
      COUNT(*) FILTER (WHERE type='click') as clicks,
      COUNT(*) FILTER (WHERE type='scroll') as scrolls,
      MIN(created_at)::date as first_day,
      MAX(created_at)::date as last_day
    FROM events
  `);
  console.log('\nStats:', stats.rows[0]);

  await pool.end();
}

async function insertBatch(rows) {
  const values = [];
  const params = [];
  let i = 1;
  for (const [type, page, target, referrer, utm, device, session, value, ts] of rows) {
    values.push(`($${i++},$${i++},$${i++},$${i++},$${i++},$${i++},$${i++},$${i++},$${i++})`);
    params.push(type, page, target, referrer, utm, device, session, value, ts);
  }
  await pool.query(
    `INSERT INTO events (type,page,target,referrer,utm_source,device,session_id,value,created_at) VALUES ${values.join(',')}`,
    params
  );
}

seed().catch(err => { console.error('Seed error:', err); process.exit(1); });
