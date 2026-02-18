"""
TWICE — Générateur de rapport HTML
Lit outputs/resultats_latest.json et produit outputs/rapport.html
Aucune dépendance externe — HTML/CSS/JS pur avec Chart.js 4
"""

import json
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
    return (f'<span style="background:{bg};color:{fg};padding:2px 8px;'
            f'border-radius:4px;font-size:11px;font-weight:600;">{dot} {statut}</span>')


def format_eur(val: float) -> str:
    return f"{val:,.0f} €".replace(",", "\u202f")


def fmt_label(iso: str) -> str:
    """YYYY-MM-DDTHH:MM → JJ/MM HH:MM"""
    if len(iso) >= 16:
        d, m = iso[8:10], iso[5:7]
        hhmm = iso[11:16]
        return f"{d}/{m} {hhmm}"
    return iso


def generate_html(data: dict) -> str:
    generated_at = data.get("generated_at", "")[:16].replace("T", " ")
    zone         = data.get("zone", "")
    hypotheses   = data.get("hypotheses", {})
    meteo        = data.get("meteo", {})
    indices      = data.get("indices_alea", [])
    resultats    = data.get("resultats", [])
    now_index    = data.get("now_index", 0)
    times        = meteo.get("times", [])
    precip       = meteo.get("precipitation", [])

    labels_js    = json.dumps([fmt_label(t) for t in times])
    precip_js    = json.dumps([float(p or 0) for p in precip])
    indices_js   = json.dumps(indices)
    now_index_js = now_index
    sites_js     = json.dumps(resultats)

    # ── Tableau chronologique
    chrono_rows = ""
    if resultats:
        for h in resultats[0].get("chronologie", []):
            t      = fmt_label(h["time"])
            p      = f"{float(h['precipitation_mm'] or 0):.1f}"
            ia     = f"{h['indice_alea']:.2f}"
            acc    = f"{h['accessibilite']:.0%}"
            taux   = f"{h['taux_activite']:.0%}"
            perte  = format_eur(h["perte_eur"])
            routes = " ".join(statut_badge(v) for v in h.get("statuts_routes", {}).values())
            is_fc  = h.get("is_forecast", False)

            if h["taux_activite"] == 0:
                row_bg = 'style="background:#fff5f5;"'
            elif h["taux_activite"] < 1:
                row_bg = 'style="background:#fffbeb;"'
            elif is_fc:
                row_bg = 'style="background:#f0f9ff;"'
            else:
                row_bg = ""

            fc_tag = (' <span style="font-size:10px;color:#0369a1;font-weight:600;">'
                      'PRÉVIS.</span>') if is_fc else ""
            chrono_rows += f"""
            <tr {row_bg}>
              <td>{t}{fc_tag}</td><td>{p} mm</td><td>{ia}</td>
              <td>{routes}</td><td>{acc}</td><td>{taux}</td>
              <td style="font-weight:600;text-align:right;">{perte}</td>
            </tr>"""

    # ── Cartes de synthèse
    site_cards = ""
    for s in resultats:
        perte   = format_eur(s["perte_totale_eur"])
        acc_min = f"{s['accessibilite_min']:.0%}"
        site_cards += f"""
        <div class="site-card">
          <div class="site-name">{s['site_nom']}</div>
          <div class="site-type">{s.get('type','')}</div>
          <div class="kpi-grid">
            <div class="kpi"><div class="kpi-val loss">{perte}</div><div class="kpi-label">Perte totale estimée</div></div>
            <div class="kpi"><div class="kpi-val">{s['heures_arret']}h</div><div class="kpi-label">Heures à l'arrêt</div></div>
            <div class="kpi"><div class="kpi-val">{s['heures_degradees']}h</div><div class="kpi-label">Heures dégradées</div></div>
            <div class="kpi"><div class="kpi-val">{acc_min}</div><div class="kpi-label">Accessibilité minimale</div></div>
          </div>
        </div>"""

    # ── Hypothèses
    hyp_rows = "".join(
        f"<tr><td><strong>{k}</strong></td><td>{v}</td></tr>"
        for k, v in hypotheses.items()
    )

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
    --ink:#1a1a2e; --mid:#4a4a6a; --muted:#9090a8;
    --border:#e2e2ee; --bg:#f7f7fb; --white:#ffffff;
    --accent:#2563eb; --danger:#dc2626;
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--ink);font-size:14px;line-height:1.6;}}
  header{{background:var(--ink);color:white;padding:36px 48px 28px;display:flex;justify-content:space-between;align-items:flex-end;}}
  .header-left h1{{font-family:'DM Serif Display',serif;font-size:28px;font-weight:400;letter-spacing:-0.5px;margin-bottom:4px;}}
  .header-left .subtitle{{color:#a0a0c0;font-size:13px;font-weight:300;}}
  .header-right{{text-align:right;font-size:12px;color:#a0a0c0;}}
  .badge{{display:inline-block;background:var(--accent);color:white;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;margin-bottom:6px;}}
  .chain{{background:var(--white);border-bottom:1px solid var(--border);padding:14px 48px;display:flex;align-items:center;font-size:12px;color:var(--mid);font-weight:500;overflow-x:auto;gap:0;}}
  .chain-step{{white-space:nowrap;padding:4px 12px;border-radius:4px;background:var(--bg);border:1px solid var(--border);}}
  .chain-arrow{{margin:0 8px;color:var(--accent);font-size:16px;}}
  .legend-bar{{background:var(--white);border-bottom:1px solid var(--border);padding:10px 48px;display:flex;gap:24px;font-size:12px;color:var(--mid);align-items:center;flex-wrap:wrap;}}
  .leg{{display:flex;align-items:center;gap:6px;}}
  .leg-box{{width:16px;height:10px;border-radius:2px;}}
  main{{padding:32px 48px;max-width:1400px;margin:0 auto;}}
  section{{margin-bottom:40px;}}
  section h2{{font-family:'DM Serif Display',serif;font-size:18px;font-weight:400;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid var(--ink);display:flex;align-items:center;gap:8px;}}
  .num{{font-family:'DM Sans',sans-serif;font-size:11px;font-weight:600;color:var(--accent);background:#eff6ff;padding:2px 8px;border-radius:4px;letter-spacing:1px;}}
  .cards-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px;}}
  .site-card{{background:var(--white);border:1px solid var(--border);border-radius:8px;padding:24px;border-top:3px solid var(--accent);}}
  .site-name{{font-family:'DM Serif Display',serif;font-size:17px;font-weight:400;margin-bottom:2px;}}
  .site-type{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:20px;}}
  .kpi-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;}}
  .kpi-val{{font-size:22px;font-weight:600;line-height:1.2;}}
  .kpi-val.loss{{color:var(--danger);}}
  .kpi-label{{font-size:11px;color:var(--muted);margin-top:2px;text-transform:uppercase;letter-spacing:0.5px;}}
  .chart-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(460px,1fr));gap:20px;}}
  .chart-box{{background:var(--white);border:1px solid var(--border);border-radius:8px;padding:20px 24px;}}
  .chart-box h3{{font-size:13px;font-weight:600;color:var(--mid);text-transform:uppercase;letter-spacing:0.8px;margin-bottom:16px;}}
  .table-wrap{{background:var(--white);border:1px solid var(--border);border-radius:8px;overflow:auto;max-height:480px;}}
  table{{width:100%;border-collapse:collapse;font-size:12.5px;}}
  thead tr{{background:var(--ink);color:white;position:sticky;top:0;z-index:1;}}
  thead th{{padding:10px 14px;text-align:left;font-weight:500;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;white-space:nowrap;}}
  tbody tr{{border-bottom:1px solid var(--border);}}
  tbody tr:hover{{filter:brightness(0.97);}}
  tbody td{{padding:8px 14px;vertical-align:middle;}}
  .hyp-table{{width:100%;border-collapse:collapse;font-size:13px;}}
  .hyp-table td{{padding:8px 12px;border-bottom:1px solid var(--border);}}
  .hyp-table td:first-child{{width:40px;color:var(--accent);font-size:12px;}}
  .hyp-table tr:last-child td{{border-bottom:none;}}
  footer{{text-align:center;padding:24px;font-size:11px;color:var(--muted);border-top:1px solid var(--border);margin-top:40px;}}
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
    {zone}<br>Généré le {generated_at} UTC
  </div>
