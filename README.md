# TWICE — Digital Twin Bettembourg

Prototype de Digital Twin : **pluie → routes → accessibilité → pertes économiques**

Zone : Terminal Eurohub Sud + Zone industrielle Wolser, Bettembourg (Luxembourg)

## Lancer une simulation

1. Onglet **Actions** → **TWICE — Digital Twin Bettembourg**
2. **Run workflow** → ajuster les CA si besoin → **Run workflow**

## Rapport

Disponible après chaque run sur GitHub Pages :
`https://allanderrien.github.io/twice-bettembourg/rapport.html`

## Structure

```
src/
  twice_run.py       — simulation (Open-Meteo → JSON)
  twice_report.py    — rapport HTML (JSON → HTML)
outputs/
  resultats_latest.json
  rapport.html
docs/
  rapport.html       — servi par GitHub Pages
.github/workflows/
  twice_run.yml      — workflow Actions
```

## Hypothèses

| # | Description |
|---|-------------|
| H1 | Indice d'aléa = cumul 3h glissantes / 60mm |
| H2 | Route impactée si indice ≥ seuil_impact |
| H3 | Activité pleine si accessibilité ≥ 70%, arrêt si ≤ 40% |
| H4 | CA journalier réparti uniformément sur 24h |
| H5 | CA journalier = paramètre fictif |
| H6 | Fenêtre = 2j historiques + 7j prévisions |
