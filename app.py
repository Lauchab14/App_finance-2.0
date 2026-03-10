"""
app.py — Application Streamlit : Analyseur de Rentabilité Immobilière v2.0
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium

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
from geocoding import verifier_adresse, rechercher_adresses, determiner_region_gps, obtenir_tous_services, obtenir_loisirs_ville
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
    /* =========================================
       THÈME IMVEST - Dashboard Clair
       Primaire : #002A54 (Bleu Marine)
       Secondaire : #005A9C (Bleu Moyen)
       Accent : #FFC000 (Or)
       Fond : #F4F6F9 (Gris très clair)
       Texte : #1E293B (Gris anthracite)
       Cartes : #FFFFFF (Blanc)
       ========================================= */

    /* Forcer le thème clair sur l'application entière */
    .stApp {
        background-color: #F4F6F9;
        color: #1E293B;
    }

    .main .block-container {
        padding-top: 0rem !important;
        max-width: 1200px;
    }

    /* Annuler totalement le padding par défaut de Streamlit */
    div[data-testid="stAppViewBlockContainer"] {
        padding-top: 0.5rem !important; 
    }

    /* Cacher le header natif de Streamlit (la barre blanche avec le bouton "Deploy") qui prend de la place pour rien */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Carte métrique */
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        margin-bottom: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }
    .metric-card h3 {
        color: #64748B;
        font-size: 0.85rem;
        margin: 0 0 0.3rem 0;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .metric-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        color: #002A54; /* Bleu Marine IMVEST */
    }
    .metric-card .value.positive { color: #16A34A; } /* Vert plus lisible sur fond blanc */
    .metric-card .value.negative { color: #DC2626; } /* Rouge plus lisible sur fond blanc */
    .metric-card .value.neutral  { color: #005A9C; } /* Bleu moyen IMVEST */

    /* Ratio card */
    .ratio-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border-left: 4px solid #FFC000; /* Accent Or IMVEST */
    }
    .ratio-card .ratio-name {
        color: #475569;
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .ratio-card .ratio-value {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        color: #002A54;
    }
    .ratio-card .ratio-desc {
        color: #64748B;
        font-size: 0.78rem;
        margin-bottom: 0.6rem;
        font-style: italic;
    }
    .ratio-card .ratio-interp {
        font-size: 0.85rem;
        padding: 0.5rem 0.7rem;
        border-radius: 6px;
        background: #F1F5F9;
        color: #334155;
        border-left: 3px solid #005A9C;
    }

    /* Score localisation */
    .score-badge {
        display: inline-block;
        font-size: 2.6rem;
        font-weight: 800;
        padding: 0.6rem 1.4rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .score-badge.high   { background: #F0FDF4; color: #15803D; border: 2px solid #86EFAC; }
    .score-badge.medium { background: #FEFCE8; color: #A16207; border: 2px solid #FDE047; }
    .score-badge.low    { background: #FEF2F2; color: #B91C1C; border: 2px solid #FCA5A5; }

    /* Titre principal */
    .app-title {
        text-align: center;
        padding: 0.5rem 0 1.5rem 0;
    }
    .app-title h1 {
        font-size: 2.2rem;
        color: #002A54;
        margin: 0;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .app-title p {
        color: #64748B;
        font-size: 1rem;
        margin: 0.3rem 0 0 0;
        font-weight: 500;
    }

    /* Sidebar info box */
    .info-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        border-left: 3px solid #005A9C;
    }
    .info-box div {
        color: #475569 !important;
    }

    /* Forcer le style des labels Streamlit (gris foncé au lieu de gris clair) */
    .st-emotion-cache-10trblm, label {
        color: #334155 !important;
        font-weight: 600 !important;
    }
    /* =========================================
       BOUTONS
       ========================================= */
    /* Boutons secondaires (Bleu Marine) */
    .stButton > button {
        background-color: #002A54 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background-color: #004080 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.15) !important;
    }
    /* Bouton Principal (Or) - utiliser type="primary" dans st.button */
    .stButton > button[data-testid="baseButton-primary"] {
        background-color: #FFC000 !important;
        color: #002A54 !important; /* Texte foncé sur or */
    }
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #FFD633 !important;
    }

    /* =========================================
       SIDEBAR
       ========================================= */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important; /* Blanc bleuté très très clair */
        border-right: 1px solid #E2E8F0 !important;
    }

    /* =========================================
       EN-TÊTES DE SECTION CUSTOM
       ========================================= */
    .section-header {
        margin-top: 2rem;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #E2E8F0;
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    .section-header h2 {
        font-size: 1.5rem;
        color: #002A54;
        margin: 0;
        font-weight: 700;
    }
    .section-header .accent-line {
        height: 4px;
        width: 40px;
        background-color: #FFC000;
        border-radius: 2px;
        margin-top: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# HELPERS UI (DASHBOARD IMVEST)
# =============================================================================
def section_header(titre):
    st.markdown(f'''
    <div class="section-header">
        <h2>{titre}</h2>
        <div class="accent-line"></div>
    </div>
    ''', unsafe_allow_html=True)

def custom_subheader(titre):
    st.markdown(f'''
    <div style="margin-top: 1.8rem; margin-bottom: 0.75rem; color: #002A54; font-weight: 700; font-size: 1.25rem; border-bottom: 1px solid #E2E8F0; padding-bottom: 0.4rem;">
        {titre}
    </div>
    ''', unsafe_allow_html=True)

# =============================================================================
# TITRE ET LOGO
# =============================================================================
col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
with col_logo2:
    try:
        st.image("imvest_logo.png", use_container_width=True)
    except FileNotFoundError:
        pass # Fallback silencieux si l'image manque

st.markdown(
    """
    <div class="app-title" style="margin-top: 0.5rem; padding-top: 0;">
        <p>Analyse complète d'un immeuble à revenus — Québec</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# =============================================================================
