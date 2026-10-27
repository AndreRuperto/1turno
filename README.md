# turnos

**Relatórios interativos dos resultados das Eleições Gerais brasileiras de 2026.**

🔗 [1turno.up.railway.app](https://1turno.up.railway.app)

---

## O que é

Dois documentos estáticos de jornalismo de dados cobrindo os dois turnos das eleições de outubro de 2026 — presidente, governadores, senadores e deputados federais nos 26 estados e no Distrito Federal.

Sem framework, sem opinião, sem paywall. Só os números que importam.

---

## O que tem

### 1º turno (`index.html`)
- **Presidência** — resultado nacional, mapa por UF (cartograma), tabela de candidatos
- **Governadores** — 20 eleitos no 1º turno + 7 disputas para o 2º turno
- **Senado** — 54 eleitos, composição completa de 2027 (81 cadeiras)
- **Câmara** — 513 deputados por partido, hemiciclo interativo
- **Congresso 2027** — hemiciclos com 3 modos: por partido, espectro detalhado, esquerda/centro/direita
- **Estados** — listas de deputados federais e estaduais de SP, RJ, DF e MG com votações individuais

### 2º turno (`2turno.html`)
- **Presidente** — resultado nacional, mapa por UF, comparação entre turnos
- **Governadores** — 6 disputas decididas no 2º turno
- **Timeline** — cronologia da campanha e resultado

### Comum
- **Tabelas ordenáveis** — clique em qualquer coluna para ordenar por nome, UF ou %
- **Links diretos** — cada candidato tem link para o perfil no TSE via meuspoliticos.com.br
- **Dark mode** — segue a preferência do sistema
- **Responsivo** — funciona em mobile

---

## Fontes

Os dados vêm de reportagens baseadas na apuração do TSE. As principais fontes estão listadas no rodapé do relatório. Onde as fontes divergem, o relatório indica explicitamente — ver seção **Ressalvas**.

Fontes primárias incluem: Agência Senado, Agência Brasil, Agência Câmara, Gazeta do Povo, CNN Brasil, Poder360 e outros veículos citados no relatório.

---

## Stack

```
HTML + CSS + JavaScript vanilla
Sem dependências externas (exceto fontes do Google Fonts)
Deploy: Railway
```

Duas páginas HTML com CSS compartilhado. Sem build step, sem bundler, sem framework.

Os gráficos (cartogramas, hemiciclos, barras) são gerados em SVG e HTML via JavaScript puro.

---

## Estrutura

```
turnos/
├── index.html            # 1º turno
├── 2turno.html           # 2º turno
├── css/
│   └── shared.css        # Design tokens, layout, componentes comuns
├── assets/
│   ├── favicon/          # SVG, PNG 16/32/48/64/180/512, ICO
│   ├── logo/             # Horizontal claro/escuro/preto (SVG + PNG)
│   ├── simbolo/          # Ícone isolado claro/escuro/preto (SVG + PNG)
│   └── 1turno/           # Brand kit "1turno" (favicon, logo, símbolo)
├── docs/
└── README.md
```

---

## Decisões editoriais

- Percentuais usam a apuração disponível no momento da compilação (5/10/2026). Pequenas variações em relação ao resultado final são esperadas e documentadas nas Ressalvas.
- Partido de candidatos com divergência entre fontes usa a versão da maioria das fontes consultadas.
- A federação PT/PCdoB/PV é contada como 88 cadeiras na Câmara, seguindo o infográfico oficial da Câmara dos Deputados.
- Marco histórico do PL (121 deputados): referência é "desde 1990" — as eleições proporcionais pós-Constituição começam em 1990, não em 1988.

---

## Calendário eleitoral

| Data | Evento |
|------|--------|
| 04/10/2026 | 1º turno |
| 25/10/2026 | 2º turno |
| até 18/12/2026 | Diplomação dos eleitos |
| 05/01/2027 | Posse do presidente |
| 06/01/2027 | Posse dos governadores |
| 01/02/2027 | Posse de senadores e deputados |

---

## Licença

Dados eleitorais são públicos. O código é livre para uso e adaptação.
