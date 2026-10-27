# Página do Político — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a dynamic `politico.html` page showing each politician's profile (election results, patrimony, previous candidacies), fed by a pre-generated `data/politicos.json`.

**Architecture:** Single `politico.html` loads `data/politicos.json`, filters by `?id=tseCandidateId` from the URL. Data is generated offline via Eleições.dev MCP API. Same vanilla HTML/CSS/JS stack as the rest of the site.

**Tech Stack:** Vanilla HTML/JS, shared.css, Eleições.dev MCP API for data generation.

---

## Data Reference

### API: list_candidates
Returns per candidate: `id` (UUID), `tseCandidateId`, `ballotName`, `fullName`, `number`, `office`, `state`, `partyId`, `gender`, `race`, `education`, `occupation`, `totalAssets`, `photoUrl`, `coalitionName`, `result` (votes, voteShare, status, outcome, round).

Batch: up to 50 per page. Filters: office, state, outcome, round, q.

### API: get_candidate_filings(uuid)
Returns array of past candidacies: year, office, party, state, declaredAssets.

### API: list_candidate_assets(uuid)
Returns individual declared assets: description, value, type.

### JSON Target Structure
```json
{
  "280002551544": {
    "nome": "FLAVIO BOLSONARO",
    "nomeCompleto": "FLAVIO NANTES BOLSONARO",
    "partido": "PL",
    "numero": 22,
    "cargo": "presidente",
    "estado": "BR",
    "foto": "https://divulgacandcontas.tse.jus.br/...",
    "totalBens": 3200000,
    "coligacao": "...",
    "educacao": "SUPERIOR COMPLETO",
    "ocupacao": "SENADOR",
    "genero": "MASCULINO",
    "raca": "BRANCA",
    "uuid": "xxx-xxx-xxx",
    "resultado": { "turno": 1, "votos": 56104503, "pct": 47.03, "situacao": "2º turno" },
    "resultado2t": { "turno": 2, "votos": 59826041, "pct": 48.21, "situacao": "Não eleito" },
    "candidaturas": [
      { "ano": 2018, "cargo": "SENADOR", "estado": "RJ", "partido": "PSL", "bens": 1523000 }
    ]
  }
}
```

---

## Tasks

### Task 1: Create `politico.html` page with layout

**Files:**
- Create: `politico.html`

**Step 1:** Create `politico.html` with:
- Same `<head>` as index.html (charset, viewport, favicon, fonts, shared.css)
- `<title>` set dynamically via JS
- Navbar with links: Resultado, Patrimônio, Candidaturas + theme toggle + help button
- Nav brand links to `index.html`

**Step 2:** Add the header section (NOT accordion):
```html
<header class="pol-header">
  <img class="pol-photo" id="polPhoto" src="" alt="">
  <div>
    <div class="kicker" id="polKicker">...</div>
    <h1 id="polNome">Carregando...</h1>
    <p class="sub" id="polSub">...</p>
    <a id="polTse" class="pol-tse" href="#" target="_blank" rel="noopener">Ver no TSE ↗</a>
  </div>
</header>
```

**Step 3:** Add three accordion sections:
```html
<section id="resultado">
  <details open><summary><h2>Resultado na eleição 2026</h2></summary>
    <div id="resContent"></div>
  </details>
</section>

<section id="patrimonio">
  <details open><summary><h2>Patrimônio declarado</h2></summary>
    <div id="patContent"></div>
  </details>
</section>

<section id="candidaturas">
  <details open><summary><h2>Candidaturas anteriores</h2></summary>
    <div id="candContent"></div>
  </details>
</section>
```

**Step 4:** Add footer (same as index.html/2turno.html).

**Step 5:** Add the `<script>` section with:
- `loadPolitico()` function: extracts `?id=` from URL, fetches `data/politicos.json`, finds the entry, calls render functions
- `renderHeader(p)`: sets photo, name, party, cargo, state, TSE link
- `renderResultado(p)`: duel card with votes/%, bar, situation badge
- `renderPatrimonio(p)`: table of years + total + horizontal bars + variation %, details with individual assets
- `renderCandidaturas(p)`: timeline (`.tl` class from 2turno) with year, cargo, party, result
- `fmtN()` and `fmtR()` (currency) formatting functions
- Error state: "Político não encontrado" if ID missing or invalid

