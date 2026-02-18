"""
TWICE — Digital Twin Bettembourg
Chaîne causale : pluie → route → accessibilité → pertes
Exécuté via GitHub Actions
"""

import json
import requests
from datetime import datetime, timezone


# ============================================================
# HYPOTHÈSES EXPLICITES (modifiables ici)
# ============================================================
SEUIL_MAX_MM        = 60.0   # H1 : 60mm sur 3h = saturation indice=1.0
FENETRE_GLISSANTE_H = 3      # H2 : cumul sur 3h glissantes
SEUIL_NORMAL        = 0.70   # H3 : accessibilité > 70% → activité pleine
SEUIL_ARRET         = 0.40   # H4 : accessibilité < 40% → arrêt complet
HEURES_HISTORIQUE   = 48     # H5 : on analyse les 48 dernières heures


# ============================================================
# CONFIGURATION DES SITES ET DU RÉSEAU
# ============================================================

SITES = [
    {
        "id": "eurohub_sud",
        "nom": "Terminal Eurohub Sud",
        "type": "terminal_intermodal",
        "ca_journalier": 500_000,   # € — paramètre fictif, à calibrer
        "routes_critiques": {
            "A3_bettembourg":   3,  # autoroute, poids fort
            "N31_bettembourg":  2,  # nationale
            "voirie_interne":   1,  # accès local terminal
        }
    },
    {
        "id": "zone_wolser",
        "nom": "Zone industrielle Wolser",
        "type": "entrepots",
        "ca_journalier": 150_000,   # € — paramètre fictif, à calibrer
        "routes_critiques": {
            "N31_bettembourg":  3,  # accès principal
            "route_wolser":     2,  # route locale zone
            "voirie_interne":   1,
        }
    }
]

RESEAU_ROUTIER = [
    # seuil_impact et seuil_coupure exprimés en indice [0-1]
    # correspondances mm : impact=30mm/3h → 0.50 ; coupure=60mm/3h → 1.00
    {"id": "A3_bettembourg",  "nom": "A3 Bettembourg",            "type": "motorway",  "seuil_impact": 0.50, "seuil_coupure": 1.00, "statut": "normal"},
    {"id": "N31_bettembourg", "nom": "N31 Bettembourg-Dudelange", "type": "primary",   "seuil_impact": 0.42, "seuil_coupure": 0.83, "statut": "normal"},
    {"id": "voirie_interne",  "nom": "Voirie interne terminal",   "type": "secondary", "seuil_impact": 0.33, "seuil_coupure": 0.67, "statut": "normal"},
    {"id": "route_wolser",    "nom": "Route zone Wolser",         "type": "secondary", "seuil_impact": 0.33, "seuil_coupure": 0.67, "statut": "normal"},
]


# ============================================================
# ÉTAPE 1 — Récupération des données Open-Meteo
# ============================================================