</header>

<div class="chain">
  <span class="chain-step">🌧 Précipitations</span><span class="chain-arrow">→</span>
  <span class="chain-step">📊 Indice d'aléa</span><span class="chain-arrow">→</span>
  <span class="chain-step">🛣 Statut des routes</span><span class="chain-arrow">→</span>
  <span class="chain-step">🏭 Accessibilité</span><span class="chain-arrow">→</span>
  <span class="chain-step">💶 Pertes économiques</span>
</div>

<div class="legend-bar">
  <span style="font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Légende :</span>
  <span class="leg"><span class="leg-box" style="background:rgba(59,130,246,0.6);"></span>Historique</span>
  <span class="leg"><span class="leg-box" style="background:rgba(59,130,246,0.2);border:1px dashed #93c5fd;"></span>Prévisions</span>
  <span class="leg"><span style="color:#dc2626;font-weight:700;font-size:14px;">|</span>&nbsp;Maintenant</span>
  <span class="leg"><span class="leg-box" style="background:#fef3c7;border:1px solid #fcd34d;"></span>Activité dégradée</span>
  <span class="leg"><span class="leg-box" style="background:#fee2e2;border:1px solid #fca5a5;"></span>Arrêt</span>
</div>

<main>

  <section>
    <h2><span class="num">01</span> Synthèse par site logistique</h2>
    <div class="cards-grid">{site_cards}</div>
  </section>

  <section>
    <h2><span class="num">02</span> Visualisation temporelle (2j passés + 7j prévisions)</h2>
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
        <canvas id="chartTaux" height="200"></canvas>
      </div>
      <div class="chart-box">
        <h3>Pertes cumulées — Terminal Eurohub Sud</h3>
        <canvas id="chartPertes" height="200"></canvas>
      </div>
    </div>
  </section>

  <section>
    <h2><span class="num">03</span> Chronologie détaillée — Terminal Eurohub Sud</h2>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Date / Heure</th><th>Précip.</th><th>Indice aléa</th>
          <th>Statut routes</th><th>Accessibilité</th><th>Taux activité</th>
          <th style="text-align:right;">Perte (€)</th>
        </tr></thead>
        <tbody>{chrono_rows}</tbody>
      </table>
    </div>
  </section>

  <section>
    <h2><span class="num">04</span> Hypothèses du modèle</h2>
    <div class="table-wrap" style="padding:4px 0;">
      <table class="hyp-table">{hyp_rows}</table>
    </div>
  </section>

