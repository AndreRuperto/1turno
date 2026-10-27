# Página de Perfil do Político — Design

> **Para Claude:** Use superpowers:writing-plans para criar o plano de implementação a partir deste design.

**Objetivo:** Criar uma página dinâmica `politico.html` que exibe o perfil completo de cada político do site — resultado eleitoral, patrimônio declarado e candidaturas anteriores.

**Arquitetura:** Single-page dinâmica. Uma única `politico.html` recebe o ID do candidato via query string (`?id=tseCandidateId`) e carrega os dados de um arquivo `data/politicos.json` pré-gerado. Sem servidor, sem build step em runtime.

---

## Decisões de design

| Decisão | Escolha |
|---------|---------|
| Tipo de perfil | Completo (resultado + patrimônio + candidaturas) |
| Fonte de dados | API Eleições.dev (MCP) → JSON estático pré-gerado |
| Geração | Script consulta MCP, gera `data/politicos.json` |
| Escopo | Só políticos que aparecem no site (~600 do PLINKS) |
| Navegação | Ícone ↗ (tseLink) passa a abrir `politico.html?id=xxx` |
| Layout | Accordion (`<details>`) igual ao resto do site |
| Patrimônio | Tabela + barras horizontais + lista de bens colapsável |

---

## Estrutura do JSON

Arquivo `data/politicos.json`, objeto indexado por `tseCandidateId`:

```json
{
  "280002551544": {
    "nome": "Flávio Bolsonaro",
    "nomeCompleto": "Flávio Nantes Bolsonaro",
    "partido": "PL",
    "numero": 22,
    "cargo": "presidente",
    "estado": "BR",
    "foto": "https://divulgacandcontas.tse.jus.br/...",
    "resultado": {
      "turno1": { "votos": 56104503, "pct": 47.03, "situacao": "2º turno" },
      "turno2": { "votos": 59826041, "pct": 48.21, "situacao": "Não eleito" }
    },
    "patrimonio": [
      { "ano": 2018, "total": 1523000, "bens": [{"desc": "Apartamento...", "valor": 800000}] },
      { "ano": 2022, "total": 2105000, "bens": [] },
      { "ano": 2026, "total": 3200000, "bens": [] }
    ],
    "candidaturas": [
      { "ano": 2018, "cargo": "Senador", "estado": "RJ", "partido": "PSL", "resultado": "Eleito", "votos": 4380000 },
      { "ano": 2026, "cargo": "Presidente", "estado": "BR", "partido": "PL", "resultado": "Não eleito", "votos": 59826041 }
    ]
  }
}
```

Tamanho estimado: 500KB–1MB para ~600 políticos.

---

## Layout da página

```
┌─ Navbar (igual às outras páginas) ──────────────┐
│ Turnos  Resultado │ Patrimônio │ Candidaturas │ ☀ │
└─────────────────────────────────────────────────┘

┌─ Header ────────────────────────────────────────┐
│ [foto 80px]  FLÁVIO BOLSONARO                   │
│              PL · Candidato a Presidente · 2026  │
│              Número: 22 · Estado: BR             │
│              🔗 Ver no TSE                       │
└─────────────────────────────────────────────────┘

┌─ § Resultado na eleição 2026 ───────────────────┐
│ Cargo, turno, situação (eleito/2T/eliminado)     │
│ Votos e % (por turno se houver)                  │
│ Barra visual de resultado                        │
└─────────────────────────────────────────────────┘

┌─ § Patrimônio declarado ────────────────────────┐
│ Tabela: ano │ valor total │ barra horizontal     │
│ Variação % entre eleições                        │
│ <details> por eleição com lista de bens          │
└─────────────────────────────────────────────────┘

┌─ § Candidaturas anteriores ─────────────────────┐
│ Timeline: ano, cargo, partido, resultado         │
│ Evolução partidária e cargos                     │
└─────────────────────────────────────────────────┘

┌─ Footer (igual às outras páginas) ──────────────┘
```

---

## Migração do tseLink()

### Antes
```js
url = 'https://divulgacandcontas.tse.jus.br/divulga/#/candidato/...'
// Abre TSE em nova aba
```

### Depois
```js
url = 'politico.html?id=' + candId
// Abre página interna, mesma aba
```

O `candId` já é extraído dentro do `tseLink()` a partir do `PLINKS`. Fallback (sem PLINKS): mantém Google search, sem link interno.

Dentro de `politico.html`, o link pro TSE aparece no header: "Ver no TSE ↗" com `target="_blank"`.

---

## Tarefas de implementação

### Tarefa 1: Gerar `data/politicos.json`
- Consultar API MCP (get_candidate, get_candidate_filings, list_candidate_assets) para cada político do PLINKS + DEP_LINKS
- Montar JSON na estrutura definida
- Salvar em `data/politicos.json`

### Tarefa 2: Criar `politico.html`
- Navbar com links âncora (Resultado, Patrimônio, Candidaturas)
- Header com foto, nome, partido, cargo, estado, link TSE
- Seção Resultado: cards com votos/%, barra visual
- Seção Patrimônio: tabela + barras + detalhes colapsáveis
- Seção Candidaturas: timeline com accordion
- Footer igual às outras páginas
- Toggle de tema, IntersectionObserver no nav

### Tarefa 3: Alterar `tseLink()` em index.html e 2turno.html
- Trocar destino do ícone ↗ para `politico.html?id=xxx`
- Remover `target="_blank"` desses links
- Manter fallback Google para políticos sem PLINKS

### Tarefa 4: CSS no shared.css
- Estilos do header do perfil (foto, nome, dados)
- Barras de patrimônio (reutilizar `.hb` existente)
- Timeline de candidaturas (reutilizar `.tl` do 2turno)