**Step 6:** Commit: `feat: cria politico.html com layout e JS`

---

### Task 2: Add CSS for politico.html in shared.css

**Files:**
- Modify: `css/shared.css`

**Step 1:** Add politician profile styles:
```css
.pol-header{display:flex;gap:20px;align-items:center}
.pol-photo{width:80px;height:80px;border-radius:50%;object-fit:cover;background:var(--neutral-soft);flex:none}
.pol-tse{display:inline-block;margin-top:8px;font-size:13px;color:var(--accent);text-decoration:none}
.pol-tse:hover{text-decoration:underline}
.pat-bar{display:flex;align-items:center;gap:10px;margin-block:4px}
.pat-bar b{display:block;height:18px;background:var(--accent);border-radius:4px}
.pat-var{font-size:12px;font-weight:600}
.pat-var.up{color:var(--lula)} .pat-var.dn{color:var(--flavio)}
```

**Step 2:** Commit: `feat: CSS do perfil do político`

---

### Task 3: Generate `data/politicos.json` — batch candidate data

**Files:**
- Create: `data/politicos.json`

**Strategy:** Use MCP API in batches:
1. `list_candidates(office=president, limit=50)` — all presidential candidates
2. `list_candidates(office=governor, outcome=elected, limit=50)` — elected governors R1
3. `list_candidates(office=governor, outcome=runoff, limit=50)` — runoff governors
4. `list_candidates(office=senator, outcome=elected, limit=50, page=1..2)` — elected senators
5. `list_candidates(office=federalDeputy, outcome=elected, limit=50, page=1..11)` — elected deputies

For each candidate returned:
- Check if their `tseCandidateId` matches one of our 478 known IDs
- If yes, include in JSON with basic data + result
- Store UUID for filings lookup

Then for the ~70 top-tier politicians (presidents + governors + senators):
- Call `get_candidate_filings(uuid)` for candidacy history
- Call `list_candidate_assets(uuid, limit=50)` for individual assets

For deputies (~400), skip filings/assets initially (can expand later).

**Step 1:** Batch fetch all candidate groups via `list_candidates`
**Step 2:** Match against known tseCandidateIds
**Step 3:** Fetch filings for top-tier (~70 calls)
**Step 4:** Assemble and write `data/politicos.json`
**Step 5:** Commit: `feat: gera data/politicos.json com dados de 478 políticos`

---

### Task 4: Modify `tseLink()` in index.html and 2turno.html

**Files:**
- Modify: `index.html`
- Modify: `2turno.html`

**Step 1:** In index.html, change the `tseLink()` function:

Before:
```js
url='https://divulgacandcontas.tse.jus.br/divulga/#/candidato/...'
// and for DEP_LINKS:
url=DEP_LINKS[nome];
```

After:
```js
// Extract candId from either DEP_LINKS URL or PLINKS URL
// Point to politico.html?id=candId
url='politico.html?id='+candId;
```

Remove `target="_blank"` from the generated `<a>` tag.
Keep Google search fallback unchanged for unknown politicians.

**Step 2:** In 2turno.html, apply the same change to its `tseLink()` function.

**Step 3:** Commit: `feat: tseLink aponta para politico.html`

---

### Task 5: Test and polish

**Step 1:** Open `politico.html?id=280002551544` (Flávio) — verify all sections render
**Step 2:** Open `politico.html?id=280002542548` (Lula) — verify elected president shows both rounds
**Step 3:** Open a governor, senator, and deputy page — verify each works
**Step 4:** Test invalid ID — verify error state
**Step 5:** Test dark mode toggle
**Step 6:** Click a politician name in index.html — verify it navigates to politico.html
**Step 7:** Commit any fixes: `fix: ajustes no politico.html`
