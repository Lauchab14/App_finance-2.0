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
