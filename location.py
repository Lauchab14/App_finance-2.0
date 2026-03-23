"""
location.py — Analyse de localisation par région pour l'analyseur de rentabilité v2.0
"""
import plotly.graph_objects as go
from config import REGIONS, CRITERES_LOCALISATION


def calculer_score_localisation(notes: dict, region: str) -> dict:
    """
    Calcule le score de localisation /10 avec les pondérations de la région.

    Args:
        notes: dict avec les clés (transport, ecoles, commerces, ...) et notes 1-5
        region: clé de la région dans REGIONS

    Returns:
        dict avec score, détails par critère, et résumé
    """
    poids = REGIONS.get(region)
    if not poids:
        poids = list(REGIONS.values())[0]

    details = []
    score_pondere = 0.0

    # Base par défaut (manuel) OU notes automatiques fournies
    if not notes:
        notes = {k: 3 for k in CRITERES_LOCALISATION.keys()}

    for cle, info in CRITERES_LOCALISATION.items():
        note = notes.get(cle, 3)
        ponderation = poids.get(cle, 0.1)
        contribution = note * ponderation
        score_pondere += contribution

        details.append(
            {
                "cle": cle,
                "label": info["label"],
                "note": note,
                "ponderation": ponderation,
                "ponderation_pct": round(ponderation * 100),
                "contribution": round(contribution, 2),
            }
        )

    # Score sur 5 → ramener sur 10
    score_final = round(score_pondere * 2, 1)

    # Résumé textuel
    if score_final >= 8:
        resume = "🟢 **Excellente localisation** — L'emplacement est un atout majeur pour cet investissement."
    elif score_final >= 6:
        resume = "🟡 **Bonne localisation** — L'emplacement est favorable avec quelques points à améliorer."
    elif score_final >= 4:
        resume = "🟠 **Localisation correcte** — Certains facteurs limitent l'attractivité du secteur."
    else:
        resume = "🔴 **Localisation faible** — L'emplacement représente un risque pour la location."

    # Points forts et faibles
    details_tries = sorted(details, key=lambda d: d["note"], reverse=True)
    points_forts = [d["label"] for d in details_tries if d["note"] >= 4][:3]
    points_faibles = [d["label"] for d in details_tries if d["note"] <= 2][:3]

    if points_forts:
        resume += f"\n\n🟢 **Points forts** : {', '.join(points_forts)}."
    if points_faibles:
        resume += f"\n\n🔴 **Points à améliorer** : {', '.join(points_faibles)}."

    return {
        "score": score_final,
        "details": details,
        "resume": resume,
    }


def creer_graphique_radar(details: list, region: str) -> go.Figure:
    """
    Crée un graphique radar Plotly pour visualiser les scores de localisation.
    """
    labels = [d["label"] for d in details]
    notes = [d["note"] for d in details]
    ponderations_pct = [d["ponderation_pct"] for d in details]

    # Fermer le polygone
    labels_ferme = labels + [labels[0]]
    notes_ferme = notes + [notes[0]]

    # Texte personnalisé pour hover
    hover_text = [
        f"{l}<br>Note : {n}/5<br>Poids : {p}%"
        for l, n, p in zip(labels, notes, ponderations_pct)
    ]
    hover_text.append(hover_text[0])

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=notes_ferme,
            theta=labels_ferme,
            fill="toself",
            fillcolor="rgba(99, 110, 250, 0.25)",
            line=dict(color="#636EFA", width=2),
            hovertext=hover_text,
            hoverinfo="text",
            name="Score",
        )
    )

    # Nom court de la région pour le titre
    nom_region = region.split("(")[0].strip() if "(" in region else region

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=["1", "2", "3", "4", "5"],
                gridcolor="rgba(255,255,255,0.1)",
            ),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        title=dict(
            text=f"Analyse de localisation — Région {nom_region}",
            font=dict(size=16),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=450,
        margin=dict(t=60, b=30, l=60, r=60),
    )

    return fig


