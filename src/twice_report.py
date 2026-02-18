"""
TWICE — Generateur de rapport HTML
Version epuree : Chart.js standard, aucun plugin custom
"""

import json
from pathlib import Path


def fmt_date(iso):
    if len(iso) >= 16:
        return f"{iso[8:10]}/{iso[5:7]} {iso[11:16]}"
    return iso


def fmt_eur(v):
    return f"{int(v):,} EUR".replace(",", " ")


def badge(statut):
    c = {"normal": ("#d1fae5","#065f46"), "impacte": ("#fef3c7","#92400e"), "coupe": ("#fee2e2","#991b1b")}
    bg, fg = c.get(statut, ("#f3f4f6","#374151"))
    label  = {"normal":"normal","impacte":"impacte","coupe":"coupe"}.get(statut, statut)
    return f'<span style="background:{bg};color:{fg};padding:1px 7px;border-radius:3px;font-size:11px;font-weight:600">{label}</span>'


def generate(data):
    times      = data["meteo"]["times"]
    precip     = data["meteo"]["precipitation"]
    indices    = data["indices_alea"]
    resultats  = data["resultats"]
    now_index  = data["now_index"]
    gen_at     = data["generated_at"][:16].replace("T", " ")
    hypotheses = data["hypotheses"]

    n = len(times)

    # Labels JJ/MM HH:MM
    labels     = [fmt_date(t) for t in times]
    labels_js  = json.dumps(labels)
    precip_js  = json.dumps(precip)
    indices_js = json.dumps(indices)
    now_js     = now_index

    # Taux et pertes site 0
    taux0   = [h["taux_activite"] * 100 for h in resultats[0]["chronologie"]]
    pertes0 = []
    cumul   = 0
    for h in resultats[0]["chronologie"]:
        cumul += h["perte_eur"]
        pertes0.append(round(cumul))
    taux0_js   = json.dumps(taux0)
    pertes0_js = json.dumps(pertes0)

    # Routes
    route_ids = list(resultats[0]["chronologie"][0]["statuts_routes"].keys())
    STATUT_VAL = {"normal": 1.0, "impacte": 0.5, "coupe": 0.0}
    routes_data = {}
    for rid in route_ids:
        routes_data[rid] = [STATUT_VAL.get(h["statuts_routes"][rid], 1.0)
                            for h in resultats[0]["chronologie"]]
    routes_js = json.dumps(routes_data)
    route_ids_js = json.dumps(route_ids)

    # Cartes KPI
    cards_html = ""
    for s in resultats:
        cards_html += f"""
        <div class="card">
          <div class="card-title">{s['site_nom']}</div>
          <div class="card-sub">{s['type']}</div>
          <div class="kpis">
            <div class="kpi"><div class="kv red">{fmt_eur(s['perte_totale_eur'])}</div><div class="kl">Perte totale</div></div>
            <div class="kpi"><div class="kv">{s['heures_arret']}h</div><div class="kl">A l arret</div></div>
            <div class="kpi"><div class="kv">{s['heures_degradees']}h</div><div class="kl">Degradees</div></div>
            <div class="kpi"><div class="kv">{s['accessibilite_min']:.0%}</div><div class="kl">Access. min</div></div>
          </div>
        </div>"""

    # Tableau chronologique
    rows_html = ""
    for h in resultats[0]["chronologie"]:
        td     = fmt_date(h["time"])
        p      = f"{h['precipitation_mm']:.1f} mm"
        ia     = f"{h['indice_alea']:.2f}"
        acc    = f"{h['accessibilite']:.0%}"
        taux   = f"{h['taux_activite']:.0%}"
        perte  = fmt_eur(h["perte_eur"])
        badges = " ".join(badge(v) for v in h["statuts_routes"].values())
        fc     = ' <small style="color:#2563eb;font-weight:600">PREVIS.</small>' if h["is_forecast"] else ""

        if h["taux_activite"] == 0:
            bg = 'style="background:#fff5f5"'
        elif h["taux_activite"] < 1:
            bg = 'style="background:#fffbeb"'
        elif h["is_forecast"]:
            bg = 'style="background:#f0f9ff"'
        else:
            bg = ""

        rows_html += f"""<tr {bg}>
          <td>{td}{fc}</td><td>{p}</td><td>{ia}</td>
          <td>{badges}</td><td>{acc}</td><td>{taux}</td>
          <td style="text-align:right;font-weight:600">{perte}</td>
        </tr>"""

    # Hypotheses
    hyp_html = ""
    for k, v in hypotheses.items():
        hyp_html += f"<tr><td><b>{k}</b></td><td>{v}</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>TWICE — Rapport Bettembourg</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
