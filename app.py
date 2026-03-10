"""
app.py — Application Streamlit : Analyseur de Rentabilité Immobilière v2.0
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from config import (
    AMORTISSEMENT_DEFAUT,
    MISE_DE_FONDS_PCT_DEFAUT,
    TAUX_INTERET_DEFAUT,
    TAUX_VACANCE_DEFAUT,
    INFLATION_DEPENSES_DEFAUT,
    CROISSANCE_LOYERS_DEFAUT,
    APPRECIATION_DEFAUT,
    TAUX_ACTUALISATION_DEFAUT,
    TAUX_MARGINAL_IMPOT_DEFAUT,
    TAUX_MUNICIPAUX,
    FRAIS_NOTAIRE_DEFAUT,
    FRAIS_INSPECTION_DEFAUT,
    FRAIS_EVALUATION_DEFAUT,
    ESTIMATION_ASSURANCE_PCT,
    ESTIMATION_ENTRETIEN_PCT,
    ESTIMATION_TONTE,
    ESTIMATION_DENEIGEMENT,
    ESTIMATION_ELECTRICITE,
    REGIONS,
    CRITERES_LOCALISATION,
    TAUX_SCOLAIRE,
)
from finance import (
    analyser_annee1,
    projeter_10_ans,
    calculer_ratios,
    expliquer_ratio,
    generer_recommandation,
    calculer_taxes_municipales,
    calculer_taxes_scolaires,
)
from location import calculer_score_localisation_avance
from geocoding import verifier_adresse, rechercher_adresses, determiner_region_gps, obtenir_tous_services
from demographie import analyser_demographie
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION DE LA PAGE
# =============================================================================
st.set_page_config(
    page_title="Analyseur de Rentabilité Immobilière",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CSS PERSONNALISÉ
# =============================================================================
st.markdown(
    """
    <style>
    /* Thème sombre premium */
    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1200px;
    }

    /* Carte métrique */
    .metric-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid rgba(99, 110, 250, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .metric-card h3 {
        color: #a0a0b8;
        font-size: 0.85rem;
        margin: 0 0 0.3rem 0;
        font-weight: 400;
    }
    .metric-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
    }
    .metric-card .value.positive { color: #4ade80; }
    .metric-card .value.negative { color: #f87171; }
    .metric-card .value.neutral  { color: #636EFA; }

    /* Ratio card */
    .ratio-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid rgba(99, 110, 250, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .ratio-card .ratio-name {
        color: #c0c0d8;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.2rem;
    }
    .ratio-card .ratio-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .ratio-card .ratio-desc {
        color: #8888a8;
        font-size: 0.78rem;
        margin-bottom: 0.4rem;
        font-style: italic;
    }
    .ratio-card .ratio-interp {
        font-size: 0.85rem;
        padding: 0.5rem 0.7rem;
        border-radius: 8px;
        background: rgba(0,0,0,0.2);
        color: #d0d0e8; /* Fixed CSS for better readability on dark background */
    }

    /* Score localisation */
    .score-badge {
        display: inline-block;
        font-size: 2.4rem;
        font-weight: 800;
        padding: 0.5rem 1.2rem;
        border-radius: 16px;
        margin: 0.5rem 0;
    }
    .score-badge.high   { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 2px solid #4ade80; }
    .score-badge.medium { background: rgba(250, 204, 21, 0.15); color: #facc15; border: 2px solid #facc15; }
    .score-badge.low    { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 2px solid #f87171; }

    /* Titre principal */
    .app-title {
        text-align: center;
        padding: 0.5rem 0 1rem 0;
    }
    .app-title h1 {
        font-size: 1.8rem;
        background: linear-gradient(90deg, #636EFA, #EE553B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .app-title p {
        color: #8888a8;
        font-size: 0.9rem;
        margin: 0.2rem 0 0 0;
    }

    /* Sidebar info box */
    .info-box {
        background: rgba(99, 110, 250, 0.1);
        border: 1px solid rgba(99, 110, 250, 0.3);
        border-radius: 8px;
        padding: 0.7rem;
        font-size: 0.82rem;
        color: #a0a0d0;
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# TITRE
# =============================================================================
st.markdown(
    """
    <div class="app-title">
        <h1>🏠 Analyseur de Rentabilité Immobilière</h1>
        <p>Analyse complète d'un immeuble à revenus — Québec</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# SIDEBAR — HYPOTHÈSES
# =============================================================================
with st.sidebar:
    st.header("⚙️ Hypothèses")

    st.subheader("Hypothèque")
    taux_interet = st.number_input(
        "Taux d'intérêt (%)", min_value=0.0, max_value=15.0,
        value=TAUX_INTERET_DEFAUT, step=0.25, format="%.2f",
    )
    amortissement = st.number_input(
        "Amortissement (années)", min_value=5, max_value=40,
        value=AMORTISSEMENT_DEFAUT, step=5,
    )
    mise_de_fonds_pct = st.number_input(
        "Mise de fonds (%)", min_value=0.0, max_value=100.0,
        value=MISE_DE_FONDS_PCT_DEFAUT, step=5.0, format="%.1f",
    )
    st.markdown(
        '<div class="info-box">💡 <b>APH Select</b> : amortissement jusqu\'à 40 ans '
        "et mise de fonds dès 5%.</div>",
        unsafe_allow_html=True,
    )

    st.divider()
    st.subheader("Projections")
    taux_vacance = st.number_input(
        "Taux de vacance (%)", min_value=0.0, max_value=30.0,
        value=TAUX_VACANCE_DEFAUT, step=1.0, format="%.1f",
    )
    croissance_loyers = st.number_input(
        "Croissance annuelle des loyers (%)", min_value=0.0, max_value=10.0,
        value=CROISSANCE_LOYERS_DEFAUT, step=0.5, format="%.1f",
    )
    inflation_depenses = st.number_input(
        "Inflation annuelle des dépenses (%)", min_value=0.0, max_value=10.0,
        value=INFLATION_DEPENSES_DEFAUT, step=0.5, format="%.1f",
    )
    appreciation = st.number_input(
        "Appréciation annuelle de la valeur (%)", min_value=-5.0, max_value=15.0,
        value=APPRECIATION_DEFAUT, step=0.5, format="%.1f",
    )
    taux_actualisation = st.number_input(
        "Taux d'actualisation – VAN (%)", min_value=1.0, max_value=20.0,
        value=TAUX_ACTUALISATION_DEFAUT, step=0.5, format="%.1f",
    )
    taux_marginal_impot = st.number_input(
        "Taux marginal d'imposition (%)", min_value=0.0, max_value=60.0,
        value=TAUX_MARGINAL_IMPOT_DEFAUT, step=1.0, format="%.1f",
        help="Sert à calculer l'impact de l'impôt sur le rendement. Dépend de vos revenus globaux."
    )

# =============================================================================
# VARIABLES D'ÉTAT SESSIONS (Geocoding)
# =============================================================================
if "sugg_adresses" not in st.session_state:
    st.session_state.sugg_adresses = []
if "adresse_choisie" not in st.session_state:
    st.session_state.adresse_choisie = None
if "notes_auto" not in st.session_state:
    st.session_state.notes_auto = None

# =============================================================================
# SECTION 1 — INFORMATIONS DE L'IMMEUBLE
# =============================================================================
st.header("📋 Informations de l'immeuble")

col1, col2 = st.columns(2)
with col1:
    recherche_adr = st.text_input("Rechercher une adresse au Québec", placeholder="123 rue Exemple, Québec")
    if recherche_adr and len(recherche_adr) > 4:
        st.session_state.sugg_adresses = rechercher_adresses(recherche_adr)
    
    if st.session_state.sugg_adresses:
        options = ["-- Sélectionner --"] + [s["display_name"] for s in st.session_state.sugg_adresses]
        choix = st.selectbox("Suggestions d'adresses", options)
        
        if choix != "-- Sélectionner --":
            # Trouver l'adresse choisie
            for s in st.session_state.sugg_adresses:
                if s["display_name"] == choix:
                    st.session_state.adresse_choisie = s
                    break

    adresse = ""
    ville = "Montréal" # par défaut
    region_auto = None
    
    if st.session_state.adresse_choisie:
        adresse = st.session_state.adresse_choisie["display_name"]
        ville = st.session_state.adresse_choisie.get("ville", "Montréal")
        lat = st.session_state.adresse_choisie["lat"]
        lon = st.session_state.adresse_choisie["lon"]
        region_auto = determiner_region_gps(lat, lon, ville)
        st.success(f"📍 Localisée à {ville} ({region_auto.split('(')[0].strip()})")

    st.text_input("Adresse confirmée", value=adresse, disabled=True)

    # Assigner la ville pour la taxation
    ville_taxe = "Autre (entrer manuellement)"
    for v in TAUX_MUNICIPAUX.keys():
        if v.lower() in ville.lower():
            ville_taxe = v
            break
            
    ville_sel = st.selectbox("Ville pour taxation", options=list(TAUX_MUNICIPAUX.keys()), index=list(TAUX_MUNICIPAUX.keys()).index(ville_taxe))

    if ville_sel == "Autre (entrer manuellement)":
        taux_municipal = st.number_input(
            "Taux de taxation municipal (par 100$)", min_value=0.0,
            max_value=3.0, value=0.80, step=0.01, format="%.4f",
        )
    else:
        taux_municipal = TAUX_MUNICIPAUX[ville_sel]
        st.info(f"Taux municipal : **{taux_municipal:.4f}$ / 100$**")

with col2:
    prix_achat = st.number_input(
        "Prix d'achat ($)", min_value=0, value=500_000, step=5_000, format="%d",
    )
    evaluation_municipale = st.number_input(
        "Évaluation municipale ($)", min_value=0, value=400_000, step=5_000, format="%d",
    )
    nb_logements = st.number_input(
        "Nombre de logements", min_value=1, max_value=50, value=4, step=1,
    )

# --- LOYERS : Total ou Détaillé ---
st.subheader("💰 Revenus de loyers")
col_l1, col_l2 = st.columns(2)
with col_l1:
    mode_loyer = st.radio(
        "Mode de saisie des loyers",
        options=["Total", "Détaillé par logement"],
        horizontal=True,
    )
with col_l2:
    frequence_loyer = st.radio(
        "Fréquence des montants",
        options=["Mensuel", "Annuel"],
        horizontal=True,
    )

mult_freq = 1 if frequence_loyer == "Mensuel" else (1/12)

if mode_loyer == "Total":
    label_total = "Loyer total annuel ($)" if frequence_loyer == "Annuel" else "Loyer total mensuel ($)"
    loyers_saisis = st.number_input(
        label_total, min_value=0, value=3_600 if frequence_loyer == "Mensuel" else 43_200, step=100, format="%d",
    )
    loyers_mensuels_total = loyers_saisis * mult_freq
    loyers_details = None
else:
    label_det = "annuel" if frequence_loyer == "Annuel" else "mensuel"
    st.caption(f"Entrez le loyer {label_det} de chaque logement :")
    cols = st.columns(min(nb_logements, 4))
    loyers_details = []
    for i in range(nb_logements):
        with cols[i % len(cols)]:
            loyer_i = st.number_input(
                f"Logement {i + 1} ($)", min_value=0, value=900 if frequence_loyer == "Mensuel" else 10_800, step=50,
                format="%d", key=f"loyer_{i}",
            )
            loyers_details.append(loyer_i)
    loyers_mensuels_total = sum(loyers_details) * mult_freq
    st.success(f"**Total estimé mensuel : {loyers_mensuels_total:,.0f}$**")

# =============================================================================
# SECTION 2 — TAXES (Saisie Manuelle ou Automatique)
# =============================================================================
st.header("🏛️ Taxes (annuelles)")
taxes_mode = st.radio("Mode de saisie des taxes", ["Automatique (selon évaluation)", "Saisie manuelle"], horizontal=True)

taxes_muni_auto = calculer_taxes_municipales(evaluation_municipale, taux_municipal)
taxes_scol_auto = calculer_taxes_scolaires(evaluation_municipale)

col_t1, col_t2 = st.columns(2)
with col_t1:
    taxes_municipales_man = st.number_input(
        "Taxes municipales ($)", min_value=0.0, value=float(taxes_muni_auto),
        step=100.0, format="%.2f", disabled=(taxes_mode == "Automatique (selon évaluation)")
    )
with col_t2:
    taxes_scolaires_man = st.number_input(
        "Taxes scolaires ($)", min_value=0.0, value=float(taxes_scol_auto),
        step=50.0, format="%.2f", disabled=(taxes_mode == "Automatique (selon évaluation)")
    )

if taxes_mode == "Automatique (selon évaluation)":
    taxes_municipales_finales = taxes_muni_auto
    taxes_scolaires_finales = taxes_scol_auto
else:
    taxes_municipales_finales = taxes_municipales_man
    taxes_scolaires_finales = taxes_scolaires_man

# =============================================================================
# SECTION 3 — DÉPENSES
# =============================================================================
st.header("📊 Dépenses annuelles (opérationnelles)")

# Estimations par défaut basées sur le prix
est_ass = max(1000, int(prix_achat * ESTIMATION_ASSURANCE_PCT))
est_ent_autre = max(1000, int(prix_achat * ESTIMATION_ENTRETIEN_PCT))
est_tonte = ESTIMATION_TONTE
est_deneige = ESTIMATION_DENEIGEMENT
est_elec = ESTIMATION_ELECTRICITE

col_d1, col_d2, col_d3 = st.columns(3)
with col_d1:
    assurance = st.number_input("Assurance ($)", min_value=0, value=est_ass, step=100, format="%d")
    electricite = st.number_input("Électricité ($)", min_value=0, value=est_elec, step=100, format="%d", help="Chauffage, communs. Souvent 0 si payé par locataires.")
with col_d2:
    tonte = st.number_input("Tonte de pelouse ($)", min_value=0, value=est_tonte, step=50, format="%d")
    deneigement = st.number_input("Déneigement ($)", min_value=0, value=est_deneige, step=50, format="%d")
with col_d3:
    entretien_autre = st.number_input("Autre entretien/réparations ($)", min_value=0, value=est_ent_autre, step=100, format="%d")
    gestion = st.number_input("Frais de gestion ($)", min_value=0, value=0, step=100, format="%d")

autres_depenses = st.number_input("Autres dépenses (ex: permis, concierge) ($)", min_value=0, value=200, step=100, format="%d")

# =============================================================================
# SECTION 4 — FRAIS D'ACQUISITION
# =============================================================================
st.header("🏷️ Frais d'acquisition (année 1 non récurrents)")
col_f1, col_f2, col_f3 = st.columns(3)

with col_f1:
    frais_notaire = st.number_input(
        "Notaire ($)", min_value=0, value=FRAIS_NOTAIRE_DEFAUT, step=100, format="%d",
    )
with col_f2:
    frais_inspection = st.number_input(
        "Inspection ($)", min_value=0, value=FRAIS_INSPECTION_DEFAUT, step=100, format="%d",
    )
with col_f3:
    frais_evaluation = st.number_input(
        "Évaluation ($)", min_value=0, value=FRAIS_EVALUATION_DEFAUT, step=100, format="%d",
    )

# =============================================================================
# CALCULS
# =============================================================================
resultats = analyser_annee1(
    prix_achat=prix_achat,
    evaluation_municipale=evaluation_municipale,
    taux_municipal_par_100=taux_municipal,
    ville=ville_sel,
    loyers_mensuels_total=loyers_mensuels_total,
    taux_vacance=taux_vacance,
    assurance=assurance,
    entretien_autre=entretien_autre,
    tonte=tonte,
    deneigement=deneigement,
    electricite=electricite,
    gestion=gestion,
    autres_depenses=autres_depenses,
    taux_interet=taux_interet,
    amortissement=amortissement,
    mise_de_fonds_pct=mise_de_fonds_pct,
    frais_notaire=frais_notaire,
    frais_inspection=frais_inspection,
    frais_evaluation=frais_evaluation,
)

# Remplacement des taxes auto par les taxes finales (auto ou manuel)
resultats["taxes_municipales"] = taxes_municipales_finales
resultats["taxes_scolaires"] = taxes_scolaires_finales
resultats["depenses_totales"] = (taxes_municipales_finales + taxes_scolaires_finales + assurance + entretien_autre + tonte + deneigement + electricite + gestion + autres_depenses)
resultats["rne"] = resultats["revenus_nets"] - resultats["depenses_totales"]
resultats["cashflow_avant_frais"] = resultats["rne"] - resultats["paiement_annuel"]
resultats["cashflow_net_annee1"] = resultats["cashflow_avant_frais"] - resultats["frais_acquisition"]

projection = projeter_10_ans(
    prix_achat=prix_achat,
    montant_pret=resultats["montant_pret"],
    paiement_mensuel=resultats["paiement_mensuel"],
    revenus_nets_an1=resultats["revenus_nets"],
    depenses_an1=resultats["depenses_totales"],
    frais_acquisition=resultats["frais_acquisition"],
    mise_de_fonds=resultats["mise_de_fonds"],
    taux_interet=taux_interet,
    croissance_loyers=croissance_loyers,
    inflation_depenses=inflation_depenses,
    appreciation=appreciation,
    taux_marginal_impot=taux_marginal_impot,
)

mise_de_fonds_totale = resultats["mise_de_fonds"] + resultats["frais_acquisition"]
ratios = calculer_ratios(
    prix_achat=prix_achat,
    rne=resultats["rne"],
    cashflow_annee1=resultats["cashflow_avant_frais"],  # Cashflow opérationnel pour le Cash-on-cash
    mise_de_fonds_totale=mise_de_fonds_totale,
    revenus_bruts=resultats["revenus_bruts_annuels"],
    paiement_annuel=resultats["paiement_annuel"],
    cashflows_irr=projection["cashflows_irr"],
    taux_actualisation=taux_actualisation,
)

# =============================================================================
# ONGLETS D'ANALYSE
# =============================================================================
st.divider()
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Analyse Année 1", "📊 Projection 10 ans", "📍 Localisation", "🎯 Ratios & Recommandation"]
)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — ANALYSE ANNÉE 1
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("Résumé financier — Année 1")

    # Métriques clés
    m1, m2, m3, m4 = st.columns(4)

    def metric_html(titre, valeur, classe="neutral"):
        return (
            f'<div class="metric-card"><h3>{titre}</h3>'
            f'<p class="value {classe}">{valeur}</p></div>'
        )

    with m1:
        st.markdown(metric_html("Mise de fonds", f"{resultats['mise_de_fonds']:,.0f}$"), unsafe_allow_html=True)
    with m2:
        st.markdown(metric_html("Paiement mensuel", f"{resultats['paiement_mensuel']:,.0f}$"), unsafe_allow_html=True)
    with m3:
        cf_class = "positive" if resultats["cashflow_avant_frais"] >= 0 else "negative"
        st.markdown(metric_html("Cashflow annuel", f"{resultats['cashflow_avant_frais']:,.0f}$", cf_class), unsafe_allow_html=True)
    with m4:
        cf_class = "positive" if resultats["cashflow_avant_frais"] / 12 >= 0 else "negative"
        st.markdown(metric_html("Cashflow mensuel", f"{resultats['cashflow_avant_frais'] / 12:,.0f}$", cf_class), unsafe_allow_html=True)

    st.divider()

    col_rev, col_dep, col_non_rec = st.columns(3)

    with col_rev:
        st.subheader("🟩 Revenus")
        st.write(f"Loyers bruts marginaux : **{resultats['revenus_bruts_annuels']:,.0f}$**")
        st.write(f"- Vacance ({taux_vacance:.1f}%) : **-{resultats['revenus_bruts_annuels'] - resultats['revenus_nets']:,.0f}$**")
        st.divider()
        st.write(f"**Revenus nets : {resultats['revenus_nets']:,.0f}$**")

    with col_dep:
        st.subheader("🟥 Dépenses annuelles")
        st.write(f"Taxes municipales : **{resultats['taxes_municipales']:,.0f}$**")
        st.write(f"Taxes scolaires : **{resultats['taxes_scolaires']:,.0f}$**")
        st.write(f"Assurance : **{assurance:,.0f}$**")
        if electricite > 0:
            st.write(f"Électricité : **{electricite:,.0f}$**")
        st.write(f"Tonte : **{tonte:,.0f}$**")
        st.write(f"Déneigement : **{deneigement:,.0f}$**")
        st.write(f"Entretien/Réparations : **{entretien_autre:,.0f}$**")
        if gestion > 0:
            st.write(f"Gestion : **{gestion:,.0f}$**")
        if autres_depenses > 0:
            st.write(f"Autres : **{autres_depenses:,.0f}$**")
        st.divider()
        st.write(f"**Total dépenses OPEX : {resultats['depenses_totales']:,.0f}$**")

    with col_non_rec:
        st.subheader("🟧 Frais Non-Récurrents")
        st.write(f"Droits mutation : **{resultats['droits_mutation']:,.0f}$**")
        st.write(f"Notaire : **{frais_notaire:,.0f}$**")
        st.write(f"Inspection : **{frais_inspection:,.0f}$**")
        st.write(f"Évaluation : **{frais_evaluation:,.0f}$**")
        st.divider()
        st.write(f"**Total Acquisition : {resultats['frais_acquisition']:,.0f}$**")

    # Graphique donut des dépenses
    st.divider()
    st.subheader("Répartition des dépenses annuelles")

    dep_labels = ["Taxes munic.", "Taxes scol.", "Assurance", "Tonte", "Déneigement", "Entretien", "Hypothèque (intérêts)"]
    dep_values = [
        resultats["taxes_municipales"],
        resultats["taxes_scolaires"],
        assurance,
        tonte,
        deneigement,
        entretien_autre,
        resultats["interet_annee1"],
    ]
    if electricite > 0:
        dep_labels.append("Électricité")
        dep_values.append(electricite)
    if gestion > 0:
        dep_labels.append("Gestion")
        dep_values.append(gestion)
    if autres_depenses > 0:
        dep_labels.append("Autres")
        dep_values.append(autres_depenses)

    fig_donut = go.Figure(
        data=[
            go.Pie(
                labels=dep_labels,
                values=dep_values,
                hole=0.5,
                textinfo="label+percent",
                marker=dict(
                    colors=px.colors.qualitative.Set2[: len(dep_labels)]
                ),
            )
        ]
    )
    fig_donut.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        height=400,
        showlegend=False,
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

    # Frais d'acquisition
    st.divider()
    st.subheader("Frais d'acquisition (non récurrents)")
    fa1, fa2, fa3, fa4, fa5 = st.columns(5)
    with fa1:
        st.metric("Droits de mutation", f"{resultats['droits_mutation']:,.0f}$")
    with fa2:
        st.metric("Notaire", f"{frais_notaire:,.0f}$")
    with fa3:
        st.metric("Inspection", f"{frais_inspection:,.0f}$")
    with fa4:
        st.metric("Évaluation", f"{frais_evaluation:,.0f}$")
    with fa5:
        st.metric("**Total**", f"{resultats['frais_acquisition']:,.0f}$")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — PROJECTION 10 ANS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Projection sur 10 ans")

    df_proj = pd.DataFrame(projection["annees"])

    # Tableau avec style Streamlit (background color rendering is clearer)
    df_affichage = df_proj.copy()
    df_affichage.columns = [
        "Année", "Revenus nets", "Dépenses", "RNE", "Frais Non Rec.", "Hypothèque",
        "Intérêts", "Capital", "Cashflow Av. Impôt", "Rev. Imposable", "Impôt", "Cashflow Net", "Cashflow cumulé",
        "Valeur immeuble", "Solde prêt", "Équité",
    ]
    colonnes_dollars = df_affichage.columns[1:]
    for col in colonnes_dollars:
        df_affichage[col] = df_affichage[col].apply(lambda x: f"{x:,.0f} $")

    def color_cashflow(val):
        """Couleur pour le texte des colonnes Cashflow"""
        if isinstance(val, str) and "$" in val:
            clean_val = val.replace(" ", "").replace("$", "").replace(",", "")
            try:
                numeric_val = float(clean_val)
                if numeric_val > 0:
                    return 'color: #4ade80' # Vert
                elif numeric_val < 0:
                    return 'color: #f87171' # Rouge
            except:
                pass
        return ''

    styled_df = df_affichage.style.applymap(color_cashflow, subset=['Cashflow Av. Impôt', 'Cashflow Net'])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.divider()

    # Graphiques
    g1, g2 = st.columns(2)

    with g1:
        fig_cf = go.Figure()
        fig_cf.add_trace(
            go.Bar(
                x=df_proj["annee"],
                y=df_proj["cashflow_apres_impot"],
                name="Cashflow annuel net (après impôt)",
                marker_color=["#4ade80" if v >= 0 else "#f87171" for v in df_proj["cashflow_apres_impot"]],
            )
        )
        fig_cf.add_trace(
            go.Scatter(
                x=df_proj["annee"],
                y=df_proj["cashflow_cumule"],
                name="Cumulé",
                line=dict(color="#636EFA", width=3),
            )
        )
        fig_cf.update_layout(
            title="Cashflow annuel et cumulé",
            xaxis_title="Année",
            yaxis_title="$",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_cf, use_container_width=True)

    with g2:
        fig_val = go.Figure()
        fig_val.add_trace(
            go.Scatter(
                x=df_proj["annee"],
                y=df_proj["valeur_immeuble"],
                name="Valeur",
                line=dict(color="#636EFA", width=3),
                fill="tozeroy",
                fillcolor="rgba(99, 110, 250, 0.1)",
            )
        )
        fig_val.add_trace(
            go.Scatter(
                x=df_proj["annee"],
                y=df_proj["solde_pret"],
                name="Solde prêt",
                line=dict(color="#EE553B", width=3),
            )
        )
        fig_val.add_trace(
            go.Scatter(
                x=df_proj["annee"],
                y=df_proj["equite"],
                name="Équité",
                line=dict(color="#4ade80", width=3, dash="dash"),
            )
        )
        fig_val.update_layout(
            title="Valeur, prêt et équité",
            xaxis_title="Année",
            yaxis_title="$",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig_val, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — LOCALISATION
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("📍 Analyse de localisation détaillée")

    if "adresse_choisie" in st.session_state and st.session_state.adresse_choisie:
        _lat = st.session_state.adresse_choisie["lat"]
        _lon = st.session_state.adresse_choisie["lon"]
        _adresse = st.session_state.adresse_choisie.get("display_name", "")
        _region = determiner_region_gps(_lat, _lon, st.session_state.adresse_choisie.get("ville", "Inconnu"))
        
        

        if st.button("🚀 Lancer l'Analyse Avancée (Services & Démographie)", type="primary"):
            with st.spinner("Analyse de l'emplacement en cours (peut prendre 10-20 secondes)..."):
                
                # 1. Carte interactive
                df_map = pd.DataFrame({'lat': [_lat], 'lon': [_lon]})
                st.map(df_map, zoom=14, use_container_width=True)

                # 2. Tous les services dans un rayon de 5 km
                st.info("Recherche de TOUS les services à proximité (OpenStreetMap)...")
                tous_services = obtenir_tous_services(_lat, _lon, rayon=5000)
                
                # 3. Démographie locale
                st.info("Analyse démographique locale (topologie des bâtiments)...")
                stats_demo = analyser_demographie(_lat, _lon, _region)

                # 4. Score global (utilise le service le plus proche de chaque catégorie)
                trajets_proches = {}
                for cat, liste in tous_services.items():
                    if liste:
                        trajets_proches[cat] = {
                            "distance_km": liste[0]["distance_km"],
                            "temps_min": liste[0]["temps_min"]
                        }
                    else:
                        trajets_proches[cat] = None
                
                resultat_score = calculer_score_localisation_avance(trajets_proches, stats_demo)

                st.markdown("---")
                
                # --- SCORE ---
                score_total = resultat_score['score_total']
                if score_total >= 80: badge_class = "high"
                elif score_total >= 60: badge_class = "medium"
                else: badge_class = "low"
                
                st.markdown(
                    f'<div style="text-align:center;">'
                    f'<p style="color:#8888a8;margin-bottom:0;">Score d\'Attractivité Locative</p>'
                    f'<div class="score-badge {badge_class}">{score_total}/100</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"> {resultat_score['resume']}")
                
                st.divider()
                
                # --- DÉMOGRAPHIE ---
                st.markdown("### 🏘️ Synthèse Démographique")
                col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns(5)
                
                with col_d1:
                    val_pop = stats_demo.get('population')
                    st.metric("Population", f"{val_pop:,}".replace(',', ' ') if val_pop else "N/D")
                with col_d2:
                    val_age = stats_demo.get('age_median')
                    st.metric("Âge Médian", f"{val_age} ans" if val_age else "N/D")
                with col_d3:
                    val_loc = stats_demo.get('locataires_pct')
                    st.metric("Locataires", f"{val_loc}%" if val_loc else "N/D")
                with col_d4:
                    val_rev = stats_demo.get('revenu_median')
                    st.metric("Revenu Médian", f"{val_rev:,} $".replace(',', ' ') if val_rev else "N/D")
                with col_d5:
                    val_croissance = stats_demo.get('croissance_pop')
                    delta_color = "normal"
                    st.metric("Croissance (5 ans)", f"{val_croissance}%" if val_croissance is not None else "N/D",
                             delta=f"{val_croissance}%" if val_croissance is not None else None)
                    
                ville_a = stats_demo.get('ville_analyse', '')
                st.caption(f"📊 _{stats_demo.get('source', '')}_")

                st.divider()
                
                # --- TOUS LES SERVICES ---
                st.markdown("### 📍 Services à Proximité (Rayon de 5 km)")
                
                titres_cat = {
                    "epicerie": "🛒 Épiceries & Supermarchés",
                    "ecole": "🏫 Écoles & Institutions",
                    "pharmacie": "💊 Pharmacies",
                    "bus": "🚌 Transport en Commun",
                    "parc": "🌳 Parcs & Loisirs"
                }
                
                for cat_key, cat_titre in titres_cat.items():
                    liste = tous_services.get(cat_key, [])
                    nb = len(liste)
                    
                    with st.expander(f"{cat_titre} ({nb} trouvé{'s' if nb > 1 else ''})", expanded=(nb > 0)):
                        if liste:
                            rows = []
                            for s in liste:
                                rows.append({
                                    "Nom": s['nom'],
                                    "Distance": f"{s['distance_km']} km",
                                    "Temps estimé": f"~{s['temps_min']} min"
                                })
                            st.table(pd.DataFrame(rows))
                        else:
                            st.write("Aucun trouvé dans un rayon de 5 km.")
                
                with st.expander("Voir le détail des points (Score / 100)"):
                    st.dataframe(pd.DataFrame(resultat_score['details']), use_container_width=True)

    else:
        st.info("Veuillez sélectionner et confirmer une adresse dans la section 'Informations de l'immeuble' pour lancer l'analyse de localisation.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — RATIOS & RECOMMANDATION
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("🎯 Ratios financiers")

    ratio_keys = [
        ("cap_rate", "%"),
        ("cash_on_cash", "%"),
        ("mrb", "x"),
        ("csd", "x"),
        ("tri", "%"),
        ("van", "$"),
    ]

    # Afficher en grille 2×3
    for row_start in range(0, len(ratio_keys), 2):
        cols = st.columns(2)
        for j, (cle, unite) in enumerate(ratio_keys[row_start : row_start + 2]):
            valeur = ratios.get(cle)
            if valeur is None:
                valeur_str = "N/A"
                color = "#8888a8"
            else:
                if unite == "$":
                    valeur_str = f"{valeur:,.0f}$"
                elif unite == "x":
                    valeur_str = f"{valeur:.2f}x"
                else:
                    valeur_str = f"{valeur:.2f}%"

                # Couleur basée sur l'interprétation
                explication = expliquer_ratio(cle, valeur)
                interp = explication["interpretation"]
                if "🟢" in interp:
                    color = "#4ade80"
                elif "🟡" in interp:
                    color = "#facc15"
                else:
                    color = "#f87171"

            explication = expliquer_ratio(cle, valeur if valeur is not None else 0)

            with cols[j]:
                st.markdown(
                    f'<div class="ratio-card">'
                    f'<div class="ratio-name">{explication["nom"]}</div>'
                    f'<div class="ratio-value" style="color:{color};">{valeur_str}</div>'
                    f'<div class="ratio-desc">{explication["description"]}</div>'
                    f'<div class="ratio-interp">{explication["interpretation"]}</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # Délai de récupération
    delai = ratios.get("delai_recuperation")
    if delai:
        st.info(f"⏱️ **Délai de récupération de la mise de fonds** : {delai} ans")
    else:
        st.warning("⏱️ La mise de fonds n'est pas récupérée dans les 10 ans par le cashflow seul.")

    # Recommandation
    st.divider()
    st.subheader("📝 Recommandation")
    recommandation = generer_recommandation(ratios, prix_achat)
    st.markdown(recommandation)

    # Résumé des loyers si détaillé
    if loyers_details:
        st.divider()
        st.subheader("🏘️ Détail des loyers")
        
        freq_label = "Loyer mensuel" if frequence_loyer == "Mensuel" else "Loyer annuel"
        _total = loyers_mensuels_total if frequence_loyer == "Mensuel" else (loyers_mensuels_total * 12)

        df_loyers = pd.DataFrame(
            {
                "Logement": [f"Logement {i+1}" for i in range(len(loyers_details))],
                freq_label: [f"{l:,.0f}$" for l in loyers_details],
            }
        )
        df_loyers.loc[len(df_loyers)] = ["**TOTAL**", f"**{_total:,.0f}$**"]
        st.dataframe(df_loyers, use_container_width=True, hide_index=True)
