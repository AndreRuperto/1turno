<p align="center">
  <img src="assets/logo/turnos-horizontal-preto.svg" alt="turnos" width="200">
</p>

<p align="center">
  <strong>Relatórios interativos dos resultados das Eleições Gerais brasileiras de 2026.</strong><br>
  Presidente, governadores, senadores, deputados e perfis individuais — nos 26 estados e no DF.
</p>

<p align="center">
  <a href="https://1turno.up.railway.app">
    <img src="https://img.shields.io/badge/live-1turno.up.railway.app-1d4690?style=flat-square" alt="Live">
  </a>
  <img src="https://img.shields.io/badge/stack-HTML%20%2B%20CSS%20%2B%20JS%20vanilla-f0a500?style=flat-square" alt="Stack">
  <img src="https://img.shields.io/badge/candidatos-596-a9261f?style=flat-square" alt="Candidatos">
  <img src="https://img.shields.io/badge/licença-livre-2e8b57?style=flat-square" alt="Licença">
</p>

---

## Sobre

Três documentos estáticos de jornalismo de dados cobrindo os dois turnos das eleições de outubro de 2026. Sem framework, sem opinião, sem paywall. Só os números que importam.

Os dados vêm de reportagens baseadas na apuração do TSE. As fontes estão listadas no rodapé de cada página. Onde divergem, a seção **Ressalvas** documenta.

---

## Páginas

### [`index.html`](https://1turno.up.railway.app) — 1º turno (04/10/2026)

| Seção | O que mostra |
|-------|-------------|
| **Presidência** | Resultado nacional, mapa por UF (cartograma SVG), tabela com votos |
| **Governadores** | 21 eleitos no 1º turno + 6 disputas do 2º turno, com votos por candidato |
| **Senado** | 54 eleitos, composição completa de 2027 (81 cadeiras) |
| **Câmara** | 513 deputados por partido, hemiciclo interativo SVG |
| **Congresso 2027** | Hemiciclos com 3 modos: partido, espectro detalhado, esquerda/centro/direita |
| **Estados** | Deputados federais e estaduais de SP, RJ, DF e MG com votação individual |

### [`2turno.html`](https://1turno.up.railway.app/2turno.html) — 2º turno (25/10/2026)

| Seção | O que mostra |
|-------|-------------|
| **Resultado** | Lula 51,79% × Flávio 48,21% — a primeira virada de turno da história |
| **Comparação** | Evolução 1T → 2T por estado, por município, por região |
| **Transferência** | Para onde foram os 9M de votos dos candidatos eliminados |
| **Mobilização** | Abstenção, brancos, nulos — o menor nível desde 2006 |
| **Perfil do voto** | Pesquisa por gênero, idade, escolaridade, renda |
| **Governadores** | 6 eleitos no 2º turno, mapa final com todos os 27 |
| **Timeline** | 21 dias entre os turnos + hora a hora do dia 25/10 |
| **Jurídico** | A contestação, a prorrogação e a questão da isonomia |

### [`politico.html`](https://1turno.up.railway.app/politico.html?id=280002551544) — Perfil do candidato

Página dinâmica que carrega dados de 596 candidatos. Acesso pelo ícone ↗ ao lado de cada nome no site.

| Seção | O que mostra |
|-------|-------------|
| **Header** | Foto (TSE), nome, partido, cargo, número, escolaridade, ocupação |
| **Resultado** | Votos e % no 1º e 2º turno, situação (eleito/eliminado/2T) |
| **Patrimônio** | Evolução dos bens declarados ao TSE com barras e variação % |
| **Candidaturas** | Timeline de todas as candidaturas anteriores com partido/cargo/resultado |

---

## Funcionalidades

- **Tabelas ordenáveis** — clique em qualquer coluna para ordenar
- **Cartogramas SVG** — mapas gerados em JavaScript puro
- **Hemiciclos interativos** — composição do Congresso com 3 visualizações
- **Dark/light mode** — botão no navbar + respeita preferência do sistema
- **596 perfis de candidatos** — presidenciáveis, governadores, senadores e deputados
- **Links ao TSE** — cada candidato linka ao perfil oficial de candidatura
- **Responsivo** — funciona em desktop e mobile
- **Zero dependências** — sem framework, sem build step, sem bundler

---

## Como rodar

```bash
git clone https://github.com/AndreRuperto/1turno.git
cd 1turno
npx http-server . -o -c-1
```

Ou abra `index.html` direto no browser (todas as features funcionam via `file://`).

---

## Estrutura

```
turnos/
├── index.html              # 1º turno
├── 2turno.html             # 2º turno
├── politico.html           # Perfil dinâmico do candidato
├── css/
│   └── shared.css          # Design tokens, layout, componentes
├── data/
│   ├── politicos.json      # 596 candidatos (dados da API Eleições.dev)
│   └── politicos.js        # Mesmo JSON como variável JS (compatível com file://)
├── assets/
│   ├── favicon/            # SVG, PNG 16/32/48/64/180/512, ICO
│   ├── logo/               # Horizontal claro/escuro/preto (SVG + PNG)
│   └── simbolo/            # Ícone isolado claro/escuro/preto (SVG + PNG)
├── scripts/
│   └── generate_json.py    # Script para regenerar o JSON via API
├── docs/plans/             # Design docs e planos de implementação
└── package.json            # npm start → http-server
```

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Markup | HTML semântico, `<details>` para accordions |
| Estilo | CSS custom properties, dark mode via `prefers-color-scheme` + `data-theme` |
| Gráficos | SVG gerado por JS (cartogramas, hemiciclos, barras) |
| Fontes | Source Serif 4 + IBM Plex Sans (Google Fonts) |
| Dados | JSON estático pré-gerado via [Eleições.dev](https://eleicoes.dev) |
| Deploy | Railway (serve estático) |

---

## Decisões editoriais

- Percentuais são de **votos válidos** (excluindo brancos e nulos), salvo indicação.
- Dados do 1T compilados em 05/10/2026; do 2T em 26/10/2026. Variações em relação ao resultado final são documentadas nas Ressalvas.
- A federação PT/PCdoB/PV é contada como 88 cadeiras na Câmara, seguindo o infográfico da Câmara dos Deputados.
- Dados de perfil do voto (gênero, idade, renda) vêm de pesquisa DataTrends/Poder360 — não do resultado das urnas.

---

## Fontes primárias

Agência Senado · Agência Brasil · Agência Câmara · Gazeta do Povo · CNN Brasil · Poder360 · Metrópoles · Jovem Pan · Forbes · O Tempo · InfoMoney · TRE-SP · Revista Oeste · O Povo · [Eleições.dev](https://eleicoes.dev) (API).

Lista completa no rodapé de cada página.

---

## Calendário

| Data | Evento |
|------|--------|
| 04/10/2026 | 1º turno |
| 25/10/2026 | 2º turno |
| 18/12/2026 | Diplomação dos eleitos |
| 05/01/2027 | Posse do presidente e vice |
| 06/01/2027 | Posse dos governadores |
| 01/02/2027 | Posse de senadores e deputados |

---

## Licença

Dados eleitorais são públicos. Código livre para uso e adaptação.

Feito por [André Ruperto](https://github.com/AndreRuperto).