</main>

<footer>
  TWICE — Prototype Digital Twin · Données météo : Open-Meteo API · Réseau routier : OpenStreetMap
</footer>

<script>
const LABELS   = {labels_js};
const PRECIP   = {precip_js};
const INDICES  = {indices_js};
const SITES    = {sites_js};
const NOW_IDX  = {now_index_js};
const N        = LABELS.length;

// ── Utilitaires ──────────────────────────────────────────────

// Couleur différente selon passé/prévision
function colorByTime(baseRgb, alphaHist, alphaFc) {{
  return LABELS.map((_, i) =>
    i <= NOW_IDX
      ? `rgba(${{baseRgb}},${{alphaHist}})`
      : `rgba(${{baseRgb}},${{alphaFc}})`
  );
}}

// Sépare une série en deux segments : passé (plein) + prévision (pointillé)
// Retourne deux datasets à superposer
function splitSeries(label, data, color, extra) {{
  const past = data.map((v, i) => i <= NOW_IDX + 1 ? v : null);
  const fc   = data.map((v, i) => i >= NOW_IDX     ? v : null);
  return [
    {{ label, data: past, borderColor: color, borderWidth: 2, pointRadius: 0, spanGaps: false, ...extra }},
    {{ label: label + ' (prévision)', data: fc, borderColor: color, borderWidth: 2,
       pointRadius: 0, borderDash: [5, 4], spanGaps: false, ...extra,
       backgroundColor: 'transparent' }}
  ];
}}

// ── Plugin "maintenant" : ligne rouge + zone prévision ───────
const nowLinePlugin = {{
  id: 'nowLine',
  beforeDraw(chart) {{
    const {{ctx, chartArea, scales}} = chart;
    if (!chartArea || !scales.x) return;
    const xPos = scales.x.getPixelForValue(NOW_IDX);
    // Zone prévision
    ctx.save();
    ctx.fillStyle = 'rgba(219,234,254,0.22)';
    ctx.fillRect(xPos, chartArea.top, chartArea.right - xPos, chartArea.bottom - chartArea.top);
    ctx.restore();
  }},
  afterDraw(chart) {{
    const {{ctx, chartArea, scales}} = chart;
    if (!chartArea || !scales.x) return;
    const xPos = scales.x.getPixelForValue(NOW_IDX);
    // Ligne
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(xPos, chartArea.top);
    ctx.lineTo(xPos, chartArea.bottom);
    ctx.strokeStyle = 'rgba(220,38,38,0.75)';
    ctx.lineWidth   = 1.5;
    ctx.setLineDash([4, 3]);
    ctx.stroke();
    // Label
    ctx.fillStyle = '#dc2626';
    ctx.font      = 'bold 10px DM Sans, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('maintenant', xPos, chartArea.top - 5);
    ctx.restore();
  }}
}};

Chart.register(nowLinePlugin);

// ── Config commune ───────────────────────────────────────────
const TF   = {{ family: 'DM Sans', size: 10 }};
const GRID = '#e2e2ee';

// Axe X : labels toutes les 12h
const xAxis = {{
  type: 'category',
  ticks: {{
    font: TF,
    maxRotation: 45,
    callback(val, i) {{ return i % 12 === 0 ? LABELS[i] : ''; }}
  }},
  grid: {{ color: GRID }}
}};