* {{ box-sizing:border-box; margin:0; padding:0 }}
body {{ font-family:Inter,sans-serif; background:#f4f5f7; color:#1e2433; font-size:14px }}

header {{ background:#1e2433; color:#fff; padding:28px 40px; display:flex; justify-content:space-between; align-items:center }}
header h1 {{ font-size:22px; font-weight:600; letter-spacing:-.3px }}
header .sub {{ color:#8892a4; font-size:12px; margin-top:4px }}
.badge-proto {{ background:#2563eb; color:#fff; font-size:10px; font-weight:700; padding:3px 9px; border-radius:12px; letter-spacing:.5px }}
.meta {{ text-align:right; font-size:12px; color:#8892a4 }}

.chain {{ background:#fff; border-bottom:1px solid #e4e6ea; padding:12px 40px; display:flex; align-items:center; gap:0; overflow-x:auto; font-size:12px; color:#4b5563; font-weight:500 }}
.cs {{ white-space:nowrap; padding:4px 10px; border-radius:4px; background:#f4f5f7; border:1px solid #e4e6ea }}
.ca {{ margin:0 6px; color:#2563eb }}

main {{ padding:28px 40px; max-width:1300px; margin:0 auto }}
section {{ margin-bottom:36px }}
h2 {{ font-size:16px; font-weight:600; margin-bottom:14px; padding-bottom:8px; border-bottom:2px solid #1e2433; display:flex; align-items:center; gap:8px }}
.sec-num {{ font-size:10px; font-weight:700; color:#2563eb; background:#eff6ff; padding:2px 7px; border-radius:3px; letter-spacing:1px }}

.cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(340px,1fr)); gap:16px }}
.card {{ background:#fff; border:1px solid #e4e6ea; border-radius:8px; padding:20px; border-top:3px solid #2563eb }}
.card-title {{ font-size:16px; font-weight:600; margin-bottom:2px }}
.card-sub {{ font-size:11px; color:#8892a4; text-transform:uppercase; letter-spacing:.7px; margin-bottom:16px }}
.kpis {{ display:grid; grid-template-columns:repeat(2,1fr); gap:12px }}
.kv {{ font-size:20px; font-weight:700 }}
.kv.red {{ color:#dc2626 }}
.kl {{ font-size:10px; color:#8892a4; text-transform:uppercase; letter-spacing:.5px; margin-top:2px }}

.charts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(440px,1fr)); gap:16px }}
.chart-box {{ background:#fff; border:1px solid #e4e6ea; border-radius:8px; padding:18px 20px }}
.chart-box h3 {{ font-size:11px; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:.7px; margin-bottom:14px }}

.now-label {{ display:flex; align-items:center; gap:16px; font-size:12px; color:#6b7280; margin-bottom:14px; padding:8px 12px; background:#fff; border:1px solid #e4e6ea; border-radius:6px; width:fit-content }}
.dot {{ width:12px; height:3px; border-radius:2px }}

.tbl-wrap {{ background:#fff; border:1px solid #e4e6ea; border-radius:8px; overflow:auto; max-height:460px }}
table {{ width:100%; border-collapse:collapse; font-size:12px }}
thead tr {{ background:#1e2433; color:#fff; position:sticky; top:0 }}
thead th {{ padding:9px 12px; text-align:left; font-weight:500; font-size:11px; text-transform:uppercase; letter-spacing:.4px; white-space:nowrap }}
tbody tr {{ border-bottom:1px solid #f0f1f3 }}
tbody tr:hover {{ filter:brightness(.97) }}
tbody td {{ padding:7px 12px; vertical-align:middle }}

.hyp-tbl {{ width:100%; border-collapse:collapse; font-size:13px }}
.hyp-tbl td {{ padding:7px 12px; border-bottom:1px solid #f0f1f3 }}
.hyp-tbl tr:last-child td {{ border-bottom:none }}

footer {{ text-align:center; padding:20px; font-size:11px; color:#9ca3af; border-top:1px solid #e4e6ea; margin-top:20px }}
</style>
</head>
<body>

<header>
  <div>
    <h1>TWICE &mdash; Digital Twin Bettembourg</h1>
    <div class="sub">Interruption d'activite sans dommage direct &middot; Zone logistique Luxembourg</div>
  </div>
  <div class="meta">
    <div class="badge-proto">PROTOTYPE</div>
    <div style="margin-top:6px">Genere le {gen_at} UTC</div>
  </div>
</header>

<div class="chain">
  <span class="cs">Precipitations</span><span class="ca">&#8594;</span>
  <span class="cs">Indice d'alea</span><span class="ca">&#8594;</span>
  <span class="cs">Statut routes</span><span class="ca">&#8594;</span>
  <span class="cs">Accessibilite</span><span class="ca">&#8594;</span>
  <span class="cs">Pertes economiques</span>
</div>

<main>

<section>
  <h2><span class="sec-num">01</span> Synthese par site</h2>
  <div class="cards">{cards_html}</div>
</section>

<section>
  <h2><span class="sec-num">02</span> Visualisation temporelle</h2>
  <div class="now-label">
    <span><span style="color:#dc2626;font-weight:700">|</span> = maintenant (separation historique / previsions)</span>
    <span><span class="dot" style="background:rgba(59,130,246,.6)"></span> Historique</span>
    <span><span class="dot" style="background:rgba(59,130,246,.2);border:1px dashed #93c5fd"></span> Previsions</span>
  </div>
  <div class="charts">
    <div class="chart-box"><h3>Precipitations (mm/h) &amp; indice d'alea</h3><canvas id="cAlea" height="200"></canvas></div>
    <div class="chart-box"><h3>Statut des routes</h3><canvas id="cRoutes" height="200"></canvas></div>
    <div class="chart-box"><h3>Taux d'activite — Eurohub Sud</h3><canvas id="cTaux" height="200"></canvas></div>
    <div class="chart-box"><h3>Pertes cumulees — Eurohub Sud</h3><canvas id="cPertes" height="200"></canvas></div>
  </div>
</section>

<section>
  <h2><span class="sec-num">03</span> Chronologie detaillee — Terminal Eurohub Sud</h2>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>Date/Heure</th><th>Precip.</th><th>Indice</th>
        <th>Routes</th><th>Accessib.</th><th>Taux act.</th>
        <th style="text-align:right">Perte</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</section>

<section>
  <h2><span class="sec-num">04</span> Hypotheses</h2>
  <div class="tbl-wrap">
    <table class="hyp-tbl">{hyp_html}</table>
  </div>
</section>

</main>

<footer>TWICE Prototype &middot; Meteo : Open-Meteo &middot; Reseau : OpenStreetMap</footer>

<script>
var LABELS    = {labels_js};
var PRECIP    = {precip_js};
var INDICES   = {indices_js};
var TAUX0     = {taux0_js};
var PERTES0   = {pertes0_js};
var ROUTES    = {routes_js};
var ROUTE_IDS = {route_ids_js};
var NOW       = {now_js};
var N         = LABELS.length;

var GRID  = '#e9eaec';
var TFONT = {{family:'Inter',size:10}};

// Annotation ligne "maintenant" via un dataset vertical factice
// Methode simple : on dessine via un plugin inline sans Chart.register global
var nowPlugin = {{
  id: 'nowLine',
  afterDatasetsDraw: function(chart) {{
    var ctx = chart.ctx;
    var ca  = chart.chartArea;
    var x   = chart.scales.x.getPixelForValue(NOW);
    if (!ca || isNaN(x)) return;
    ctx.save();
    ctx.strokeStyle = '#dc2626';
    ctx.lineWidth   = 1.5;
    ctx.setLineDash([4,3]);
    ctx.beginPath(); ctx.moveTo(x, ca.top); ctx.lineTo(x, ca.bottom); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#dc2626'; ctx.font = 'bold 9px Inter,sans-serif'; ctx.textAlign = 'center';
    ctx.fillText('maintenant', x, ca.top - 4);
    ctx.restore();
  }}
}};

var xCfg = {{
  ticks: {{
    font: TFONT, maxRotation: 45,
    callback: function(v,i) {{ return i % 12 === 0 ? LABELS[i] : ''; }}
  }},
  grid: {{color: GRID}}
}};

var bgPrecip = PRECIP.map(function(_,i){{
  return i <= NOW ? 'rgba(59,130,246,.65)' : 'rgba(59,130,246,.18)';
}});

// ── Graphique 1 : Precip + indice ──
new Chart(document.getElementById('cAlea'), {{
  type: 'bar',
  plugins: [nowPlugin],
  data: {{
    labels: LABELS,
    datasets: [
      {{
        type: 'bar', label: 'Precip (mm/h)', data: PRECIP,
        backgroundColor: bgPrecip, yAxisID: 'yP', order: 2
      }},
      {{
        type: 'line', label: 'Indice alea', data: INDICES,
        borderColor: '#dc2626', backgroundColor: 'rgba(220,38,38,.06)',
        borderWidth: 2, pointRadius: 0, fill: true, tension: .3,
        yAxisID: 'yA', order: 1
      }}
    ]
  }},
  options: {{
    responsive: true, maintainAspectRatio: true, animation: false,
    plugins: {{legend: {{labels: {{font: TFONT, boxWidth:12}}}}}},
    scales: {{
      x:  xCfg,
      yP: {{type:'linear',position:'left', grid:{{color:GRID}},ticks:{{font:TFONT}},title:{{display:true,text:'mm/h',font:{{size:9}}}}}},
      yA: {{type:'linear',position:'right',min:0,max:1,grid:{{drawOnChartArea:false}},ticks:{{font:TFONT}},title:{{display:true,text:'Indice',font:{{size:9}}}}}}
    }}
  }}
}});

// ── Graphique 2 : Routes ──
var RCOLS = ['#2563eb','#059669','#d97706','#7c3aed'];
var rDatasets = ROUTE_IDS.map(function(rid, i) {{
  return {{
    label: rid.replace(/_/g,' '),
    data:  ROUTES[rid],
    borderColor: RCOLS[i % RCOLS.length],
    backgroundColor: 'transparent',
    borderWidth: 2, pointRadius: 0, stepped: true, tension: 0
  }};
}});

new Chart(document.getElementById('cRoutes'), {{
  type: 'line',
  plugins: [nowPlugin],
  data: {{labels: LABELS, datasets: rDatasets}},
  options: {{
    responsive: true, maintainAspectRatio: true, animation: false,
    plugins: {{legend: {{labels: {{font: TFONT, boxWidth:12}}}}}},
    scales: {{
      x: xCfg,
      y: {{
        min: -.1, max: 1.1, grid: {{color:GRID}},
        ticks: {{font:TFONT, callback: function(v){{
          return v===1?'Normal':v===.5?'Impacte':v===0?'Coupe':'';
        }}}}
      }}
    }}
  }}
}});

// ── Graphique 3 : Taux activite ──
new Chart(document.getElementById('cTaux'), {{
  type: 'line',
  plugins: [nowPlugin],
  data: {{
    labels: LABELS,
    datasets: [{{
      label: 'Taux activite (%)',
      data: TAUX0,
      borderColor: '#2563eb', backgroundColor: 'rgba(37,99,235,.08)',
      borderWidth: 2, pointRadius: 0, fill: true, stepped: true
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: true, animation: false,
    plugins: {{legend: {{labels: {{font: TFONT, boxWidth:12}}}}}},
    scales: {{
      x: xCfg,
      y: {{min:0,max:105,grid:{{color:GRID}},ticks:{{font:TFONT,callback:function(v){{return v+'%';}}}}}}
    }}
  }}
}});

// ── Graphique 4 : Pertes cumulees ──
new Chart(document.getElementById('cPertes'), {{
  type: 'line',
  plugins: [nowPlugin],
  data: {{
    labels: LABELS,
    datasets: [{{
      label: 'Pertes cumulees',
      data: PERTES0,
      borderColor: '#dc2626', backgroundColor: 'rgba(220,38,38,.07)',
      borderWidth: 2, pointRadius: 0, fill: true, tension: .3
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: true, animation: false,
    plugins: {{legend: {{labels: {{font: TFONT, boxWidth:12}}}}}},
    scales: {{
      x: xCfg,
      y: {{grid:{{color:GRID}},ticks:{{font:TFONT,callback:function(v){{return v.toLocaleString('fr-FR')+' EUR';}}}}}}
    }}
  }}
}});
</script>
</body>
</html>"""


def main():
    print("Chargement resultats...")
    with open("outputs/resultats_latest.json", encoding="utf-8") as f:
        data = json.load(f)
    print("Generation rapport HTML...")
    html = generate(data)
    import os
    os.makedirs("docs", exist_ok=True)
    Path("outputs/rapport.html").write_text(html, encoding="utf-8")
    Path("docs/rapport.html").write_text(html, encoding="utf-8")
    print("Rapport genere : outputs/rapport.html + docs/rapport.html")


if __name__ == "__main__":
    main()
