# Mapa Interativo — Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `mapa.html` page to the turnos site with the interactive Leaflet election map from apuracao-urnas, matching the existing design system, with cross-links to candidate profiles.

**Architecture:** Copy the Leaflet map page + data files from apuracao-urnas into turnos. Adapt the visual (colors, fonts, nav) to match turnos' shared.css. Add nav links in index.html and 2turno.html pointing to the new page. Municipality clicks link to politico.html profiles.

**Tech Stack:** Leaflet.js (CDN), GeoJSON (IBGE), vanilla JS, turnos shared.css/js.

---

## Source Files (apuracao-urnas)

These files from `D:\Projetos\apuracao-urnas` will be used:

| File | Size | Purpose |
|------|------|---------|
| `mapa.html` | ~25 KB | Leaflet map page (will be adapted) |
| `mun_geo.json` | ~2 MB | 5,570 municipality boundaries + vote data |
| `brazil-simple.json` | 28 KB | State boundaries (for state-level view) |
| `state_borders.json` | 81 KB | Internal state borders (no coastline) |
| `ra_geo.json` | ? | DF administrative regions (if exists) |

**NOT copied:** Python scripts, raw CSVs, build scripts, ibge_*.json — these stay in apuracao-urnas.

---

## Task 1: Copy data files

**Files:**
- Copy: `apuracao-urnas/mun_geo.json` → `turnos/data/mun_geo.json`
- Copy: `apuracao-urnas/brazil-simple.json` → `turnos/data/brazil-simple.json`
- Copy: `apuracao-urnas/state_borders.json` → `turnos/data/state_borders.json`
- Copy: `apuracao-urnas/ra_geo.json` → `turnos/data/ra_geo.json` (if exists)

**Step 1:** Copy files

```bash
cp d:/Projetos/apuracao-urnas/mun_geo.json d:/Projetos/turnos/data/
cp d:/Projetos/apuracao-urnas/brazil-simple.json d:/Projetos/turnos/data/
cp d:/Projetos/apuracao-urnas/state_borders.json d:/Projetos/turnos/data/
cp d:/Projetos/apuracao-urnas/ra_geo.json d:/Projetos/turnos/data/ 2>/dev/null
```

**Step 2:** Verify files exist and sizes are reasonable

```bash
ls -lh d:/Projetos/turnos/data/*.json
```

**Step 3:** Commit

```bash
cd d:/Projetos/turnos
git add data/mun_geo.json data/brazil-simple.json data/state_borders.json data/ra_geo.json
git commit -m "data: add GeoJSON files for interactive map"
```

---

## Task 2: Create mapa.html with turnos design system

**Files:**
- Create: `turnos/mapa.html`
- Reference: `apuracao-urnas/mapa.html` (source of map logic)
- Reference: `turnos/2turno.html` (template for nav/head/footer structure)

**Step 1:** Create `mapa.html`

The page must:
- Use the same `<head>` structure as 2turno.html (favicon, fonts, shared.css)
- Include the topnav with links to index.html, 2turno.html, politico.html
- Load Leaflet from CDN
- Contain the full map logic from apuracao-urnas/mapa.html
- Adapt colors to use turnos CSS variables: `--lula`, `--flavio`, `--bg`, `--surface`, `--fg`, `--muted`, `--line`, `--accent`
- Adapt fonts to use `--serif` and `--sans`
- Support dark/light mode via turnos' theme toggle
- Include the sidebar with national result, regions, state list
- Include candidate photos in the national result panel
- Include state flags in tooltips
- Include the ESTADO/MUNICIPIO toggle
- Include the legend filter (clickable margin ranges)
- Include state border overlays in municipality view
- Include state labels (UF + % overlay)