const baseOpts = (scales) => ({{
  responsive: true,
  maintainAspectRatio: true,
  animation: {{ duration: 0 }},
  plugins: {{
    legend: {{ labels: {{ font: TF, boxWidth: 12, filter: item => !item.text.includes('prévision') }} }},

  }},
  scales
}});

// ── Graphique 1 : Précipitations + indice d'aléa ────────────
new Chart(document.getElementById('chartAlea'), {{
  type: 'bar',
  data: {{
    labels: LABELS,
    datasets: [
      {{
        type: 'bar',
        label: 'Précipitations (mm/h)',
        data: PRECIP,
        backgroundColor: colorByTime('59,130,246', 0.65, 0.2),
        yAxisID: 'yP',
        order: 2
      }},
      ...splitSeries(
        'Indice d\'aléa [0–1]', INDICES,
        'rgba(220,38,38,0.9)',
        {{ type:'line', fill: false, tension: 0.3, yAxisID: 'yA', order: 1 }}
      )
    ]
  }},
  options: baseOpts({{
    x:  xAxis,
    yP: {{ type:'linear', position:'left',  title:{{ display:true, text:'mm/h', font:{{size:10}} }}, grid:{{ color:GRID }}, ticks:{{ font:TF }} }},
    yA: {{ type:'linear', position:'right', min:0, max:1, title:{{ display:true, text:'Indice', font:{{size:10}} }}, grid:{{ drawOnChartArea:false }}, ticks:{{ font:TF }} }}
  }})
}});

// ── Graphique 2 : Statut des routes ─────────────────────────
const ROUTE_IDS    = SITES[0]?.chronologie[0] ? Object.keys(SITES[0].chronologie[0].statuts_routes) : [];
const ROUTE_COLORS = ['59,130,246','5,150,105','217,119,6','168,85,247'];
const STATUT_VAL   = {{ 'normal':1.0, 'impacté':0.5, 'coupé':0.0 }};

new Chart(document.getElementById('chartRoutes'), {{
  type: 'line',
  data: {{
    labels: LABELS,
    datasets: ROUTE_IDS.flatMap((rid, i) => {{
      const vals  = SITES[0].chronologie.map(h => STATUT_VAL[h.statuts_routes[rid]] ?? 1);
      const color = `rgba(${{ROUTE_COLORS[i % ROUTE_COLORS.length]}},0.85)`;
      return splitSeries(rid.replace(/_/g,' '), vals, color, {{ stepped: true, fill: false }});
    }})
  }},
  options: baseOpts({{
    x: xAxis,
    y: {{
      min: -0.05, max: 1.1, grid: {{ color: GRID }},
      ticks: {{ font: TF, callback: v => v===1?'Normal':v===0.5?'Impacté':v===0?'Coupé':'' }}
    }}
  }})
}});

// ── Graphique 3 : Taux d'activité ───────────────────────────
if (SITES[0]) {{
  const taux = SITES[0].chronologie.map(h => h.taux_activite * 100);
  new Chart(document.getElementById('chartTaux'), {{
    type: 'line',
    data: {{
      labels: LABELS,
      datasets: splitSeries(
        'Taux d\'activité (%)', taux,
        'rgba(37,99,235,0.9)',
        {{ fill: true, backgroundColor:'rgba(37,99,235,0.08)', stepped: true }}
      )
    }},
    options: baseOpts({{
      x: xAxis,
      y: {{ min:0, max:105, grid:{{ color:GRID }}, ticks:{{ font:TF, callback: v => v+'%' }} }}
    }})
  }});
}}

// ── Graphique 4 : Pertes cumulées ───────────────────────────
if (SITES[0]) {{
  let cumul = 0;
  const cumData = SITES[0].chronologie.map(h => {{ cumul += h.perte_eur; return Math.round(cumul); }});
  new Chart(document.getElementById('chartPertes'), {{
    type: 'line',
    data: {{
      labels: LABELS,
      datasets: splitSeries(
        'Pertes cumulées (€)', cumData,
        'rgba(220,38,38,0.9)',
        {{ fill: true, backgroundColor:'rgba(220,38,38,0.07)', tension: 0.3 }}
      )
    }},
    options: baseOpts({{
      x: xAxis,
      y: {{ grid:{{ color:GRID }}, ticks:{{ font:TF, callback: v => v.toLocaleString('fr-FR')+' €' }} }}
    }})
  }});
}}
</script>

</body>
</html>"""
    return html


def main():
    print("→ Chargement des résultats...")
    data = load_results("outputs/resultats_latest.json")
    print("→ Génération du rapport HTML...")
    html = generate_html(data)
    Path("outputs/rapport.html").write_text(html, encoding="utf-8")
    print("→ Rapport généré : outputs/rapport.html")


if __name__ == "__main__":
    main()