from geocoding import _haversine

def calculer_score_localisation_avance(trajets: dict, stats_demo: dict, lat: float = None, lon: float = None) -> dict:
    """
    Calcule un score sur 100 basé sur les temps de transport locaux (55 pts),
    le profil démographique, et la proximité d'un grand centre.
    """
    points = 0
    details = []
    trajet_score_target = 55
    max_points = 98
    
    # 1. Analyse des trajets (55 points)
    # Le bareme est volontairement plus faible pour les parcs, puis
    # renormalise sur 55 pts pour garder un score global coherent /100.
    bareme_trajet = {
        "epicerie": 11,
        "primaire": 5,
        "secondaire": 3,
        "cegep": 2,
        "universite": 1,
        "pharmacie": 11,
        "bus": 8,
        "parc": 6
    }
    trajet_scale = trajet_score_target / sum(bareme_trajet.values())

    score_trajets = 0
    for service, max_pts in bareme_trajet.items():
        max_pts_scaled = max_pts * trajet_scale
        trajet_info = trajets.get(service)
        if trajet_info and trajet_info.get("temps_min"):
            t = trajet_info["temps_min"]
            if service == "secondaire":
                if t <= 5:
                    pts = max_pts
                elif t <= 10:
                    pts = max_pts * 0.85
                elif t <= 15:
                    pts = max_pts * 0.6
                elif t <= 20:
                    pts = max_pts * 0.35
                else:
                    pts = 0
            else:
                if t <= 3:
                    pts = max_pts
                elif t <= 5:
                    pts = max_pts * 0.8
                elif t <= 10:
                    pts = max_pts * 0.5
                elif t <= 15:
                    pts = max_pts * 0.2
                else:
                    pts = 0

            pts_scaled = pts * trajet_scale
            score_trajets += pts_scaled
            details.append({"critere": f"Proximité {service}", "points": round(pts_scaled, 1), "max": round(max_pts_scaled, 1), "valeur": f"{t} min"})
        else:
            details.append({"critere": f"Proximité {service}", "points": 0, "max": round(max_pts_scaled, 1), "valeur": "Non trouvé / Inconnu"})
            
    points += score_trajets
    
    # 2. Analyse démographique (35 points)
    # Revenu médian (10 pts)
    pts_revenu = 0
    rev = stats_demo.get("revenu_median")
    if rev:
        if rev > 90000: pts_revenu = 10
        elif rev > 75000: pts_revenu = 8
        elif rev > 60000: pts_revenu = 5
        elif rev > 45000: pts_revenu = 2
        else: pts_revenu = 0
        details.append({"critere": "Revenu médian", "points": pts_revenu, "max": 10, "valeur": f"{rev:,.0f} $".replace(',', ' ')})
    else:
        details.append({"critere": "Revenu médian", "points": 0, "max": 10, "valeur": "Inconnu"})
        
    # Proportion de locataires (15 pts) - indique la demande locative
    pts_locataires = 0
    loc_pct = stats_demo.get("locataires_pct")
    if loc_pct is not None:
        if loc_pct >= 55:
            pts_locataires = 15
        elif loc_pct >= 35:
            pts_locataires = 12
        elif loc_pct >= 20:
            pts_locataires = 8
        elif loc_pct >= 10:
            pts_locataires = 5
        else:
            pts_locataires = 0
        details.append({"critere": "Proportion locataires", "points": pts_locataires, "max": 15, "valeur": f"{loc_pct}%"})
    else:
        details.append({"critere": "Proportion locataires", "points": 0, "max": 15, "valeur": "Inconnu"})

    # Croissance de la population (8 pts)
    pts_croissance = 0
    croissance = stats_demo.get("croissance_pop")
    if croissance is not None:
        if croissance >= 5.0: pts_croissance = 8
        elif croissance >= 2.0: pts_croissance = 6
        elif croissance >= 0.0: pts_croissance = 4
        elif croissance >= -2.0: pts_croissance = 2
        else: pts_croissance = 0
        details.append({"critere": "Croissance population", "points": pts_croissance, "max": 8, "valeur": f"{croissance}%"})
    else:
        details.append({"critere": "Croissance population", "points": 0, "max": 8, "valeur": "Inconnu"})

    points += pts_revenu + pts_locataires + pts_croissance

    # 3. Proximité grand centre (10 points)
    pts_ville = 0
    top_villes = None
    if lat and lon:
        grandes_villes = {
            "Montréal": (45.5017, -73.5673),
            "Québec": (46.8139, -71.2080),
            "Laval": (45.5828, -73.7561),
            "Gatineau": (45.4287, -75.7134),
            "Longueuil": (45.5306, -73.5136),
            "Sherbrooke": (45.4010, -71.8991),
            "Lévis": (46.8021, -71.1753),
            "Saguenay": (48.4275, -71.0635),
            "Trois-Rivières": (46.3432, -72.5426),
            "Terrebonne": (45.6922, -73.6335),
            "Saint-Jean-sur-Richelieu": (45.3056, -73.2533),
            "Repentigny": (45.7408, -73.4497),
            "Brossard": (45.4601, -73.4526),
            "Drummondville": (45.8812, -72.4862),
            "Saint-Jérôme": (45.7729, -74.0016),
            "Granby": (45.4000, -72.7333),
            "Saint-Hyacinthe": (45.6262, -72.9567),
            "Rimouski": (48.4488, -68.5239),
            "Shawinigan": (46.5667, -72.7500),
            "Joliette": (46.0167, -73.4333),
            "Victoriaville": (46.0500, -71.9667),
            "Saint-Georges": (46.1219, -70.6700),
            "Rouyn-Noranda": (48.2333, -79.0167),
            "Salaberry-de-Valleyfield": (45.2500, -74.1333)
        }
        
        distances = []
        for ville, (v_lat, v_lon) in grandes_villes.items():
            dist = _haversine(lat, lon, v_lat, v_lon)
            distances.append((ville, dist))
        
        # Trouver les 3 villes les plus proches
        distances.sort(key=lambda x: x[1])
        top_villes = distances[:3]
        
        ville_principale, dist_min = top_villes[0]
        
        if dist_min <= 15: pts_ville = 10
        elif dist_min <= 30: pts_ville = 8
        elif dist_min <= 50: pts_ville = 5
        elif dist_min <= 80: pts_ville = 2
        else: pts_ville = 0
        
        villes_str = " / ".join([f"{v} ({d} km)" for v, d in top_villes])
        details.append({"critere": f"Proximité centres ({ville_principale})", "points": pts_ville, "max": 10, "valeur": villes_str})
    else:
        details.append({"critere": "Proximité centres économiques", "points": 0, "max": 10, "valeur": "N/A"})
        
    points += pts_ville
    score_total = round((points / max_points) * 100, 1) if max_points else 0

    # 3. Résumé
    if score_total >= 80:
        resume = "🌟 **Score Exceptionnel** : L'emplacement offre un accès rapide à tous les services clés et la démographie locale soutient une très forte demande locative. Risque de vacance très faible."
    elif score_total >= 60:
        resume = "🟢 **Très Bon Score** : Le secteur est attractif. Les services de base sont facilement accessibles et le marché locatif y est sain."
    elif score_total >= 40:
        resume = "🟡 **Score Moyen** : L'emplacement est correct mais présente des vulnérabilités (ex: services éloignés ou faible demande locative). Un véhicule sera probablement nécessaire pour les locataires."
    else:
        resume = "🔴 **Score Faible** : Zone peu dynamique ou isolée. Le profil démographique et le manque de services de proximité augmentent le risque locatif."

    return {
        "score_total": score_total,
        "max_score": 100,
        "details": details,
        "resume": resume,
        "top_villes": top_villes
    }
