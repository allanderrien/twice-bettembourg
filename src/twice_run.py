"""
TWICE — Digital Twin Bettembourg
Chaine causale : pluie -> route -> accessibilite -> pertes
"""

import json
import requests
from datetime import datetime, timezone

# ============================================================
# HYPOTHESES (modifiables ici)
# ============================================================
SEUIL_MAX_MM        = 60.0
FENETRE_GLISSANTE_H = 3
SEUIL_NORMAL        = 0.70
SEUIL_ARRET         = 0.40
PAST_DAYS           = 2
FORECAST_DAYS       = 7

# ============================================================
# CONFIGURATION
# ============================================================
SITES = [
    {
        "id": "eurohub_sud",
        "nom": "Terminal Eurohub Sud",
        "type": "terminal_intermodal",
        "ca_journalier": 500000,
        "routes_critiques": {
            "A3_bettembourg":  3,
            "N31_bettembourg": 2,
            "voirie_interne":  1,
        }
    },
    {
        "id": "zone_wolser",
        "nom": "Zone industrielle Wolser",
        "type": "entrepots",
        "ca_journalier": 150000,
        "routes_critiques": {
            "N31_bettembourg": 3,
            "route_wolser":    2,
            "voirie_interne":  1,
        }
    }
]

RESEAU_ROUTIER = [
    {"id": "A3_bettembourg",  "nom": "A3 Bettembourg",            "type": "motorway",  "seuil_impact": 0.50, "seuil_coupure": 1.00},
    {"id": "N31_bettembourg", "nom": "N31 Bettembourg-Dudelange", "type": "primary",   "seuil_impact": 0.42, "seuil_coupure": 0.83},
    {"id": "voirie_interne",  "nom": "Voirie interne terminal",   "type": "secondary", "seuil_impact": 0.33, "seuil_coupure": 0.67},
    {"id": "route_wolser",    "nom": "Route zone Wolser",         "type": "secondary", "seuil_impact": 0.33, "seuil_coupure": 0.67},
]

STATUT_VERS_SCORE = {"normal": 1.0, "impacte": 0.5, "coupe": 0.0}


# ============================================================
# FONCTIONS
# ============================================================

def fetch_meteo():
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":      49.525,
        "longitude":     6.110,
        "hourly":        "precipitation",
        "past_days":     PAST_DAYS,
        "forecast_days": FORECAST_DAYS,
        "timezone":      "Europe/Luxembourg",
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    times  = data["hourly"]["time"]
    precip = data["hourly"]["precipitation"]

    now_str   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
    now_index = max(i for i, t in enumerate(times) if t <= now_str)

    return times, precip, now_index


def indice_alea(precip):
    out = []
    for i in range(len(precip)):
        debut = max(0, i - FENETRE_GLISSANTE_H + 1)
        cumul = sum(float(p or 0) for p in precip[debut:i+1])
        out.append(round(min(cumul / SEUIL_MAX_MM, 1.0), 3))
    return out


def statut_route(seuil_impact, seuil_coupure, idx):
    if idx >= seuil_coupure: return "coupe"
    if idx >= seuil_impact:  return "impacte"
    return "normal"


def accessibilite(site, statuts):
    score  = 0.0
    poids  = 0.0
    for rid, p in site["routes_critiques"].items():
        s      = statuts.get(rid, "normal")
        score += p * STATUT_VERS_SCORE[s]
        poids += p
    return round(score / poids, 3) if poids else 1.0


def taux_activite(acc):
    if acc >= SEUIL_NORMAL: return 1.0
    if acc <= SEUIL_ARRET:  return 0.0
    return round((acc - SEUIL_ARRET) / (SEUIL_NORMAL - SEUIL_ARRET), 3)


def run():
    print("=== TWICE démarrage ===")
    times, precip, now_index = fetch_meteo()
    print(f"  {len(times)} heures, now_index={now_index} ({times[now_index]})")

    indices = indice_alea(precip)

    resultats = []
    for site in SITES:
        chrono = []
        for i, idx in enumerate(indices):
            statuts = {
                r["id"]: statut_route(r["seuil_impact"], r["seuil_coupure"], idx)
                for r in RESEAU_ROUTIER
            }
            acc   = accessibilite(site, statuts)
            taux  = taux_activite(acc)
            perte = round((site["ca_journalier"] / 24.0) * (1.0 - taux), 2)
            chrono.append({
                "time":            times[i],
                "is_forecast":     i > now_index,
                "precipitation_mm": float(precip[i] or 0),
                "indice_alea":     indices[i],
                "accessibilite":   acc,
                "taux_activite":   taux,
                "perte_eur":       perte,
                "statuts_routes":  statuts,
            })

        resultats.append({
            "site_id":           site["id"],
            "site_nom":          site["nom"],
            "type":              site["type"],
            "ca_journalier_eur": site["ca_journalier"],
            "perte_totale_eur":  round(sum(h["perte_eur"] for h in chrono), 2),
            "heures_normales":   sum(1 for h in chrono if h["taux_activite"] == 1.0),
            "heures_degradees":  sum(1 for h in chrono if 0 < h["taux_activite"] < 1.0),
            "heures_arret":      sum(1 for h in chrono if h["taux_activite"] == 0.0),
            "accessibilite_min": min(h["accessibilite"] for h in chrono),
            "chronologie":       chrono,
        })
        print(f"  [{site['nom']}] perte={resultats[-1]['perte_totale_eur']:,.0f}€  arret={resultats[-1]['heures_arret']}h")

    rapport = {
        "projet":       "TWICE",
        "zone":         "Bettembourg, Luxembourg",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "now_index":    now_index,
        "hypotheses": {
            "H1": f"Indice = cumul {FENETRE_GLISSANTE_H}h glissantes / {SEUIL_MAX_MM}mm",
            "H2": "Route impactee si indice >= seuil_impact, coupee si >= seuil_coupure",
            "H3": f"Activite pleine si accessibilite >= {SEUIL_NORMAL}, arret si <= {SEUIL_ARRET}",
            "H4": "CA journalier reparti uniformement sur 24h",
            "H5": "CA journalier = parametre fictif a calibrer",
            "H6": f"Fenetre = {PAST_DAYS}j historiques + {FORECAST_DAYS}j previsions",
        },
        "meteo": {
            "times":         times,
            "precipitation": [float(p or 0) for p in precip],
            "now_index":     now_index,
        },
        "indices_alea": indices,
        "resultats":    resultats,
    }

    import os
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/resultats_latest.json", "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)
    print("  Sauvegarde : outputs/resultats_latest.json")
    print("=== TWICE termine ===")


if __name__ == "__main__":
    run()