# SIDEBAR — HYPOTHÈSES
# =============================================================================
with st.sidebar:
    section_header("⚙️ Hypothèses")

    custom_subheader("Hypothèque")
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
    custom_subheader("Projections")
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
if "analyse_locale_auto" not in st.session_state:
    st.session_state.analyse_locale_auto = False
if "derniere_adresse_analysee" not in st.session_state:
    st.session_state.derniere_adresse_analysee = None

# =============================================================================
# SECTION 1 — INFORMATIONS DE L'IMMEUBLE
# =============================================================================
section_header("📋 Informations de l'immeuble")

# ── Bloc adresse — pleine largeur ────────────────────────────────────────────
st.markdown("#### 📍 Adresse de l'immeuble")

# Champ de recherche principal (pleine largeur)
recherche_adr = st.text_input(
    "Rechercher une adresse au Québec",
    placeholder="Commencez à écrire : 123 rue des Érables, Sainte-Marie…",
    key="adr_recherche",
    label_visibility="collapsed",
)
# Déclencher dès 3 caractères
if len(recherche_adr.strip()) >= 3:
    st.session_state.sugg_adresses = rechercher_adresses(recherche_adr.strip())
elif len(recherche_adr.strip()) == 0:
    st.session_state.sugg_adresses = []

# Selectbox de suggestions
if st.session_state.sugg_adresses:
    options_adr = ["-- Sélectionner une adresse --"] + [s["display_name"] for s in st.session_state.sugg_adresses]
    choix_adr = st.selectbox("Adresse sélectionnée", options_adr, key="selectbox_adresse", label_visibility="collapsed")

    if choix_adr != "-- Sélectionner une adresse --":
        for s in st.session_state.sugg_adresses:
            if s["display_name"] == choix_adr:
                if st.session_state.adresse_choisie != s:
                    st.session_state.adresse_choisie = s
                    st.session_state.analyse_locale_auto = True
                    st.session_state.derniere_adresse_analysee = s["display_name"]
                    # Extraire ville et CP depuis les données brutes Nominatim
                    raw_addr = s.get("raw", {}).get("address", {})
                    st.session_state.adr_ville_affich = s.get("ville", raw_addr.get("city", raw_addr.get("town", raw_addr.get("municipality", ""))))
                    st.session_state.adr_cp_affich    = raw_addr.get("postcode", "")
                    st.session_state.adr_rue_affich   = s["display_name"].split(",")[0].strip()
                break



