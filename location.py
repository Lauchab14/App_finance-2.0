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


def calculer_score_localisation_avance(trajets: dict, stats_demo: dict) -> dict:
    """
    Calcule un score sur 100 basé sur les temps de transport ORS (60 pts) 
    et le profil démographique (40 pts).
    """
    points = 0
    max_points = 100
    details = []
    
    # 1. Analyse des trajets (60 points)
    # Attribution: 12 pts max par service (5 services = 60 pts)
    bareme_trajet = {
        "epicerie": 12,
        "ecole": 12,
        "pharmacie": 12,
        "bus": 12,
        "parc": 12
    }
    
    score_trajets = 0
    for service, max_pts in bareme_trajet.items():
        trajet_info = trajets.get(service)
        if trajet_info and trajet_info.get("temps_min"):
            t = trajet_info["temps_min"]
            if t <= 3: pts = max_pts
            elif t <= 5: pts = max_pts * 0.8
            elif t <= 10: pts = max_pts * 0.5
            elif t <= 15: pts = max_pts * 0.2
            else: pts = 0
            
            score_trajets += pts
            details.append({"critere": f"Proximité {service}", "points": round(pts, 1), "max": max_pts, "valeur": f"{t} min"})
        else:
            details.append({"critere": f"Proximité {service}", "points": 0, "max": max_pts, "valeur": "Non trouvé / Inconnu"})
            
    points += score_trajets
    
    # 2. Analyse démographique (40 points)
    # Revenu médian (15 pts)
    pts_revenu = 0
    rev = stats_demo.get("revenu_median")
    if rev:
        if rev > 90000: pts_revenu = 15
        elif rev > 75000: pts_revenu = 12
        elif rev > 60000: pts_revenu = 8
        elif rev > 45000: pts_revenu = 4
        else: pts_revenu = 0
        details.append({"critere": "Revenu médian", "points": pts_revenu, "max": 15, "valeur": f"{rev:,.0f} $".replace(',', ' ')})
    else:
        details.append({"critere": "Revenu médian", "points": 0, "max": 15, "valeur": "Inconnu"})
        
    # Proportion de locataires (15 pts) - indique la demande locative
    pts_locataires = 0
    loc_pct = stats_demo.get("locataires_pct")
    if loc_pct is not None:
        if loc_pct >= 60: pts_locataires = 15
        elif loc_pct >= 40: pts_locataires = 12
        elif loc_pct >= 25: pts_locataires = 8
        elif loc_pct >= 10: pts_locataires = 4
        else: pts_locataires = 0
        details.append({"critere": "Proportion locataires", "points": pts_locataires, "max": 15, "valeur": f"{loc_pct}%"})
    else:
        details.append({"critere": "Proportion locataires", "points": 0, "max": 15, "valeur": "Inconnu"})

    # Croissance de la population (10 pts)
    pts_croissance = 0
    croissance = stats_demo.get("croissance_pop")
    if croissance is not None:
        if croissance >= 5.0: pts_croissance = 10
        elif croissance >= 2.0: pts_croissance = 8
        elif croissance >= 0.0: pts_croissance = 5
        elif croissance >= -2.0: pts_croissance = 2
        else: pts_croissance = 0
        details.append({"critere": "Croissance population", "points": pts_croissance, "max": 10, "valeur": f"{croissance}%"})
    else:
        details.append({"critere": "Croissance population", "points": 0, "max": 10, "valeur": "Inconnu"})

    points += pts_revenu + pts_locataires + pts_croissance
    points = round(points, 1)

    # 3. Résumé
    if points >= 80:
        resume = "🌟 **Score Exceptionnel** : L'emplacement offre un accès rapide à tous les services clés et la démographie locale soutient une très forte demande locative. Risque de vacance très faible."
    elif points >= 60:
        resume = "🟢 **Très Bon Score** : Le secteur est attractif. Les services de base sont facilement accessibles et le marché locatif y est sain."
    elif points >= 40:
        resume = "🟡 **Score Moyen** : L'emplacement est correct mais présente des vulnérabilités (ex: services éloignés ou faible demande locative). Un véhicule sera probablement nécessaire pour les locataires."
    else:
        resume = "🔴 **Score Faible** : Zone peu dynamique ou isolée. Le profil démographique et le manque de services de proximité augmentent le risque locatif."

    return {
        "score_total": points,
        "max_score": max_points,
        "details": details,
        "resume": resume
    }