def fetch_precipitations_openmeteo(lat: float = 49.525,
                                    lon: float = 6.110,
                                    heures: int = HEURES_HISTORIQUE) -> dict:
    """
    Récupère les précipitations horaires passées via Open-Meteo.
    Coordonnées centrées sur Bettembourg.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":            lat,
        "longitude":           lon,
        "hourly":              "precipitation",
        "past_days":           2,
        "forecast_days":       1,
        "timezone":            "Europe/Luxembourg",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    times          = data["hourly"]["time"]
    precipitations = data["hourly"]["precipitation"]

    # On garde les N dernières heures
    times          = times[-heures:]
    precipitations = precipitations[-heures:]

    return {
        "source":        "Open-Meteo",
        "latitude":      lat,
        "longitude":     lon,
        "times":         times,
        "precipitation": precipitations,
        "fetched_at":    datetime.now(timezone.utc).isoformat(),
    }


# ============================================================
# ÉTAPE 2 — Indice d'aléa
# ============================================================

def calculer_indice_alea(precipitations: list,
                          fenetre: int = FENETRE_GLISSANTE_H) -> list:
    """
    Transforme les précipitations horaires en indice d'aléa [0–1].
    Indice = cumul sur fenêtre glissante / SEUIL_MAX_MM
    """
    indices = []
    for i in range(len(precipitations)):
        debut  = max(0, i - fenetre + 1)
        cumul  = sum(float(p or 0) for p in precipitations[debut:i+1])
        indice = min(cumul / SEUIL_MAX_MM, 1.0)
        indices.append(round(indice, 3))
    return indices


# ============================================================
# ÉTAPE 3 — Statut des routes
# ============================================================

STATUT_VERS_SCORE = {
    "normal":  1.0,
    "impacté": 0.5,
    "coupé":   0.0,
}

def evaluer_statut_route(route: dict, indice: float) -> str:
    if indice >= route["seuil_coupure"]:
        return "coupé"
    elif indice >= route["seuil_impact"]:
        return "impacté"
    return "normal"

def marquer_routes(reseau: list, indice: float) -> list:
    for route in reseau:
        route["statut"] = evaluer_statut_route(route, indice)
    return reseau


# ============================================================
# ÉTAPE 4 — Accessibilité et taux d'activité
# ============================================================

def calculer_accessibilite(site: dict, reseau: list) -> float:
    routes_par_id = {r["id"]: r for r in reseau}
    score_pondere = 0.0
    poids_total   = 0.0
    for route_id, poids in site["routes_critiques"].items():
        if route_id in routes_par_id:
            statut         = routes_par_id[route_id]["statut"]
            score_pondere += poids * STATUT_VERS_SCORE[statut]
            poids_total   += poids
    return round(score_pondere / poids_total, 3) if poids_total > 0 else 1.0

def accessibilite_vers_taux(score: float) -> float:
    if score >= SEUIL_NORMAL:
        return 1.0
    elif score <= SEUIL_ARRET:
        return 0.0
    return round((score - SEUIL_ARRET) / (SEUIL_NORMAL - SEUIL_ARRET), 3)


# ============================================================
# ÉTAPE 5 — Pertes économiques
# ============================================================

def calculer_perte_horaire(site: dict, taux: float) -> float:
    return round((site["ca_journalier"] / 24.0) * (1.0 - taux), 2)


# ============================================================
# ORCHESTRATION PRINCIPALE
# ============================================================

def run_twice():
    print("=== TWICE — Démarrage ===")

    # 1. Données météo
    print("→ Récupération Open-Meteo...")
    meteo = fetch_precipitations_openmeteo()
    precipitations = meteo["precipitation"]
    times          = meteo["times"]
    print(f"   {len(precipitations)} heures récupérées")

    # 2. Indices d'aléa
    indices = calculer_indice_alea(precipitations)
    indice_max = max(indices)
    print(f"   Indice d'aléa max : {indice_max:.3f}")

    # 3. Calcul par site
    resultats_sites = []

    for site in SITES:
        pertes_h       = []
        taux_h         = []
        access_h       = []
        statuts_routes = []

        for i, indice_t in enumerate(indices):
            reseau_t = [dict(r) for r in RESEAU_ROUTIER]  # copie fraîche
            reseau_t = marquer_routes(reseau_t, indice_t)

            access = calculer_accessibilite(site, reseau_t)
            taux   = accessibilite_vers_taux(access)
            perte  = calculer_perte_horaire(site, taux)

            access_h.append(access)
            taux_h.append(taux)
            pertes_h.append(perte)
            statuts_routes.append({r["id"]: r["statut"] for r in reseau_t})

        # Chronologie complète
        chronologie = [
            {
                "time":         times[i],
                "precipitation_mm": float(precipitations[i] or 0),
                "indice_alea":  indices[i],
                "accessibilite": access_h[i],
                "taux_activite": taux_h[i],
                "perte_eur":    pertes_h[i],
                "statuts_routes": statuts_routes[i],
            }
            for i in range(len(times))
        ]

        resultat_site = {
            "site_id":           site["id"],
            "site_nom":          site["nom"],
            "ca_journalier_eur": site["ca_journalier"],
            "perte_totale_eur":  round(sum(pertes_h), 2),
            "heures_normales":   sum(1 for t in taux_h if t == 1.0),
            "heures_degradees":  sum(1 for t in taux_h if 0 < t < 1.0),
            "heures_arret":      sum(1 for t in taux_h if t == 0.0),
            "accessibilite_min": min(access_h),
            "chronologie":       chronologie,
        }

        resultats_sites.append(resultat_site)
        print(f"   [{site['nom']}] perte totale : {resultat_site['perte_totale_eur']:,.0f} €"
              f"  |  arrêt : {resultat_site['heures_arret']}h"
              f"  |  dégradé : {resultat_site['heures_degradees']}h")

    # 4. Assemblage du rapport final
    rapport = {
        "projet":        "TWICE",
        "zone":          "Bettembourg, Luxembourg",
        "generated_at":  datetime.now(timezone.utc).isoformat(),
        "hypotheses": {
            "H1": f"Indice d'aléa = cumul {FENETRE_GLISSANTE_H}h / {SEUIL_MAX_MM}mm (pas de modèle hydraulique)",
            "H2": f"Route impactée si indice ≥ seuil_impact, coupée si ≥ seuil_coupure",
            "H3": f"Activité pleine si accessibilité ≥ {SEUIL_NORMAL}, arrêt si ≤ {SEUIL_ARRET}",
            "H4": "CA journalier réparti uniformément sur 24h",
            "H5": "CA journalier = paramètre fictif à calibrer",
        },
        "meteo":         meteo,
        "indices_alea":  indices,
        "resultats":     resultats_sites,
    }

    # 5. Sauvegarde
    output_path = "outputs/resultats_latest.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rapport, f, ensure_ascii=False, indent=2)

    print(f"→ Résultats sauvegardés : {output_path}")
    print("=== TWICE — Terminé ===")

    return rapport


if __name__ == "__main__":
    run_twice()