# Carte visuelle de confirmation
adresse = ""
ville    = "Montréal"
region_auto = None
if st.session_state.adresse_choisie:
    adresse = st.session_state.adresse_choisie["display_name"]
    ville   = st.session_state.adresse_choisie.get("ville", "Montréal")
    lat     = st.session_state.adresse_choisie["lat"]
    lon     = st.session_state.adresse_choisie["lon"]
    region_auto = determiner_region_gps(lat, lon, ville)
    st.markdown(
        f"""
        <div style="background:#FFFFFF;
                    border:1px solid #E2E8F0; border-radius:12px;
                    border-left:4px solid #002A54;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                    padding:0.8rem 1.1rem; margin-top:0.4rem; margin-bottom:0.8rem;">
            <div style="font-size:0.75rem;color:#005A9C;margin-bottom:0.15rem; font-weight:700; text-transform:uppercase; letter-spacing:0.02em;">✅ Adresse confirmée</div>
            <div style="font-size:1.1rem;font-weight:800;color:#002A54;">{adresse}</div>
            <div style="font-size:0.85rem;color:#475569;margin-top:0.35rem;">
                📍 {ville} &nbsp;&middot;&nbsp; <span style="color:#D4AF37; font-weight:600;">{region_auto.split('(')[0].strip()}</span>
                &nbsp;&middot;&nbsp; <span style="color:#94A3B8; font-size:0.75rem;">GPS : {lat:.5f}, {lon:.5f}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ── Autres informations (deux colonnes) ──────────────────────────────────────
col1, col2 = st.columns(2, gap="large")
with col1:

    # Taux municipal calculé en arrière-plan selon la ville détectée
    ville_taxe = "Autre (entrer manuellement)"
    for v in TAUX_MUNICIPAUX.keys():
        if v.lower() in ville.lower():
            ville_taxe = v
            break
    taux_municipal = TAUX_MUNICIPAUX.get(ville_taxe, 0.80)


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
custom_subheader("💰 Revenus de loyers")
col_l1, col_l2 = st.columns(2, gap="large")
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
section_header("🏛️ Taxes (annuelles)")
taxes_mode = st.radio("Mode de saisie des taxes", ["Automatique (selon évaluation)", "Saisie manuelle"], horizontal=True)

taxes_muni_auto = calculer_taxes_municipales(evaluation_municipale, taux_municipal)
taxes_scol_auto = calculer_taxes_scolaires(evaluation_municipale)

col_t1, col_t2 = st.columns(2, gap="large")
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
section_header("📊 Dépenses annuelles (opérationnelles)")

# Estimations par défaut basées sur le prix
est_ass = max(1000, int(prix_achat * ESTIMATION_ASSURANCE_PCT))
est_ent_autre = max(1000, int(prix_achat * ESTIMATION_ENTRETIEN_PCT))
est_tonte = ESTIMATION_TONTE
est_deneige = ESTIMATION_DENEIGEMENT
est_elec = ESTIMATION_ELECTRICITE

col_d1, col_d2, col_d3 = st.columns(3, gap="large")
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
section_header("🏷️ Frais d'acquisition (année 1 non récurrents)")
col_f1, col_f2, col_f3 = st.columns(3, gap="large")

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
    ville=ville_taxe,
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
    custom_subheader("Résumé financier — Année 1")

    # Métriques clés
    m1, m2, m3, m4 = st.columns(4, gap="large")

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

    col_rev, col_dep, col_non_rec = st.columns(3, gap="large")

    with col_rev:
        custom_subheader("🟩 Revenus")
        st.write(f"Loyers bruts marginaux : **{resultats['revenus_bruts_annuels']:,.0f}$**")
        st.write(f"- Vacance ({taux_vacance:.1f}%) : **-{resultats['revenus_bruts_annuels'] - resultats['revenus_nets']:,.0f}$**")
        st.divider()
        st.write(f"**Revenus nets : {resultats['revenus_nets']:,.0f}$**")

    with col_dep:
        custom_subheader("🟥 Dépenses annuelles")
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
        custom_subheader("🟧 Frais Non-Récurrents")
        st.write(f"Droits mutation : **{resultats['droits_mutation']:,.0f}$**")
        st.write(f"Notaire : **{frais_notaire:,.0f}$**")
        st.write(f"Inspection : **{frais_inspection:,.0f}$**")
        st.write(f"Évaluation : **{frais_evaluation:,.0f}$**")
        st.divider()
        st.write(f"**Total Acquisition : {resultats['frais_acquisition']:,.0f}$**")

    # Graphique donut des dépenses
    st.divider()
    custom_subheader("Répartition des dépenses annuelles")

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
    custom_subheader("Frais d'acquisition (non récurrents)")
    fa1, fa2, fa3, fa4, fa5 = st.columns(5, gap="large")
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
    custom_subheader("Projection sur 10 ans")

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
    g1, g2 = st.columns(2, gap="large")

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
    custom_subheader("📍 Analyse de localisation détaillée")

    if "adresse_choisie" in st.session_state and st.session_state.adresse_choisie:
        _lat = st.session_state.adresse_choisie["lat"]
        _lon = st.session_state.adresse_choisie["lon"]
        _adresse = st.session_state.adresse_choisie.get("display_name", "")
        _region = determiner_region_gps(_lat, _lon, st.session_state.adresse_choisie.get("ville", "Inconnu"))
        
        

        # Lancement automatique si nouvelle adresse sélectionnée, ou bouton manuel
        _lancer = st.session_state.get("analyse_locale_auto", False)

        col_btn1, col_btn2 = st.columns([3, 1], gap="large")
        with col_btn1:
            if st.button("🔄 Relancer l'analyse", help="Relancer manuellement l'analyse de localisation"):
                _lancer = True
        with col_btn2:
            if _lancer:
                st.markdown(
                    "<div style='padding:0.45rem 0;color:#4ade80;font-size:0.85rem;'>⚡ Analyse automatique…</div>",
                    unsafe_allow_html=True,
                )

        if _lancer:
            st.session_state.analyse_locale_auto = False  # reset du flag
            with st.spinner("Analyse de l'emplacement en cours (peut prendre 10-20 secondes)..."):

                # 1. Services proches (rayon 5 km)
                st.info("Recherche de TOUS les services à proximité (OpenStreetMap)...")
                st.session_state.loc_tous_services = obtenir_tous_services(_lat, _lon, rayon=5000)

                # 2. Loisirs & commodités dans les limites municipales OSM
                _ville_loisirs = st.session_state.adresse_choisie.get("ville", "")
                st.info(f"Comptage des loisirs & commodités ({_ville_loisirs})...")
                st.session_state.loc_loisirs_ville = obtenir_loisirs_ville(_ville_loisirs, _lat, _lon)
                st.session_state.loc_ville_loisirs_nom = _ville_loisirs

                # 3. Démographie locale
                st.info("Analyse démographique locale...")
                st.session_state.loc_stats_demo = analyser_demographie(_lat, _lon, _region)

                # 4. Score de localisation
                trajets_proches = {}
                for cat, liste in st.session_state.loc_tous_services.items():
                    trajets_proches[cat] = {"distance_km": liste[0]["distance_km"], "temps_min": liste[0]["temps_min"]} if liste else None
                st.session_state.loc_score = calculer_score_localisation_avance(trajets_proches, st.session_state.loc_stats_demo, lat=_lat, lon=_lon)

                # 5. Carte Folium
                _config_services_carte = {
                    "epicerie":  {"label": "Epicerie",  "color": "green",     "icon": "shopping-cart"},
                    "ecole":     {"label": "Ecole",     "color": "blue",      "icon": "graduation-cap"},
                    "pharmacie": {"label": "Pharmacie", "color": "purple",    "icon": "plus-square"},
                    "bus":       {"label": "Transport", "color": "orange",    "icon": "bus"},
                    "parc":      {"label": "Parc",      "color": "darkgreen", "icon": "tree"},
                }
                m = folium.Map(location=[_lat, _lon], zoom_start=15, tiles="CartoDB positron")
                folium.Marker(
                    location=[_lat, _lon],
                    popup=folium.Popup(f"<b>Immeuble analysé</b><br>{_adresse}", max_width=300),
                    tooltip="🏠 Immeuble analysé",
                    icon=folium.Icon(color="red", icon="home", prefix="fa"),
                ).add_to(m)
                for cat_key, cfg in _config_services_carte.items():
                    for s in st.session_state.loc_tous_services.get(cat_key, [])[:5]:
                        nom_s = s["nom"] if s["nom"] else cfg["label"]
                        folium.Marker(
                            location=[s["lat"], s["lon"]],
                            popup=folium.Popup(f"<b>{nom_s}</b><br>📍 {s['distance_km']:.2f} km — ⏱ ~{s['temps_min']} min", max_width=250),
                            tooltip=f"{nom_s} ({s['distance_km']:.2f} km)",
                            icon=folium.Icon(color=cfg["color"], icon=cfg["icon"], prefix="fa"),
                        ).add_to(m)
                st.session_state.loc_carte = m

        # ── Affichage des résultats (persistés dans session_state) ──────────
        if "loc_score" in st.session_state:
            tous_services   = st.session_state.loc_tous_services
            loisirs_ville   = st.session_state.loc_loisirs_ville
            _ville_loisirs  = st.session_state.loc_ville_loisirs_nom
            stats_demo      = st.session_state.loc_stats_demo
            resultat_score  = st.session_state.loc_score

            # Carte
            custom_subheader("🗺️ Carte Interactive — Immeuble & Services Proches")
            st.caption("🏠 Rouge : immeuble | 🟢 Vert : épiceries | 🔵 Bleu : écoles | 🟣 Violet : pharmacies | 🟠 Orange : transport | 🌲 Vert foncé : parcs")
            st_folium(st.session_state.loc_carte, use_container_width=True, height=500, returned_objects=[])

            st.markdown("---")

            # Score
            score_total = resultat_score['score_total']
            badge_class = "high" if score_total >= 80 else ("medium" if score_total >= 60 else "low")
            st.markdown(
                f'<div style="text-align:center;">'
                f'<p style="color:#8888a8;margin-bottom:0;">Score d\'Attractivité Locative</p>'
                f'<div class="score-badge {badge_class}">{score_total}/100</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"> {resultat_score['resume']}")
            st.divider()

            # Démographie
            st.markdown("### 🏘️ Synthèse Démographique")
            col_d1, col_d2, col_d3, col_d4, col_d5 = st.columns(5, gap="large")
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
                st.metric("Croissance (5 ans)", f"{val_croissance}%" if val_croissance is not None else "N/D",
                         delta=f"{val_croissance}%" if val_croissance is not None else None)
            st.caption(f"📊 _{stats_demo.get('source', '')}_")
            st.divider()

            # Loisirs & Commodités
            st.markdown(f"### 🍔 Loisirs & Commodités — {_ville_loisirs}")
            col_c1, col_c2, col_c3 = st.columns(3, gap="large")
            with col_c1:
                st.metric("Restaurants & Fast-Foods", f"{loisirs_ville['nb_restos']:,}".replace(",", " "))
            with col_c2:
                st.metric("Centres de loisirs & Sports", f"{loisirs_ville['nb_loisirs']:,}".replace(",", " "))
            with col_c3:
                st.metric("Stations-service", f"{loisirs_ville['nb_essence']:,}".replace(",", " "))
            st.caption(f"*(Cinémas, arénas, centres de dek hockey, piscines municipales, etc.) — Source : {loisirs_ville['methode']}*")
            st.divider()

            # Grandes villes proches
            st.markdown("### 🏢 Grandes villes les plus proches")
            top_villes = resultat_score.get("top_villes")
            if top_villes:
                for i, (v, d) in enumerate(top_villes):
                    st.write(f"**{i+1}.** {v} à {d} km")
            else:
                st.write("Aucune grande ville trouvée.")
            st.divider()

            # Services à proximité
            st.markdown("### 📍 Services à Proximité (Rayon de 5 km)")
            titres_cat = {
                "epicerie":  "🛒 Épiceries & Supermarchés",
                "ecole":     "🏫 Écoles & Institutions",
                "pharmacie": "💊 Pharmacies",
                "bus":       "🚌 Transport en Commun",
                "parc":      "🌳 Parcs & Loisirs",
            }
            for cat_key, cat_titre in titres_cat.items():
                liste = tous_services.get(cat_key, [])
                nb = len(liste)
                with st.expander(f"{cat_titre} ({nb} trouvé{'s' if nb > 1 else ''})", expanded=(nb > 0)):
                    if liste:
                        rows = [{"Nom": s['nom'], "Distance": f"{s['distance_km']} km", "Temps estimé": f"~{s['temps_min']} min"} for s in liste]
                        st.table(pd.DataFrame(rows))
                    else:
                        st.write("Aucun trouvé dans un rayon de 5 km.")

            with st.expander("Voir le détail des points (Score / 100)"):
                st.dataframe(pd.DataFrame(resultat_score['details']), use_container_width=True)

        elif not _lancer:
            st.info("Sélectionnez une adresse pour lancer l'analyse automatiquement, ou utilisez le bouton 🔄 Relancer.")

    else:
        st.info("Veuillez sélectionner et confirmer une adresse dans la section 'Informations de l'immeuble' pour lancer l'analyse de localisation.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — RATIOS & RECOMMANDATION
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    custom_subheader("🎯 Ratios financiers")

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
        cols = st.columns(2, gap="large")
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
    custom_subheader("📝 Recommandation")
    recommandation = generer_recommandation(ratios, prix_achat)
    st.markdown(recommandation)

    # Résumé des loyers si détaillé
    if loyers_details:
        st.divider()
        custom_subheader("🏘️ Détail des loyers")
        
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
