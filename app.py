"""
app.py — Application Streamlit : Analyseur de Rentabilité Immobilière v2.0
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import st_folium
from html import escape

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

    .decision-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        min-height: 100%;
    }
    .decision-card.positive {
        border-top: 4px solid #16A34A;
    }
    .decision-card.warning {
        border-top: 4px solid #D97706;
    }
    .decision-card.negative {
        border-top: 4px solid #DC2626;
    }
    .decision-card.neutral {
        border-top: 4px solid #005A9C;
    }
    .decision-card .label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }
    .decision-card .value {
        font-size: 1.8rem;
        line-height: 1.1;
        font-weight: 900;
        color: #002A54;
        margin-bottom: 0.45rem;
    }
    .decision-card.positive .value {
        color: #166534;
    }
    .decision-card.warning .value {
        color: #B45309;
    }
    .decision-card.negative .value {
        color: #B91C1C;
    }
    .decision-card .note {
        font-size: 0.84rem;
        color: #475569;
        line-height: 1.35;
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
       ONGLETS
       ========================================= */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.55rem;
        width: 100%;
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        background: transparent;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }
    .stTabs [data-baseweb="tab"] {
        width: 100%;
        margin: 0 !important;
        padding: 0.72rem 0.8rem !important;
        min-height: 60px;
        border-radius: 16px 16px 0 0 !important;
        border: 1px solid #D8E2EE !important;
        border-bottom: 3px solid #D8E2EE !important;
        background: #FFFFFF !important;
        color: #35506E !important;
        font-size: 0.92rem !important;
        font-weight: 700 !important;
        line-height: 1.2 !important;
        text-align: center !important;
        justify-content: center !important;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        border-color: #AFC3D9 !important;
        background: #F8FBFF !important;
        transform: translateY(-1px);
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F3F8FD 100%) !important;
        color: #002A54 !important;
        border-color: #8FB0CF !important;
        border-bottom-color: #005A9C !important;
        box-shadow: 0 10px 22px rgba(0, 42, 84, 0.10);
    }
    .stTabs [data-baseweb="tab"] p {
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        white-space: normal !important;
        overflow-wrap: anywhere;
    }
    @media (max-width: 900px) {
        .stTabs [data-baseweb="tab-list"] {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }
    @media (max-width: 560px) {
        .stTabs [data-baseweb="tab-list"] {
            grid-template-columns: 1fr;
        }
        .stTabs [data-baseweb="tab"] {
            min-height: 54px;
            border-radius: 14px !important;
        }
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

    /* Etat des resultats */
    .statement-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.1rem 1.15rem 1rem 1.15rem;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
        min-height: 100%;
    }
    .statement-card + .statement-card {
        margin-top: 1rem;
    }
    .statement-card.income {
        border-top: 5px solid #16A34A;
    }
    .statement-card.opex {
        border-top: 5px solid #E11D48;
    }
    .statement-card.nonrec {
        border-top: 5px solid #F97316;
    }
    .statement-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.75rem;
        margin-bottom: 0.9rem;
    }
    .statement-kicker {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }
    .statement-title {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .statement-pill {
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        white-space: nowrap;
    }
    .statement-pill.income {
        background: #DCFCE7;
        color: #166534;
    }
    .statement-pill.opex {
        background: #FFE4E6;
        color: #9F1239;
    }
    .statement-pill.nonrec {
        background: #FFEDD5;
        color: #9A3412;
    }
    .statement-amount {
        font-size: 2rem;
        font-weight: 800;
        color: #002A54;
        margin-bottom: 0.2rem;
    }
    .statement-caption {
        color: #64748B;
        font-size: 0.8rem;
        margin-bottom: 0.85rem;
    }
    .statement-lines {
        border-top: 1px solid #E2E8F0;
        margin-top: 0.85rem;
        padding-top: 0.75rem;
    }
    .statement-line {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        padding: 0.46rem 0;
        border-bottom: 1px dashed #E2E8F0;
        color: #334155;
    }
    .statement-line:last-child {
        border-bottom: none;
    }
    .statement-line .label {
        color: #475569;
    }
    .statement-line .value {
        font-weight: 700;
        color: #0F172A;
        white-space: nowrap;
    }
    .statement-line.negative .value {
        color: #B91C1C;
    }
    .statement-line.total {
        margin-top: 0.55rem;
        padding-top: 0.8rem;
        border-top: 2px solid #CBD5E1;
        border-bottom: none;
    }
    .statement-line.total .label,
    .statement-line.total .value {
        font-size: 1.05rem;
        font-weight: 800;
        color: #002A54;
    }

    .autofinance-box {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #D8E2EE;
        border-radius: 18px;
        padding: 1.15rem 1.2rem;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    }
    .autofinance-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 0.9rem;
    }
    .autofinance-title {
        font-size: 1.15rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .autofinance-subtitle {
        font-size: 0.85rem;
        color: #64748B;
    }
    .autofinance-badge {
        padding: 0.4rem 0.8rem;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 800;
        white-space: nowrap;
    }
    .autofinance-badge.positive {
        background: #DCFCE7;
        color: #166534;
    }
    .autofinance-badge.negative {
        background: #FFE4E6;
        color: #9F1239;
    }
    .autofinance-steps {
        margin-top: 0.8rem;
        border-top: 1px solid #E2E8F0;
        padding-top: 0.8rem;
    }
    .autofinance-step {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        padding: 0.55rem 0;
        border-bottom: 1px dashed #E2E8F0;
    }
    .autofinance-step:last-child {
        border-bottom: none;
    }
    .autofinance-step .label {
        color: #475569;
    }
    .autofinance-step .value {
        font-weight: 700;
        color: #0F172A;
        white-space: nowrap;
    }
    .autofinance-step.minus .value {
        color: #B91C1C;
    }
    .autofinance-step.total {
        margin-top: 0.45rem;
        padding: 0.9rem 1rem;
        border-top: 2px solid #CBD5E1;
        border-radius: 14px;
        border-bottom: none;
    }
    .autofinance-step.total .label,
    .autofinance-step.total .value {
        color: #002A54;
        font-size: 1.08rem;
        font-weight: 900;
    }
    .autofinance-step.total.positive {
        background: #ECFDF3;
        border: 1px solid #86EFAC;
    }
    .autofinance-step.total.positive .label,
    .autofinance-step.total.positive .value {
        color: #166534;
    }
    .autofinance-step.total.negative {
        background: #FEF2F2;
        border: 1px solid #FCA5A5;
    }
    .autofinance-step.total.negative .label {
        color: #991B1B;
    }
    .autofinance-step.total.negative .value {
        color: #B91C1C;
    }
    .autofinance-kpis {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.8rem;
        margin-top: 1rem;
    }
    .autofinance-kpi {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 0.9rem 1rem;
    }
    .autofinance-kpi .label {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .autofinance-kpi .value {
        font-size: 1.3rem;
        color: #002A54;
        font-weight: 900;
    }
    @media (max-width: 700px) {
        .autofinance-kpis {
            grid-template-columns: 1fr;
        }
    }
    .statement-footer {
        margin-top: 1rem;
        padding: 0.85rem 1rem;
        border-radius: 14px;
        background: linear-gradient(135deg, #002A54 0%, #005A9C 100%);
        color: #FFFFFF;
    }
    .statement-footer .footer-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.8;
        margin-bottom: 0.2rem;
    }
    .statement-footer .footer-value {
        font-size: 1.55rem;
        font-weight: 800;
    }
    .statement-footer .footer-note {
        font-size: 0.82rem;
        opacity: 0.9;
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


def format_money(value):
    return f"{value:,.0f}$".replace(",", " ")


def statement_row(label, value, negative=False, total=False):
    return {
        "label": label,
        "value": value,
        "negative": negative,
        "total": total,
    }


def render_statement_card(theme, kicker, title, pill, amount, rows, footer_label=None, footer_value=None, footer_note=None, summary_metrics=None):
    theme_colors = {
        "income": {"line": "#16A34A", "pill_bg": "#DCFCE7", "pill_fg": "#166534"},
        "opex": {"line": "#E11D48", "pill_bg": "#FFE4E6", "pill_fg": "#9F1239"},
        "nonrec": {"line": "#F97316", "pill_bg": "#FFEDD5", "pill_fg": "#9A3412"},
    }
    palette = theme_colors.get(theme, theme_colors["income"])
    kicker_html = (
        f'<div style="font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:#64748B; font-weight:800; margin-bottom:0.2rem;">{escape(kicker)}</div>'
        if kicker else ""
    )
    pill_html = (
        f'<div style="padding:0.35rem 0.75rem; border-radius:999px; background:{palette["pill_bg"]}; color:{palette["pill_fg"]}; font-weight:800; white-space:nowrap;">{escape(pill)}</div>'
        if pill else ""
    )

    with st.container(border=True):
        header_html = (
            f'<div style="height:6px;background:{palette["line"]};border-radius:999px;margin:-1rem -1rem 1.15rem -1rem;"></div>'
            '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;">'
            '<div>'
            f"{kicker_html}"
            f'<div style="font-size:1.1rem;line-height:1.2;color:#0F172A;font-weight:800;">{escape(title)}</div>'
            '</div>'
            f"{pill_html}"
            '</div>'
            f'<div style="font-size:2.05rem;color:#002A54;font-weight:900;margin:1.1rem 0 0.35rem 0;">{escape(amount)}</div>'
        )
        st.markdown(
            header_html,
            unsafe_allow_html=True,
        )

        st.divider()

        for index, row in enumerate(rows):
            left, right = st.columns([2.9, 1.45], gap="medium")
            label_color = "#002A54" if row["total"] else "#475569"
            value_color = "#B91C1C" if row["negative"] else "#0F172A"
            if row["total"]:
                value_color = "#002A54"
            label_weight = 800 if row["total"] else 500
            value_weight = 900 if row["total"] else 700

            with left:
                st.markdown(
                    f'<div style="color:{label_color}; font-weight:{label_weight};">{escape(row["label"])}</div>',
                    unsafe_allow_html=True,
                )
            with right:
                st.markdown(
                    f'<div style="text-align:right; color:{value_color}; font-weight:{value_weight}; white-space:nowrap; padding-right:0.25rem;">{escape(row["value"])}</div>',
                    unsafe_allow_html=True,
                )

            if index < len(rows) - 1:
                separator = "2px solid #CBD5E1" if row["total"] else "1px dashed #E2E8F0"
                st.markdown(
                    f'<div style="border-bottom:{separator}; margin:0.5rem 0 0.85rem 0;"></div>',
                    unsafe_allow_html=True,
                )

        if summary_metrics:
            st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)
            for metric in summary_metrics:
                summary_html = (
                    '<div style="border:1px solid #E2E8F0;border-radius:12px;padding:0.9rem 1rem;background:#F8FAFC;margin-bottom:0.75rem;">'
                    f'<div style="font-size:0.8rem;color:#64748B;font-weight:700;margin-bottom:0.3rem;">{escape(metric["label"])}</div>'
                    f'<div style="font-size:1.45rem;color:#002A54;font-weight:900;line-height:1.15;">{escape(metric["value"])}</div>'
                    '</div>'
                )
                st.markdown(
                    summary_html,
                    unsafe_allow_html=True,
                )

        if footer_label and footer_value:
            footer_note_html = (
                f'<div style="font-size:0.82rem; opacity:0.9; margin-top:0.2rem;">{escape(footer_note)}</div>'
                if footer_note else ""
            )
            footer_html = (
                '<div style="margin-top:1rem;padding:0.9rem 1rem;border-radius:14px;background:linear-gradient(135deg, #002A54 0%, #005A9C 100%);color:#FFFFFF;">'
                f'<div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:0.08em;opacity:0.82;margin-bottom:0.2rem;">{escape(footer_label)}</div>'
                f'<div style="font-size:1.45rem;font-weight:900;">{escape(footer_value)}</div>'
                f"{footer_note_html}"
                '</div>'
            )
            st.markdown(
                footer_html,
                unsafe_allow_html=True,
            )


def statement_card_html(theme, kicker, title, amount, caption, rows, footer_label=None, footer_value=None, footer_note=None, summary_metrics=None):
    render_statement_card(
        theme,
        kicker,
        title,
        amount,
        caption,
        rows,
        footer_label=footer_label,
        footer_value=footer_value,
        footer_note=footer_note,
        summary_metrics=summary_metrics,
    )
    return ""


def decision_card_html(label, value, note, variant="neutral"):
    return (
        f'<div class="decision-card {variant}">'
        f'<div class="label">{escape(label)}</div>'
        f'<div class="value">{escape(value)}</div>'
        f'<div class="note">{escape(note)}</div>'
        '</div>'
    )


def render_autofinancement_section(revenus_nets, depenses, rne, interets, capital, cashflow, mise_de_fonds, frais_acquisition):
    badge_class = "positive" if cashflow >= 0 else "negative"
    badge_text = "Se paie seul" if cashflow >= 0 else "Apport requis"
    reste_mensuel = cashflow / 12
    service_dette = interets + capital
    apport_initial_total = mise_de_fonds + frais_acquisition
    total_step_class = "positive" if cashflow >= 0 else "negative"
    cashflow_label = "Argent restant après dette" if cashflow >= 0 else "Déficit après dette"
    cashflow_value = format_money(cashflow) if cashflow >= 0 else f"-{format_money(abs(cashflow))}"
    reste_mensuel_label = "Reste mensuel" if cashflow >= 0 else "Déficit mensuel"
    reste_mensuel_value = format_money(reste_mensuel) if cashflow >= 0 else f"-{format_money(abs(reste_mensuel))}"

    steps_html = "".join([
        f'<div class="autofinance-step"><span class="label">Revenus nets effectifs</span><span class="value">{format_money(revenus_nets)}</span></div>',
        f'<div class="autofinance-step minus"><span class="label">Moins dépenses d\'exploitation</span><span class="value">-{format_money(depenses)}</span></div>',
        f'<div class="autofinance-step"><span class="label">Résultat net d\'exploitation (RNE)</span><span class="value">{format_money(rne)}</span></div>',
        f'<div class="autofinance-step minus"><span class="label">Moins intérêts hypothécaires</span><span class="value">-{format_money(interets)}</span></div>',
        f'<div class="autofinance-step minus"><span class="label">Moins capital remboursé</span><span class="value">-{format_money(capital)}</span></div>',
        f'<div class="autofinance-step total {total_step_class}"><span class="label">{cashflow_label}</span><span class="value">{cashflow_value}</span></div>',
    ])
    kpis_html = "".join([
        f'<div class="autofinance-kpi"><div class="label">Service de la dette annuel</div><div class="value">{format_money(service_dette)}</div></div>',
        f'<div class="autofinance-kpi"><div class="label">{reste_mensuel_label}</div><div class="value">{reste_mensuel_value}</div></div>',
    ])
    sortie_poche_html = "".join([
        f'<div class="autofinance-kpi"><div class="label">Mise de fonds</div><div class="value">{format_money(mise_de_fonds)}</div></div>',
        f'<div class="autofinance-kpi"><div class="label">Frais d\'acquisition</div><div class="value">{format_money(frais_acquisition)}</div></div>',
        f'<div class="autofinance-kpi"><div class="label">Total à sortir de votre poche</div><div class="value">{format_money(apport_initial_total)}</div></div>',
    ])
    subtitle = (
        "L'immeuble couvre ses charges et sa dette avec les revenus locatifs."
        if cashflow >= 0
        else "Les revenus locatifs ne couvrent pas entièrement la dette en année 1."
    )

    html = (
        '<div class="autofinance-box">'
        '<div class="autofinance-head">'
        '<div>'
        '<div class="autofinance-title">Autofinancement du projet</div>'
        f'<div class="autofinance-subtitle">{escape(subtitle)}</div>'
        '</div>'
        f'<div class="autofinance-badge {badge_class}">{badge_text}</div>'
        '</div>'
        f'<div class="autofinance-steps">{steps_html}</div>'
        f'<div class="autofinance-kpis">{kpis_html}</div>'
        '<div class="autofinance-steps" style="margin-top:1rem;">'
        '<div class="autofinance-title" style="font-size:1rem; margin-bottom:0.2rem;">Apport du propriétaire non inclus ci-dessus</div>'
        '<div class="autofinance-subtitle">Ces montants doivent être avancés personnellement au démarrage du projet.</div>'
        '</div>'
        f'<div class="autofinance-kpis">{sortie_poche_html}</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)

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
ville_taxe = "Autre (entrer manuellement)"
for v in TAUX_MUNICIPAUX.keys():
    if v.lower() in ville.lower():
        ville_taxe = v
        break
taux_municipal = TAUX_MUNICIPAUX.get(ville_taxe, 0.80)

col_form, col_spacer = st.columns([1.35, 0.65], gap="large")
with col_form:

    # Taux municipal calculé en arrière-plan selon la ville détectée
    ville_taxe = "Autre (entrer manuellement)"
    for v in TAUX_MUNICIPAUX.keys():
        if v.lower() in ville.lower():
            ville_taxe = v
            break
    taux_municipal = TAUX_MUNICIPAUX.get(ville_taxe, 0.80)


with col_form:
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

ratios = calculer_ratios(
    prix_achat=prix_achat,
    rne=resultats["rne"],
    cashflow_annee1=resultats["cashflow_avant_frais"],  # Cashflow opérationnel pour le Cash-on-cash
    mise_de_fonds=resultats["mise_de_fonds"],
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
    custom_subheader("📈 Analyse Année 1")

    perte_vacance = resultats["revenus_bruts_annuels"] - resultats["revenus_nets"]
    revenus_rows = [
        statement_row("Loyers bruts potentiels", format_money(resultats["revenus_bruts_annuels"])),
        statement_row(f"Vacance ({taux_vacance:.1f}%)", f"-{format_money(perte_vacance)}", negative=True),
        statement_row("Revenus nets effectifs", format_money(resultats["revenus_nets"]), total=True),
    ]

    depenses_rows = [
        statement_row("Taxes municipales", format_money(resultats["taxes_municipales"])),
        statement_row("Taxes scolaires", format_money(resultats["taxes_scolaires"])),
        statement_row("Assurance", format_money(assurance)),
    ]
    if electricite > 0:
        depenses_rows.append(statement_row("Électricité", format_money(electricite)))
    depenses_rows.extend([
        statement_row("Tonte", format_money(tonte)),
        statement_row("Déneigement", format_money(deneigement)),
        statement_row("Entretien / réparations", format_money(entretien_autre)),
    ])
    if gestion > 0:
        depenses_rows.append(statement_row("Gestion", format_money(gestion)))
    if autres_depenses > 0:
        depenses_rows.append(statement_row("Autres charges", format_money(autres_depenses)))
    acquisition_rows = [
        statement_row("Droits de mutation", format_money(resultats["droits_mutation"])),
        statement_row("Notaire", format_money(frais_notaire)),
        statement_row("Inspection", format_money(frais_inspection)),
        statement_row("Évaluation", format_money(frais_evaluation)),
    ]

    col_rev, col_dep, col_non_rec = st.columns(3, gap="medium")

    with col_rev:
        st.markdown(
            statement_card_html(
                "income",
                "",
                "Revenus locatifs",
                "",
                format_money(resultats["revenus_nets"]),
                revenus_rows,
                None,
                None,
                None,
            ),
            unsafe_allow_html=True,
        )

    with col_dep:
        st.markdown(
            statement_card_html(
                "opex",
                "",
                "Dépenses annuelles",
                "",
                format_money(resultats["depenses_totales"]),
                depenses_rows,
                "Bénéfice d'exploitation",
                format_money(resultats["rne"]),
                None,
            ),
            unsafe_allow_html=True,
        )

    with col_non_rec:
        st.markdown(
            statement_card_html(
                "nonrec",
                "",
                "Frais non récurrents",
                "Année 1",
                format_money(resultats["frais_acquisition"]),
                acquisition_rows,
                None,
                None,
                None,
                summary_metrics=[
                    {"label": "Mise de fonds", "value": format_money(resultats["mise_de_fonds"])},
                    {"label": "Frais d'acquisition", "value": format_money(resultats["frais_acquisition"])},
                ],
            ),
            unsafe_allow_html=True,
        )

    st.divider()
    render_autofinancement_section(
        revenus_nets=resultats["revenus_nets"],
        depenses=resultats["depenses_totales"],
        rne=resultats["rne"],
        interets=resultats["interet_annee1"],
        capital=resultats["capital_annee1"],
        cashflow=resultats["cashflow_avant_frais"],
        mise_de_fonds=resultats["mise_de_fonds"],
        frais_acquisition=resultats["frais_acquisition"],
    )

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

    dep_df = (
        pd.DataFrame({"poste": dep_labels, "montant": dep_values})
        .sort_values("montant", ascending=False)
        .reset_index(drop=True)
    )
    dep_df["part_pct"] = dep_df["montant"] / dep_df["montant"].sum() * 100
    dep_df["montant_fmt"] = dep_df["montant"].apply(format_money)
    dep_df["part_fmt"] = dep_df["part_pct"].apply(lambda x: f"{x:.1f}%")

    color_map = {
        "Hypothèque (intérêts)": "#D9B36C",
        "Entretien": "#FFD23F",
        "Entretien / réparations": "#FFD23F",
        "Taxes munic.": "#64C2A6",
        "Taxes municipales": "#64C2A6",
        "Assurance": "#8C9FD1",
        "Déneigement": "#A6D854",
        "Tonte": "#F08AC0",
        "Taxes scol.": "#9AA5B1",
        "Taxes scolaires": "#9AA5B1",
        "Électricité": "#FF8A5B",
        "Gestion": "#6C7BFF",
        "Autres": "#B8C0CC",
    }
    dep_colors = [color_map.get(label, "#94A3B8") for label in dep_df["poste"]]

    chart_col, rank_col = st.columns([1.15, 0.85], gap="large")

    with chart_col:
        fig_donut = go.Figure(
            data=[
                go.Pie(
                    labels=dep_df["poste"],
                    values=dep_df["montant"],
                    hole=0.62,
                    sort=False,
                    direction="clockwise",
                    textinfo="none",
                    hovertemplate="<b>%{label}</b><br>%{value:,.0f}$<br>%{percent}<extra></extra>",
                    marker=dict(colors=dep_colors, line=dict(color="#F8FAFC", width=3)),
                )
            ]
        )
        fig_donut.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155"),
            height=430,
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            annotations=[
                dict(
                    text=f"<span style='font-size:13px;color:#64748B;'>Total</span><br><span style='font-size:28px;color:#002A54;'><b>{format_money(dep_df['montant'].sum())}</b></span>",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    align="center",
                )
            ],
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with rank_col:
        fig_bar = go.Figure(
            go.Bar(
                x=dep_df["montant"],
                y=dep_df["poste"],
                orientation="h",
                marker=dict(color=dep_colors, line=dict(color="rgba(255,255,255,0.9)", width=1)),
                text=dep_df["montant_fmt"] + " · " + dep_df["part_fmt"],
                textposition="outside",
                cliponaxis=False,
                customdata=dep_df[["part_fmt"]],
                hovertemplate="<b>%{y}</b><br>%{x:,.0f}$<br>%{customdata[0]} du total<extra></extra>",
            )
        )
        fig_bar.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155"),
            height=430,
            margin=dict(t=18, b=10, l=10, r=120),
            xaxis=dict(
                showgrid=False,
                showticklabels=False,
                zeroline=False,
                title=None,
            ),
            yaxis=dict(
                title=None,
                tickfont=dict(size=13, color="#475569"),
                autorange="reversed",
            ),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

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
                    "primaire":  {"label": "École primaire", "color": "blue", "icon": "child"},
                    "secondaire":{"label": "École secondaire", "color": "cadetblue", "icon": "book"},
                    "cegep":     {"label": "Cégep", "color": "darkblue", "icon": "university"},
                    "universite":{"label": "Université", "color": "lightgray", "icon": "graduation-cap"},
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
                "primaire":  "🎒 Écoles Primaires",
                "secondaire":"📓 Écoles Secondaires",
                "cegep":     "📚 Cégeps",
                "universite":"🎓 Universités",
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

    st.divider()
    custom_subheader("📌 Aide à la décision")

    cout_annuel_a_couvrir = resultats["depenses_totales"] + resultats["paiement_annuel"]
    facteur_occupation = 1 - (taux_vacance / 100)
    loyer_equilibre_annuel = (cout_annuel_a_couvrir / facteur_occupation) if facteur_occupation > 0 else None
    loyer_equilibre_mensuel = (loyer_equilibre_annuel / 12) if loyer_equilibre_annuel is not None else None
    loyer_equilibre_par_logement = (loyer_equilibre_mensuel / nb_logements) if loyer_equilibre_mensuel and nb_logements > 0 else None
    ecart_loyer = (loyers_mensuels_total - loyer_equilibre_mensuel) if loyer_equilibre_mensuel is not None else None

    if loyer_equilibre_mensuel is None:
        loyer_equilibre_value = "N/A"
        loyer_equilibre_note = "Impossible a calculer avec 100% de vacance."
        loyer_equilibre_variant = "warning"
    else:
        loyer_equilibre_value = f"{format_money(loyer_equilibre_mensuel)}/mois"
        if ecart_loyer is not None and ecart_loyer >= 0:
            loyer_equilibre_note = (
                f"Actuel : {format_money(loyers_mensuels_total)}/mois. "
                f"Marge de {format_money(ecart_loyer)}/mois."
            )
            loyer_equilibre_variant = "positive"
        else:
            manque = abs(ecart_loyer) if ecart_loyer is not None else 0
            loyer_equilibre_note = (
                f"Actuel : {format_money(loyers_mensuels_total)}/mois. "
                f"Il manque {format_money(manque)}/mois pour l'equilibre."
            )
            loyer_equilibre_variant = "negative"
        if loyer_equilibre_par_logement is not None:
            loyer_equilibre_note += f" Environ {format_money(loyer_equilibre_par_logement)}/logement/mois."

    vacance_max_brute = (
        (1 - (cout_annuel_a_couvrir / resultats["revenus_bruts_annuels"])) * 100
        if resultats["revenus_bruts_annuels"] > 0 else None
    )
    if vacance_max_brute is None:
        vacance_value = "N/A"
        vacance_note = "Aucun revenu brut disponible pour calculer cette marge."
        vacance_variant = "warning"
    elif vacance_max_brute <= 0:
        vacance_value = "0,0%"
        vacance_note = "Meme a pleine occupation, le projet ne couvre pas totalement ses charges et sa dette."
        vacance_variant = "negative"
    else:
        vacance_value = f"{vacance_max_brute:.1f}%"
        if vacance_max_brute >= taux_vacance:
            vacance_note = f"Avec les loyers actuels, le projet reste viable jusqu'a {vacance_max_brute:.1f}% de vacance."
            vacance_variant = "positive"
        else:
            vacance_note = f"La vacance utilisee ({taux_vacance:.1f}%) depasse deja la marge supportable."
            vacance_variant = "warning"

    cashflow_annuel = resultats["cashflow_avant_frais"]
    cashflow_mensuel = cashflow_annuel / 12
    if cashflow_annuel >= 0:
        cashflow_value = format_money(cashflow_annuel)
        cashflow_note = f"Soit {format_money(cashflow_mensuel)}/mois apres OPEX et service de la dette."
        cashflow_variant = "positive"
        cashflow_label = "Surplus apres dette"
    else:
        cashflow_value = f"-{format_money(abs(cashflow_annuel))}"
        cashflow_note = f"Soit -{format_money(abs(cashflow_mensuel))}/mois a couvrir par le proprietaire."
        cashflow_variant = "negative"
        cashflow_label = "Deficit apres dette"

    apport_initial = resultats["mise_de_fonds"] + resultats["frais_acquisition"]
    apport_note = (
        f"Mise de fonds {format_money(resultats['mise_de_fonds'])} + "
        f"frais d'acquisition {format_money(resultats['frais_acquisition'])}."
    )

    info_row1 = st.columns(2, gap="large")
    with info_row1[0]:
        st.markdown(
            decision_card_html(
                "Loyer d'equilibre",
                loyer_equilibre_value,
                loyer_equilibre_note,
                loyer_equilibre_variant,
            ),
            unsafe_allow_html=True,
        )
    with info_row1[1]:
        st.markdown(
            decision_card_html(
                "Vacance max. supportable",
                vacance_value,
                vacance_note,
                vacance_variant,
            ),
            unsafe_allow_html=True,
        )

    info_row2 = st.columns(2, gap="large")
    with info_row2[0]:
        st.markdown(
            decision_card_html(
                cashflow_label,
                cashflow_value,
                cashflow_note,
                cashflow_variant,
            ),
            unsafe_allow_html=True,
        )
    with info_row2[1]:
        st.markdown(
            decision_card_html(
                "Apport initial requis",
                format_money(apport_initial),
                apport_note,
                "neutral",
            ),
            unsafe_allow_html=True,
        )

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
