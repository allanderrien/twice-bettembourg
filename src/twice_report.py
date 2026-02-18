"""
TWICE — Générateur de rapport HTML
Lit outputs/resultats_latest.json et produit outputs/rapport.html
Aucune dépendance externe — HTML/CSS/JS pur
"""

import json
import sys
from pathlib import Path


def load_results(path: str = "outputs/resultats_latest.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def statut_badge(statut: str) -> str:
    colors = {
        "normal":  ("#d1fae5", "#065f46", "●"),
        "impacté": ("#fef3c7", "#92400e", "●"),
        "coupé":   ("#fee2e2", "#991b1b", "●"),
    }
    bg, fg, dot = colors.get(statut, ("#f3f4f6", "#374151", "●"))
    return f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600;">{dot} {statut}</span>'


def format_eur(val: float) -> str:
    return f"{val:,.0f} €".replace(",", " ")


def generate_html(data: dict) -> str:
    generated_at = data.get("generated_at", "")[:16].replace("T", " ")
    zone = data.get("zone", "")
    hypotheses = data.get("hypotheses", {})
    meteo = data.get("meteo", {})
    indices = data.get("indices_alea", [])
    resultats = data.get("resultats", [])
    times = meteo.get("times", [])
    precip = meteo.get("precipitation", [])

    # Labels simplifiés pour les graphiques (HH:MM)
    labels_js = json.dumps([t[11:16] if len(t) >= 16 else t for t in times])
    precip_js = json.dumps([float(p or 0) for p in precip])
    indices_js = json.dumps(indices)

    # Données par site
    sites_js = json.dumps(resultats)

    # Tableau chronologique du premier site (le plus détaillé)
    chrono_rows = ""
    if resultats:
        site0 = resultats[0]
        for h in site0.get("chronologie", []):
            t = h["time"][11:16] if len(h["time"]) >= 16 else h["time"]
            p = f"{float(h['precipitation_mm'] or 0):.1f}"
            ia = f"{h['indice_alea']:.2f}"
            acc = f"{h['accessibilite']:.0%}"
            taux = f"{h['taux_activite']:.0%}"
            perte = format_eur(h["perte_eur"])
            routes = " ".join(
                statut_badge(v) for v in h.get("statuts_routes", {}).values()
            )
            row_bg = ""
            if h["taux_activite"] == 0:
                row_bg = 'style="background:#fff5f5;"'
            elif h["taux_activite"] < 1:
                row_bg = 'style="background:#fffbeb;"'
            chrono_rows += f"""
            <tr {row_bg}>
              <td>{t}</td>
              <td>{p} mm</td>
              <td>{ia}</td>
              <td>{routes}</td>
              <td>{acc}</td>
              <td>{taux}</td>
              <td style="font-weight:600;text-align:right;">{perte}</td>
            </tr>"""

    # Cartes de synthèse par site
    site_cards = ""
    for s in resultats:
        perte = format_eur(s["perte_totale_eur"])
        acc_min = f"{s['accessibilite_min']:.0%}"
        site_cards += f"""
        <div class="site-card">
          <div class="site-name">{s['site_nom']}</div>
          <div class="site-type">{s.get('type', '')}</div>
          <div class="kpi-grid">
            <div class="kpi">
              <div class="kpi-val loss">{perte}</div>
              <div class="kpi-label">Perte totale estimée</div>
            </div>
            <div class="kpi">
              <div class="kpi-val">{s['heures_arret']}h</div>
              <div class="kpi-label">Heures à l'arrêt</div>
            </div>
            <div class="kpi">
              <div class="kpi-val">{s['heures_degradees']}h</div>
              <div class="kpi-label">Heures dégradées</div>
            </div>
            <div class="kpi">
              <div class="kpi-val">{acc_min}</div>
              <div class="kpi-label">Accessibilité minimale</div>
            </div>
          </div>
        </div>"""

    # Hypothèses
    hyp_rows = ""
    for k, v in hypotheses.items():
        hyp_rows += f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>"

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TWICE — Rapport Digital Twin Bettembourg</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:     #1a1a2e;
    --mid:     #4a4a6a;
    --muted:   #9090a8;
    --border:  #e2e2ee;
    --bg:      #f7f7fb;
    --white:   #ffffff;
    --accent:  #2563eb;
    --warn:    #d97706;
    --danger:  #dc2626;
    --success: #059669;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--ink);
    font-size: 14px;
    line-height: 1.6;
  }}

  /* ── HEADER ── */
  header {{
    background: var(--ink);
    color: white;
    padding: 36px 48px 28px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }}
  .header-left h1 {{
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    font-weight: 400;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
  }}
  .header-left .subtitle {{
    color: #a0a0c0;
    font-size: 13px;
    font-weight: 300;
  }}
  .header-right {{
    text-align: right;
    font-size: 12px;
    color: #a0a0c0;
  }}
  .header-right .badge {{
    display: inline-block;
    background: var(--accent);
    color: white;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 6px;
    letter-spacing: 0.5px;
  }}

  /* ── CHAIN BANNER ── */
  .chain {{
    background: var(--white);
    border-bottom: 1px solid var(--border);
    padding: 14px 48px;
    display: flex;
    align-items: center;
    gap: 0;
    font-size: 12px;
    color: var(--mid);
    font-weight: 500;
    letter-spacing: 0.3px;
    overflow-x: auto;
  }}
  .chain-step {{
    white-space: nowrap;
    padding: 4px 12px;
    border-radius: 4px;
    background: var(--bg);
    border: 1px solid var(--border);
  }}
  .chain-arrow {{
    margin: 0 8px;
    color: var(--accent);
    font-size: 16px;
  }}

  /* ── MAIN LAYOUT ── */
  main {{ padding: 32px 48px; max-width: 1400px; margin: 0 auto; }}

  section {{ margin-bottom: 40px; }}
  section h2 {{
    font-family: 'DM Serif Display', serif;
    font-size: 18px;
    font-weight: 400;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--ink);
    display: flex;
    align-items: center;
    gap: 8px;
  }}
  section h2 .num {{
    font-family: 'DM Sans', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: var(--accent);
    background: #eff6ff;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 1px;
  }}

  /* ── SITE CARDS ── */
  .cards-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
    gap: 20px;
  }}
  .site-card {{
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 24px;
    border-top: 3px solid var(--accent);
  }}
  .site-name {{
    font-family: 'DM Serif Display', serif;
    font-size: 17px;
    font-weight: 400;
    margin-bottom: 2px;
  }}
  .site-type {{
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 20px;
  }}
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }}
  .kpi {{ }}
  .kpi-val {{
    font-size: 22px;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.2;
  }}
  .kpi-val.loss {{ color: var(--danger); }}
  .kpi-label {{
    font-size: 11px;
    color: var(--muted);
    margin-top: 2px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  /* ── CHARTS ── */
  .chart-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(460px, 1fr));
    gap: 20px;
  }}
  .chart-box {{
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 24px;
  }}
  .chart-box h3 {{
    font-size: 13px;
    font-weight: 600;
    color: var(--mid);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 16px;
  }}
  .chart-box canvas {{ width: 100% !important; }}

  /* ── TABLE ── */
  .table-wrap {{
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12.5px;
  }}
  thead tr {{
    background: var(--ink);
    color: white;
  }}
  thead th {{
    padding: 10px 14px;
    text-align: left;
    font-weight: 500;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }}
  tbody tr {{ border-bottom: 1px solid var(--border); }}
  tbody tr:hover {{ background: #f0f0fa !important; }}
  tbody td {{ padding: 8px 14px; vertical-align: middle; }}

  /* ── HYPOTHESES ── */
  .hyp-table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  .hyp-table td {{ padding: 8px 12px; border-bottom: 1px solid var(--border); }}
  .hyp-table td:first-child {{
    width: 40px;
    color: var(--accent);
    font-size: 12px;
  }}
  .hyp-table tr:last-child td {{ border-bottom: none; }}

  /* ── FOOTER ── */
  footer {{
    text-align: center;
    padding: 24px;
    font-size: 11px;
    color: var(--muted);
    border-top: 1px solid var(--border);
    margin-top: 40px;
  }}
</style>
</head>
<body>

<header>
  <div class="header-left">
    <h1>TWICE — Digital Twin Bettembourg</h1>
    <div class="subtitle">Rapport de simulation · Interruption d'activité sans dommage direct</div>
  </div>
  <div class="header-right">
    <div class="badge">PROTOTYPE</div><br>
    {zone}<br>
    Généré le {generated_at} UTC
  </div>
</header>

<div class="chain">
  <span class="chain-step">🌧 Précipitations (Open-Meteo)</span>
  <span class="chain-arrow">→</span>
  <span class="chain-step">📊 Indice d'aléa</span>
  <span class="chain-arrow">→</span>
  <span class="chain-step">🛣 Statut des routes</span>
  <span class="chain-arrow">→</span>
  <span class="chain-step">🏭 Accessibilité des sites</span>
  <span class="chain-arrow">→</span>
  <span class="chain-step">💶 Pertes économiques</span>
</div>

<main>

  <!-- SECTION 1 — SYNTHÈSE -->
  <section>
    <h2><span class="num">01</span> Synthèse par site logistique</h2>
    <div class="cards-grid">
      {site_cards}
    </div>
  </section>

  <!-- SECTION 2 — GRAPHIQUES -->
  <section>
    <h2><span class="num">02</span> Visualisation temporelle (48h)</h2>
    <div class="chart-grid">

      <div class="chart-box">
        <h3>Précipitations horaires &amp; indice d'aléa</h3>
        <canvas id="chartAlea" height="200"></canvas>
      </div>

      <div class="chart-box">
        <h3>Statut des routes dans le temps</h3>
        <canvas id="chartRoutes" height="200"></canvas>
      </div>

      <div class="chart-box">
        <h3>Taux d'activité — Terminal Eurohub Sud</h3>
        <canvas id="chartTaux0" height="200"></canvas>
      </div>

      <div class="chart-box">
        <h3>Pertes cumulées — Terminal Eurohub Sud</h3>
        <canvas id="chartPertes0" height="200"></canvas>
      </div>

    </div>
  </section>

  <!-- SECTION 3 — CHRONOLOGIE DÉTAILLÉE -->
  <section>
    <h2><span class="num">03</span> Chronologie détaillée — Terminal Eurohub Sud</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Heure</th>
            <th>Précip.</th>
            <th>Indice aléa</th>
            <th>Statut routes</th>
            <th>Accessibilité</th>
            <th>Taux activité</th>
            <th style="text-align:right;">Perte (€)</th>
          </tr>
        </thead>
        <tbody>
          {chrono_rows}
        </tbody>
      </table>
    </div>
  </section>

  <!-- SECTION 4 — HYPOTHÈSES -->
  <section>
    <h2><span class="num">04</span> Hypothèses du modèle</h2>
    <div class="table-wrap" style="padding:4px 0;">
      <table class="hyp-table">
        {hyp_rows}
      </table>
    </div>
  </section>

</main>

<footer>
  TWICE — Prototype Digital Twin · Projet de démonstration · Données météo : Open-Meteo API · Réseau routier : OpenStreetMap
</footer>

<script>
const LABELS   = {labels_js};
const PRECIP   = {precip_js};
const INDICES  = {indices_js};
const SITES    = {sites_js};

const COLORS = {{
  precip:  'rgba(59,130,246,0.7)',
  alea:    'rgba(220,38,38,1)',
  normal:  'rgba(5,150,105,0.85)',
  impacte: 'rgba(217,119,6,0.85)',
  coupe:   'rgba(220,38,38,0.85)',
  taux:    'rgba(37,99,235,0.8)',
  pertes:  'rgba(220,38,38,0.7)',
}};

const CHART_DEFAULTS = {{
  plugins: {{ legend: {{ labels: {{ font: {{ family: 'DM Sans', size: 11 }}, boxWidth: 12 }} }} }},
  scales: {{
    x: {{
      ticks: {{ font: {{ family: 'DM Sans', size: 10 }}, maxTicksLimit: 12 }},
      grid:  {{ color: '#e2e2ee' }}
    }},
    y: {{
      ticks: {{ font: {{ family: 'DM Sans', size: 10 }} }},
      grid:  {{ color: '#e2e2ee' }}
    }}
  }},
  animation: {{ duration: 600 }},
  responsive: true,
  maintainAspectRatio: true,
}};

// ── GRAPHIQUE 1 : Précipitations + indice d'aléa ──
new Chart(document.getElementById('chartAlea'), {{
  data: {{
    labels: LABELS,
    datasets: [
      {{
        type: 'bar',
        label: 'Précipitations (mm/h)',
        data: PRECIP,
        backgroundColor: COLORS.precip,
        yAxisID: 'yPrecip',
        order: 2,
      }},
      {{
        type: 'line',
        label: 'Indice d\\'aléa [0–1]',
        data: INDICES,
        borderColor: COLORS.alea,
        backgroundColor: 'rgba(220,38,38,0.08)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
        yAxisID: 'yAlea',
        order: 1,
      }}
    ]
  }},
  options: {{
    ...CHART_DEFAULTS,
    scales: {{
      x:      {{ ...CHART_DEFAULTS.scales.x }},
      yPrecip: {{
        type: 'linear', position: 'left',
        title: {{ display: true, text: 'mm/h', font: {{ size: 10 }} }},
        grid: {{ color: '#e2e2ee' }},
        ticks: {{ font: {{ size: 10 }} }}
      }},
      yAlea: {{
        type: 'linear', position: 'right',
        min: 0, max: 1,
        title: {{ display: true, text: 'Indice', font: {{ size: 10 }} }},
        grid: {{ drawOnChartArea: false }},
        ticks: {{ font: {{ size: 10 }} }}
      }}
    }}
  }}
}});

// ── GRAPHIQUE 2 : Statut des routes ──
// Encode : normal=1, impacté=0.5, coupé=0
const ROUTE_IDS = SITES[0]?.chronologie[0]
  ? Object.keys(SITES[0].chronologie[0].statuts_routes)
  : [];

const ROUTE_COLORS = [
  'rgba(37,99,235,0.8)',
  'rgba(5,150,105,0.8)',
  'rgba(217,119,6,0.8)',
  'rgba(168,85,247,0.8)',
];

const STATUT_VAL = {{ 'normal': 1.0, 'impacté': 0.5, 'coupé': 0.0 }};

const routeDatasets = ROUTE_IDS.map((rid, i) => {{
  const vals = SITES[0].chronologie.map(h => STATUT_VAL[h.statuts_routes[rid]] ?? 1);
  return {{
    label: rid.replace(/_/g, ' '),
    data: vals,
    borderColor: ROUTE_COLORS[i % ROUTE_COLORS.length],
    backgroundColor: 'transparent',
    borderWidth: 2,
    pointRadius: 0,
    stepped: true,
    tension: 0,
  }};
}});

new Chart(document.getElementById('chartRoutes'), {{
  type: 'line',
  data: {{ labels: LABELS, datasets: routeDatasets }},
  options: {{
    ...CHART_DEFAULTS,
    scales: {{
      x: {{ ...CHART_DEFAULTS.scales.x }},
      y: {{
        min: -0.1, max: 1.1,
        ticks: {{
          font: {{ size: 10 }},
          callback: v => v === 1 ? 'Normal' : v === 0.5 ? 'Impacté' : v === 0 ? 'Coupé' : ''
        }},
        grid: {{ color: '#e2e2ee' }}
      }}
    }}
  }}
}});

// ── GRAPHIQUE 3 : Taux d'activité site 0 ──
if (SITES[0]) {{
  const taux   = SITES[0].chronologie.map(h => h.taux_activite * 100);
  new Chart(document.getElementById('chartTaux0'), {{
    type: 'line',
    data: {{
      labels: LABELS,
      datasets: [{{
        label: 'Taux d\\'activité (%)',
        data: taux,
        borderColor: COLORS.taux,
        backgroundColor: 'rgba(37,99,235,0.1)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.2,
        stepped: true,
      }}]
    }},
    options: {{
      ...CHART_DEFAULTS,
      scales: {{
        x: {{ ...CHART_DEFAULTS.scales.x }},
        y: {{ min: 0, max: 105, ticks: {{ callback: v => v + '%', font: {{ size: 10 }} }}, grid: {{ color: '#e2e2ee' }} }}
      }}
    }}
  }});
}}

// ── GRAPHIQUE 4 : Pertes cumulées site 0 ──
if (SITES[0]) {{
  let cumul = 0;
  const pertCumul = SITES[0].chronologie.map(h => {{ cumul += h.perte_eur; return Math.round(cumul); }});
  new Chart(document.getElementById('chartPertes0'), {{
    type: 'line',
    data: {{
      labels: LABELS,
      datasets: [{{
        label: 'Pertes cumulées (€)',
        data: pertCumul,
        borderColor: COLORS.alea,
        backgroundColor: 'rgba(220,38,38,0.08)',
        borderWidth: 2,
        pointRadius: 0,
        fill: true,
        tension: 0.3,
      }}]
    }},
    options: {{
      ...CHART_DEFAULTS,
      scales: {{
        x: {{ ...CHART_DEFAULTS.scales.x }},
        y: {{
          ticks: {{
            font: {{ size: 10 }},
            callback: v => v.toLocaleString('fr-FR') + ' €'
          }},
          grid: {{ color: '#e2e2ee' }}
        }}
      }}
    }}
  }});
}}
</script>

</body>
</html>"""

    return html


def main():
    json_path = "outputs/resultats_latest.json"
    html_path = "outputs/rapport.html"

    print("→ Chargement des résultats...")
    data = load_results(json_path)

    print("→ Génération du rapport HTML...")
    html = generate_html(data)

    Path(html_path).write_text(html, encoding="utf-8")
    print(f"→ Rapport généré : {html_path}")


if __name__ == "__main__":
    main()