**Key color mapping (apuracao-urnas → turnos):**
- `--red` / `--r2` → `--lula` / `--lula-mid`
- `--blu` / `--b2` → `--flavio` / `--flavio-mid`
- `--bg` (#0a0e1a) → `var(--bg)` (adapts to light/dark)
- `--s1` → `var(--surface)`
- `--tx` → `var(--fg)`
- `--t2` → `var(--muted)`
- `--bd` → `var(--line)`
- `--gld` → `var(--accent)`

**Layout:** Full viewport height below the topnav. Grid: map area (flex 1) + sidebar (340px). No `.wrap` max-width constraint — map needs full width.

**Data paths:** Change `fetch('mun_geo.json')` → `fetch('data/mun_geo.json')` etc.

**Step 2:** Test locally

```bash
cd d:/Projetos/turnos
npx http-server . -o -c-1
# Open http://localhost:8080/mapa.html
```

Verify:
- Map renders with Esri Dark Gray tiles
- States show colored by election result
- Zoom in shows municipalities
- Tooltips show flag + name + %
- Sidebar shows national result with photos
- ESTADO/MUNICIPIO toggle works
- Legend filter works
- State borders appear in municipality view
- Theme toggle switches colors
- Nav links work (back to 1turno, 2turno)

**Step 3:** Commit

```bash
git add mapa.html
git commit -m "feat: add interactive election map page"
```

---

## Task 3: Add nav links in index.html and 2turno.html

**Files:**
- Modify: `turnos/index.html` (nav-links section)
- Modify: `turnos/2turno.html` (nav-links section)

**Step 1:** In `index.html`, add a link to mapa.html in the nav-links div.

Find the nav-links div and add before the "2º turno" link:
```html
<a href="mapa.html" style="background:var(--accent);color:#fff;border-radius:99px">🗺 Mapa</a>
```

**Step 2:** In `2turno.html`, add the same link in the nav-links div, before the "← 1º turno" link:
```html
<a href="mapa.html" style="background:var(--accent);color:#fff;border-radius:99px">🗺 Mapa</a>
```

**Step 3:** In `mapa.html`, ensure the nav has links back:
```html
<a href="index.html">1º turno</a>
<a href="2turno.html">2º turno</a>
```

**Step 4:** Test navigation between all 4 pages works

**Step 5:** Commit

```bash
git add index.html 2turno.html
git commit -m "feat: add Mapa Interativo nav links"
```

---

## Task 4: Link municipalities to candidate profiles

**Files:**
- Modify: `turnos/mapa.html` (municipality click handler)
- Reference: `turnos/data/politicos.json` (candidate TSE IDs)

**Step 1:** In the municipality layer's `onEachFeature`, add a click handler that links to the winning candidate's profile:

The presidential candidates' TSE IDs are:
- Lula: `280002542548`
- Flávio Bolsonaro: `280002551544`

On municipality click:
```javascript
layer.on('click', () => {
  const winner = lula > flavio ? '280002542548' : '280002551544';
  // Open profile in same tab or new tab
  window.open('politico.html?id=' + winner, '_blank');
});
```

**Step 2:** Same for state layer clicks — clicking a state opens the winning candidate's profile

**Step 3:** Add a visual hint (cursor: pointer + tooltip note "Clique para ver perfil")

**Step 4:** Test: click a municipality → opens politico.html with correct candidate

**Step 5:** Commit

```bash
git add mapa.html
git commit -m "feat: link map clicks to candidate profiles"
```

---

## Task 5: Optimize for Railway deployment

**Files:**
- Check: `turnos/.gitignore` (ensure data/*.json not ignored)
- Check: total repo size stays reasonable

**Step 1:** Verify .gitignore allows the JSON data files

```bash
cat d:/Projetos/turnos/.gitignore
```

If `data/*.json` or `*.json` is ignored, add exceptions:
```
!data/mun_geo.json
!data/brazil-simple.json
!data/state_borders.json
```

**Step 2:** Check total deployment size

```bash
du -sh d:/Projetos/turnos --exclude=node_modules --exclude=.git
```

Expected: ~5 MB (was ~3 MB + ~2 MB mun_geo.json). Acceptable for Railway.

**Step 3:** Test production-like serving

```bash
cd d:/Projetos/turnos
npx http-server . -c-1
```

Navigate all pages, verify map loads, verify politico.html links work.

**Step 4:** Commit any .gitignore changes

```bash
git add .gitignore
git commit -m "chore: allow map data files in git"
```

---

## Task 6: Final testing & deploy

**Step 1:** Full test checklist

- [ ] `index.html` loads, nav has "Mapa" link
- [ ] `2turno.html` loads, nav has "Mapa" link
- [ ] `mapa.html` loads, map renders with states
- [ ] ESTADO/MUNICIPIO toggle works
- [ ] Zoom in shows municipalities with correct colors
- [ ] State borders appear between states (not on coastline)
- [ ] Tooltips show flag + name + % for states and municipalities
- [ ] Info box shows candidate photos
- [ ] Legend filter highlights matching municipalities
- [ ] State labels (UF + %) visible at reasonable zoom levels
- [ ] Dark mode toggle works (map tiles stay dark, sidebar adapts)
- [ ] Nav links cycle correctly: index ↔ 2turno ↔ mapa ↔ politico
- [ ] Municipality click opens candidate profile
- [ ] Mobile responsive: sidebar stacks below map

**Step 2:** Push to Railway

```bash
cd d:/Projetos/turnos
git push origin main
```

**Step 3:** Verify live at https://1turno.up.railway.app/mapa.html

---

## Notes

- **Data freshness:** The GeoJSON files are static snapshots from Oct 27, 2026 (2nd round). No need to update unless re-running apuracao-urnas pipeline.
- **mun_geo.json size (2 MB):** Acceptable for Railway. Gzip compression (automatic) brings it to ~500 KB over the wire.
- **Leaflet CDN:** Using unpkg CDN for leaflet.js/css. No local copy needed.
- **No build step:** Continues the turnos pattern of zero-build static files.
- **preferCanvas: true:** Critical for performance with 5,570 municipality polygons.
