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
    analyser_opportunite_investissement,
    calculer_taxes_municipales,
    calculer_taxes_scolaires,
)
from ai_recommendation import enrich_analysis_with_ai
from location import calculer_score_localisation_avance
from geocoding import verifier_adresse, rechercher_adresses, determiner_region_gps, obtenir_tous_services, obtenir_loisirs_ville
from demographie import analyser_demographie
from dotenv import load_dotenv

load_dotenv()

AI_RECOMMENDATION_CACHE_VERSION = "2026-03-23-gemini-premium-v2"


@st.cache_data(show_spinner=False, ttl=900)
def get_recommendation_analysis(base_analysis, dossier_context, cache_version):
    _ = cache_version
    return enrich_analysis_with_ai(base_analysis, dossier_context)

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
    .ai-insight-shell {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FBFF 100%);
        border: 1px solid #D8E2EE;
        border-radius: 20px;
        padding: 1.1rem 1.15rem;
        margin-top: 1rem;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
    }
    .ai-insight-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        margin-bottom: 0.9rem;
    }
    .ai-insight-kicker {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 800;
    }
    .ai-insight-title {
        font-size: 1.15rem;
        color: #002A54;
        font-weight: 900;
        margin-top: 0.18rem;
    }
    .ai-insight-pill {
        padding: 0.42rem 0.8rem;
        border-radius: 999px;
        background: #E2EDF8;
        color: #234361;
        font-size: 0.78rem;
        font-weight: 800;
        white-space: nowrap;
    }
    .ai-insight-summary {
        background: linear-gradient(135deg, #002A54 0%, #005A9C 100%);
        color: #FFFFFF;
        border-radius: 18px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 24px rgba(0, 42, 84, 0.16);
    }
    .ai-insight-summary-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.82;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }
    .ai-insight-summary-text {
        font-size: 0.98rem;
        line-height: 1.55;
    }
    .ai-list-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        height: 100%;
    }
    .ai-list-card.positive {
        border-top: 4px solid #16A34A;
    }
    .ai-list-card.warning {
        border-top: 4px solid #D97706;
    }
    .ai-list-card.neutral {
        border-top: 4px solid #005A9C;
    }
    .ai-list-card .title {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #64748B;
        font-weight: 800;
        margin-bottom: 0.7rem;
    }
    .ai-list-card ul {
        margin: 0;
        padding-left: 1.1rem;
        color: #334155;
    }
    .ai-list-card li {
        margin-bottom: 0.48rem;
        line-height: 1.42;
    }
    .ai-list-card .empty {
        color: #64748B;
        font-size: 0.86rem;
        line-height: 1.4;
    }
    .ai-detail-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1rem 1.05rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        height: 100%;
    }
    .ai-detail-card.positive {
        border-top: 4px solid #16A34A;
    }
    .ai-detail-card.warning {
        border-top: 4px solid #D97706;
    }
    .ai-detail-card.neutral {
        border-top: 4px solid #005A9C;
    }
    .ai-detail-card .eyebrow {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }
    .ai-detail-card .title {
        font-size: 0.9rem;
        color: #0F172A;
        font-weight: 800;
        margin-bottom: 0.45rem;
    }
    .ai-detail-card .body {
        color: #334155;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    .ai-block-heading {
        margin: 1rem 0 0.7rem;
    }
    .ai-block-kicker {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }
    .ai-block-title {
        font-size: 1.05rem;
        font-weight: 900;
        color: #0F172A;
    }
    .ai-block-caption {
        margin-top: 0.18rem;
        color: #64748B;
        font-size: 0.86rem;
    }
    .ai-summary-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
        border: 1px solid #D8E2EE;
        border-radius: 18px;
        padding: 1rem 1.05rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
    }
    .ai-summary-top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
        flex-wrap: wrap;
        margin-bottom: 0.7rem;
    }
    .ai-summary-subtitle {
        font-size: 0.8rem;
        font-weight: 800;
        color: #46627F;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    .ai-summary-provider {
        padding: 0.38rem 0.75rem;
        border-radius: 999px;
        background: #E8F0F8;
        color: #234361;
        font-size: 0.78rem;
        font-weight: 800;
        white-space: nowrap;
    }
    .ai-summary-text {
        color: #1F2937;
        font-size: 0.98rem;
        line-height: 1.58;
    }
    .ai-thesis-row {
        margin-top: 0.8rem;
        padding-top: 0.8rem;
        border-top: 1px solid #E8EEF6;
        display: flex;
        gap: 0.55rem;
        align-items: baseline;
        flex-wrap: wrap;
    }
    .ai-thesis-label {
        color: #46627F;
        font-size: 0.82rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .ai-thesis-value {
        color: #334155;
        font-size: 0.92rem;
        line-height: 1.5;
        flex: 1 1 240px;
    }
    .ai-verdict-card {
        background: #FFFFFF;
        border: 1px solid #D8E2EE;
        border-radius: 22px;
        padding: 1.2rem 1.2rem 1.1rem;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
    }
    .ai-verdict-layout {
        display: grid;
        grid-template-columns: minmax(0, 1.5fr) minmax(260px, 0.9fr);
        gap: 1.4rem;
        align-items: center;
    }
    .ai-verdict-copy {
        min-width: 0;
    }
    .ai-verdict-card.positive {
        border-top: 4px solid #16A34A;
    }
    .ai-verdict-card.warning {
        border-top: 4px solid #D97706;
    }
    .ai-verdict-card.negative {
        border-top: 4px solid #DC2626;
    }
    .ai-verdict-card.neutral {
        border-top: 4px solid #005A9C;
    }
    .ai-verdict-head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.9rem;
        flex-wrap: wrap;
        margin-bottom: 0.6rem;
    }
    .ai-verdict-kicker {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    .ai-verdict-title {
        font-size: 2rem;
        line-height: 1.02;
        font-weight: 900;
        color: #0F172A;
        max-width: 28rem;
    }
    .ai-verdict-badges {
        display: flex;
        gap: 0.45rem;
        flex-wrap: wrap;
        justify-content: flex-end;
    }
    .ai-verdict-pill {
        padding: 0.36rem 0.72rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 800;
        white-space: nowrap;
        border: 1px solid transparent;
    }
    .ai-verdict-pill.positive {
        background: #F0FDF4;
        border-color: #BBF7D0;
        color: #166534;
    }
    .ai-verdict-pill.warning {
        background: #FFFBEB;
        border-color: #FDE68A;
        color: #9A6700;
    }
    .ai-verdict-pill.negative {
        background: #FEF2F2;
        border-color: #FECACA;
        color: #991B1B;
    }
    .ai-verdict-pill.neutral {
        background: #EFF6FF;
        border-color: #BFDBFE;
        color: #234361;
    }
    .ai-verdict-reason {
        color: #334155;
        font-size: 0.95rem;
        line-height: 1.48;
        max-width: 46rem;
    }
    .ai-verdict-visual {
        border-left: 1px solid #EDF2F7;
        padding-left: 1.2rem;
    }
    .ai-verdict-visual-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 800;
        margin-bottom: 0.8rem;
    }
    .ai-verdict-approach {
        display: grid;
        grid-template-columns: minmax(0, 1fr) auto;
        gap: 0.85rem;
        align-items: end;
    }
    .ai-verdict-track-shell {
        position: relative;
        min-height: 4.6rem;
    }
    .ai-verdict-lane {
        position: absolute;
        left: 0;
        right: 0;
        top: 2.55rem;
        height: 4px;
        border-radius: 999px;
        background: linear-gradient(90deg, #F3D1D1 0%, #F4E8C8 48%, #CFEAD6 100%);
    }
    .ai-verdict-pointer {
        position: absolute;
        top: 0;
        transform: translateX(-50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.15rem;
        z-index: 2;
    }
    .ai-verdict-pointer-tag {
        color: #475569;
        font-size: 0.68rem;
        line-height: 1;
        font-weight: 800;
        white-space: nowrap;
    }
    .ai-verdict-pointer-arrow {
        font-size: 1.08rem;
        line-height: 1;
        font-weight: 900;
    }
    .ai-verdict-pointer.positive .ai-verdict-pointer-arrow {
        color: #16A34A;
    }
    .ai-verdict-pointer.warning .ai-verdict-pointer-arrow {
        color: #D97706;
    }
    .ai-verdict-pointer.negative .ai-verdict-pointer-arrow {
        color: #DC2626;
    }
    .ai-verdict-pointer.neutral .ai-verdict-pointer-arrow {
        color: #005A9C;
    }
    .ai-verdict-building {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.35rem;
        min-width: 3.8rem;
    }
    .ai-verdict-building-body {
        width: 2.9rem;
        height: 4.2rem;
        border-radius: 0.95rem 0.95rem 0.55rem 0.55rem;
        border: 1px solid #CAD8E6;
        background: #F8FBFE;
        padding: 0.55rem 0.48rem 0.75rem;
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.22rem;
        position: relative;
    }
    .ai-verdict-building-body span {
        display: block;
        height: 0.5rem;
        border-radius: 0.22rem;
        background: #EEF4FA;
        border: 1px solid #DCE8F3;
    }
    .ai-verdict-building-door {
        position: absolute;
        left: 50%;
        bottom: 0;
        transform: translateX(-50%);
        width: 0.72rem;
        height: 0.95rem;
        border-radius: 0.38rem 0.38rem 0 0;
        background: #6B85A1;
    }
    .ai-verdict-building-label {
        color: #64748B;
        font-size: 0.66rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 800;
        white-space: nowrap;
    }
    .ai-verdict-scale-line {
        display: flex;
        justify-content: space-between;
        gap: 0.65rem;
        margin-top: 0.55rem;
        color: #94A3B8;
        font-size: 0.7rem;
        font-weight: 800;
    }
    .ai-verdict-scale-label.active {
        color: #0F172A;
    }
    .ai-verdict-scale-label.active.positive {
        color: #166534;
    }
    .ai-verdict-scale-label.active.warning {
        color: #9A6700;
    }
    .ai-verdict-scale-label.active.negative {
        color: #991B1B;
    }
    .ai-verdict-scale-label.active.neutral {
        color: #234361;
    }
    .ai-verdict-visual-caption {
        margin-top: 0.6rem;
        color: #475569;
        font-size: 0.82rem;
        line-height: 1.42;
        max-width: 22rem;
    }
    .ai-verdict-flow-shell {
        margin-bottom: 1.1rem;
    }
    .ai-verdict-flow-guide {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.4rem;
        margin-top: 0.8rem;
    }
    .ai-verdict-flow-arrow {
        width: 2.65rem;
        height: 2.65rem;
        border-radius: 999px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(180deg, #FFF8E1 0%, #FDE68A 100%);
        border: 1px solid #F4D08B;
        color: #9A6700;
        font-size: 1.4rem;
        font-weight: 900;
        box-shadow: 0 10px 22px rgba(154, 103, 0, 0.12);
    }
    .ai-verdict-flow-text {
        text-align: center;
        color: #64748B;
        font-size: 0.82rem;
        line-height: 1.4;
        font-weight: 700;
        max-width: 34rem;
    }
    .ai-diagnostic-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 1rem 1.05rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
        height: 100%;
    }
    .ai-diagnostic-card.positive {
        border-left: 4px solid #16A34A;
    }
    .ai-diagnostic-card.warning {
        border-left: 4px solid #D97706;
    }
    .ai-diagnostic-card.negative {
        border-left: 4px solid #DC2626;
    }
    .ai-diagnostic-card .title {
        font-size: 0.92rem;
        color: #0F172A;
        font-weight: 900;
        margin-bottom: 0.15rem;
    }
    .ai-diagnostic-card .subtitle {
        color: #64748B;
        font-size: 0.82rem;
        margin-bottom: 0.7rem;
    }
    .ai-metric-row {
        display: flex;
        gap: 0.8rem;
        padding: 0.8rem 0;
        border-top: 1px solid #EEF2F7;
    }
    .ai-metric-row:first-child {
        border-top: none;
        padding-top: 0.15rem;
    }
    .ai-metric-icon {
        width: 0.72rem;
        height: 0.72rem;
        border-radius: 999px;
        margin-top: 0.42rem;
        flex: 0 0 auto;
    }
    .ai-metric-row.positive .ai-metric-icon {
        background: #16A34A;
        box-shadow: 0 0 0 5px rgba(22, 163, 74, 0.10);
    }
    .ai-metric-row.warning .ai-metric-icon {
        background: #D97706;
        box-shadow: 0 0 0 5px rgba(217, 119, 6, 0.10);
    }
    .ai-metric-row.negative .ai-metric-icon {
        background: #DC2626;
        box-shadow: 0 0 0 5px rgba(220, 38, 38, 0.10);
    }
    .ai-metric-content {
        flex: 1 1 auto;
    }
    .ai-metric-line {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .ai-metric-name {
        font-size: 0.9rem;
        font-weight: 800;
        color: #0F172A;
    }
    .ai-metric-value {
        font-size: 1rem;
        font-weight: 900;
        color: #002A54;
        white-space: nowrap;
    }
    .ai-metric-row.negative .ai-metric-value {
        color: #B91C1C;
    }
    .ai-metric-row.warning .ai-metric-value {
        color: #B45309;
    }
    .ai-metric-note {
        margin-top: 0.18rem;
        color: #475569;
        font-size: 0.84rem;
        line-height: 1.42;
    }
    .ai-metric-empty {
        color: #64748B;
        font-size: 0.86rem;
        line-height: 1.45;
        padding-top: 0.2rem;
    }
    .ai-plan-card {
        background: linear-gradient(180deg, #FFFFFF 0%, #FBFDFF 100%);
        border: 1px solid #D8E2EE;
        border-radius: 18px;
        padding: 1rem 1.05rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
        height: 100%;
    }
    .ai-plan-card.positive {
        border-top: 4px solid #16A34A;
    }
    .ai-plan-card.warning {
        border-top: 4px solid #D97706;
    }
    .ai-plan-card.negative {
        border-top: 4px solid #DC2626;
    }
    .ai-plan-card.neutral {
        border-top: 4px solid #005A9C;
    }
    .ai-plan-top {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        margin-bottom: 0.75rem;
    }
    .ai-plan-rank {
        width: 1.9rem;
        height: 1.9rem;
        border-radius: 999px;
        background: #0F172A;
        color: #FFFFFF;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 900;
        font-size: 0.86rem;
        flex: 0 0 auto;
    }
    .ai-plan-priority {
        color: #46627F;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 800;
    }
    .ai-plan-title {
        color: #0F172A;
        font-size: 0.96rem;
        font-weight: 900;
        margin-bottom: 0.2rem;
    }
    .ai-plan-value {
        color: #002A54;
        font-size: 1.85rem;
        line-height: 1.05;
        font-weight: 900;
        margin-bottom: 0.55rem;
    }
    .ai-plan-card.negative .ai-plan-value {
        color: #B91C1C;
    }
    .ai-plan-card.warning .ai-plan-value {
        color: #B45309;
    }
    .ai-plan-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin-bottom: 0.7rem;
    }
    .ai-plan-chip {
        padding: 0.32rem 0.7rem;
        border-radius: 999px;
        background: #F1F5F9;
        color: #334155;
        font-size: 0.76rem;
        font-weight: 800;
    }
    .ai-plan-state {
        color: #64748B;
        font-size: 0.78rem;
        font-weight: 700;
        margin-bottom: 0.45rem;
    }
    .ai-plan-note {
        color: #475569;
        font-size: 0.88rem;
        line-height: 1.45;
    }
    .ai-preview-shell {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%);
        border-radius: 20px;
        padding: 1rem 1.05rem;
        color: #FFFFFF;
        box-shadow: 0 14px 30px rgba(15, 23, 42, 0.14);
    }
    .ai-preview-kicker {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 800;
        opacity: 0.78;
        margin-bottom: 0.25rem;
    }
    .ai-preview-title {
        font-size: 1.08rem;
        font-weight: 900;
        margin-bottom: 0.18rem;
    }
    .ai-preview-note {
        color: rgba(255, 255, 255, 0.82);
        font-size: 0.86rem;
        line-height: 1.45;
    }
    .ai-preview-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.75rem;
        margin-top: 0.9rem;
    }
    .ai-preview-metric {
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 0.8rem 0.9rem;
        backdrop-filter: blur(8px);
    }
    .ai-preview-metric-label {
        font-size: 0.74rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: rgba(255, 255, 255, 0.72);
        font-weight: 800;
        margin-bottom: 0.22rem;
    }
    .ai-preview-metric-value {
        font-size: 1.25rem;
        font-weight: 900;
        color: #FFFFFF;
        line-height: 1.1;
    }
    @media (max-width: 900px) {
        .ai-verdict-layout {
            grid-template-columns: 1fr;
        }
        .ai-verdict-title {
            font-size: 1.65rem;
            max-width: none;
        }
        .ai-verdict-badges {
            justify-content: flex-start;
        }
        .ai-verdict-visual {
            border-left: none;
            border-top: 1px solid #EDF2F7;
            padding-left: 0;
            padding-top: 1rem;
        }
        .ai-plan-value {
            font-size: 1.55rem;
        }
        .ai-summary-provider {
            white-space: normal;
        }
    }
    .decision-meter-shell {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 1rem 1rem 1.1rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.05);
    }
    .decision-meter-shell.positive {
        border-top: 4px solid #16A34A;
    }
    .decision-meter-shell.warning {
        border-top: 4px solid #D97706;
    }
    .decision-meter-shell.negative {
        border-top: 4px solid #DC2626;
    }
    .decision-meter-shell.neutral {
        border-top: 4px solid #005A9C;
    }
    .decision-meter-header {
        margin-bottom: 0.75rem;
    }
    .decision-meter-kicker {
        font-size: 0.76rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 800;
    }
    .decision-meter-title {
        font-size: 1rem;
        font-weight: 800;
        color: #002A54;
        margin-top: 0.2rem;
    }
    .decision-meter {
        position: relative;
        padding-top: 3.35rem;
    }
    .decision-meter-arrow {
        position: absolute;
        top: 0;
        transform: translateX(-50%);
        display: flex;
        flex-direction: column;
        align-items: center;
        pointer-events: none;
        z-index: 2;
    }
    .decision-meter-badge {
        background: #0F172A;
        color: #FFFFFF;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 800;
        line-height: 1;
        white-space: nowrap;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.15);
    }
    .decision-meter-arrow-line {
        width: 4px;
        height: 1.5rem;
        border-radius: 999px;
        background: #0F172A;
        margin-top: 0.2rem;
    }
    .decision-meter-arrow-head {
        width: 0;
        height: 0;
        border-left: 10px solid transparent;
        border-right: 10px solid transparent;
        border-top: 14px solid #0F172A;
        margin-top: -1px;
    }
    .decision-meter-track {
        display: flex;
        border-radius: 999px;
        overflow: hidden;
        border: 1px solid #D8E2EE;
        box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.08);
    }
    .decision-meter-segment {
        flex: 1 1 0;
        min-height: 4.5rem;
        display: flex;
        align-items: end;
        justify-content: center;
        text-align: center;
        padding: 0.8rem 0.45rem 0.7rem;
        font-size: 0.82rem;
        font-weight: 800;
        line-height: 1.2;
    }
    .decision-meter-segment.negative {
        background: linear-gradient(180deg, #FEE2E2 0%, #FECACA 100%);
        color: #7F1D1D;
    }
    .decision-meter-segment.warning {
        background: linear-gradient(180deg, #FEF3C7 0%, #FDE68A 100%);
        color: #854D0E;
        border-left: 1px solid rgba(255, 255, 255, 0.7);
        border-right: 1px solid rgba(255, 255, 255, 0.7);
    }
    .decision-meter-segment.positive {
        background: linear-gradient(180deg, #DCFCE7 0%, #BBF7D0 100%);
        color: #166534;
    }
    .decision-meter-caption {
        margin-top: 0.8rem;
        text-align: center;
        font-size: 0.88rem;
        color: #475569;
    }
    @media (max-width: 900px) {
        .decision-meter {
            padding-top: 3.8rem;
        }
        .decision-meter-badge {
            font-size: 0.7rem;
            padding: 0.3rem 0.6rem;
        }
        .decision-meter-segment {
            min-height: 4.8rem;
            font-size: 0.75rem;
            padding-left: 0.3rem;
            padding-right: 0.3rem;
        }
    }

    .projection-table-shell {
        position: relative;
        border: 1px solid #D8E2EE;
        border-radius: 18px;
        overflow: hidden;
        background: #FFFFFF;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.06);
        margin: 0.5rem 0 1rem 0;
    }
    .projection-table-shell.with-trigger {
        margin-top: 0.1rem;
    }
    .projection-table-actions {
        position: absolute;
        top: 0.8rem;
        right: 0.8rem;
        z-index: 8;
        opacity: 0;
        pointer-events: none;
        transform: translateY(-4px);
        transition: opacity 0.18s ease, transform 0.18s ease;
    }
    .projection-table-shell:hover .projection-table-actions,
    .projection-table-shell:focus-within .projection-table-actions {
        opacity: 1;
        pointer-events: auto;
        transform: translateY(0);
    }
    .projection-table-action {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 2.2rem;
        height: 2.2rem;
        border-radius: 10px;
        border: 1px solid #D8E2EE;
        background: rgba(255, 255, 255, 0.96);
        color: #35506E;
        box-shadow: 0 8px 18px rgba(15, 23, 42, 0.10);
        text-decoration: none;
        backdrop-filter: blur(6px);
        cursor: pointer;
        appearance: none;
    }
    .projection-table-action:hover {
        background: #FFFFFF;
        color: #002A54;
        border-color: #AFC3D9;
    }
    .projection-table-action svg {
        width: 1rem;
        height: 1rem;
    }
    .projection-table-scroll {
        overflow-x: auto;
    }
    .projection-table {
        width: max-content;
        min-width: 100%;
        border-collapse: separate;
        border-spacing: 0;
    }
    .projection-table thead tr.group-row th {
        background: linear-gradient(180deg, #EEF5FB 0%, #E2EDF8 100%);
        color: #46627F;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-align: center;
        padding: 0.72rem 0.9rem;
        border-bottom: 1px solid #D8E2EE;
        border-right: 1px solid #D8E2EE;
        white-space: nowrap;
    }
    .projection-table thead tr.column-row th {
        background: #F8FBFF;
        color: #35506E;
        font-size: 0.88rem;
        font-weight: 800;
        text-align: center;
        padding: 0.9rem 0.85rem 0.85rem 0.85rem;
        border-bottom: 1px solid #D8E2EE;
        border-right: 1px solid #E2E8F0;
        vertical-align: bottom;
        white-space: nowrap;
    }
    .projection-table thead tr.column-row th.is-single-line {
        vertical-align: middle;
    }
    .projection-table thead th .th-title {
        display: block;
        line-height: 1.1;
    }
    .projection-table thead th .th-sub {
        display: block;
        margin-top: 0.18rem;
        color: #64748B;
        font-size: 0.72rem;
        font-weight: 700;
        line-height: 1.1;
    }
    .projection-table thead th .th-sub.is-continuation {
        margin-top: 0.12rem;
        color: inherit;
        font-size: inherit;
        font-weight: inherit;
    }
    .projection-table tbody th,
    .projection-table tbody td {
        background: #FFFFFF;
        color: #0F172A;
        font-size: 0.98rem;
        padding: 0.82rem 0.9rem;
        border-bottom: 1px solid #E2E8F0;
        border-right: 1px solid #E2E8F0;
        white-space: nowrap;
    }
    .projection-table tbody tr:nth-child(even) th,
    .projection-table tbody tr:nth-child(even) td {
        background: #FCFDFE;
    }
    .projection-table tbody tr.is-year0 th,
    .projection-table tbody tr.is-year0 td {
        background: #FFF8ED;
    }
    .projection-table tbody tr.is-year10 th,
    .projection-table tbody tr.is-year10 td {
        background: #F3FBF5;
    }
    .projection-table tbody tr:hover th,
    .projection-table tbody tr:hover td {
        background: #F8FBFF;
    }
    .projection-table th.is-sticky,
    .projection-table td.is-sticky {
        position: sticky;
        left: 0;
        z-index: 3;
        box-shadow: 1px 0 0 #E2E8F0;
    }
    .projection-table thead th.is-sticky {
        z-index: 5;
    }
    .projection-table tbody th.is-year {
        min-width: 72px;
        text-align: center;
        color: #002A54;
        font-weight: 900;
    }
    .projection-table td.is-money {
        text-align: right;
        font-variant-numeric: tabular-nums;
    }
    .projection-table td.is-empty {
        color: #94A3B8;
        text-align: center;
        font-weight: 700;
    }
    .projection-table td.is-positive {
        color: #166534;
        font-weight: 800;
    }
    .projection-table td.is-negative {
        color: #B91C1C;
        font-weight: 800;
    }
    .projection-table td.is-sale {
        color: #92400E;
        font-weight: 900;
        background: linear-gradient(180deg, #FFFDF4 0%, #FFF7D6 100%);
    }
    .projection-table td.is-strong {
        font-weight: 900;
    }
    .projection-table tr > *:last-child {
        border-right: none;
    }
    .projection-table tbody tr:last-child > * {
        border-bottom: none;
    }
    div[data-testid="stDialog"] div[role="dialog"],
    div[data-testid="stDialog"] section[role="dialog"] {
        width: min(96vw, 1760px) !important;
    }
    div[data-testid="stDialog"] .projection-table-shell {
        margin-bottom: 0;
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


def decision_meter_html(verdict_value, variant="neutral"):
    pointer_positions = {
        "negative": 16,
        "warning": 50,
        "positive": 84,
        "neutral": 50,
    }
    zone_labels = {
        "negative": "Pas un bon achat",
        "warning": "Sous conditions",
        "positive": "Bon achat",
        "neutral": "A analyser",
    }

    pointer_position = pointer_positions.get(variant, 50)
    current_zone = zone_labels.get(variant, "A analyser")

    return (
        f'<div class="decision-meter-shell {variant}">'
        f'<div class="decision-meter-header">'
        f'<div class="decision-meter-kicker">Lecture visuelle</div>'
        f'<div class="decision-meter-title">Positionnement rapide de l\'immeuble</div>'
        f'</div>'
        f'<div class="decision-meter">'
        f'<div class="decision-meter-arrow" style="left:{pointer_position}%;">'
        f'<div class="decision-meter-badge">{escape(current_zone)}</div>'
        f'<div class="decision-meter-arrow-line"></div>'
        f'<div class="decision-meter-arrow-head"></div>'
        f'</div>'
        f'<div class="decision-meter-track">'
        f'<div class="decision-meter-segment negative">Pas un bon achat</div>'
        f'<div class="decision-meter-segment warning">Sous conditions</div>'
        f'<div class="decision-meter-segment positive">Bon achat</div>'
        f'</div>'
        f'</div>'
        f'<div class="decision-meter-caption">Verdict actuel : <strong>{escape(verdict_value)}</strong></div>'
        f'</div>'
    )


def ai_summary_banner_html(provider, model, summary):
    provider_label = provider or "Gemini"
    model_label = model or "modele non precise"
    summary_text = summary or "Lecture IA disponible pour completer l'analyse locale."
    return (
        '<div class="ai-insight-shell">'
        '<div class="ai-insight-header">'
        '<div>'
        '<div class="ai-insight-kicker">Lecture complementaire</div>'
        '<div class="ai-insight-title">Lecture IA Gemini</div>'
        '</div>'
        f'<div class="ai-insight-pill">{escape(provider_label)} | {escape(model_label)}</div>'
        '</div>'
        '<div class="ai-insight-summary">'
        '<div class="ai-insight-summary-label">Synthese Gemini</div>'
        f'<div class="ai-insight-summary-text">{escape(summary_text)}</div>'
        '</div>'
        '</div>'
    )


def ai_list_card_html(title, items, variant="neutral", empty_message="Aucun point n'a ete remonte."):
    if items:
        list_items = "".join(f"<li>{escape(item)}</li>" for item in items)
        body = f"<ul>{list_items}</ul>"
    else:
        body = f'<div class="empty">{escape(empty_message)}</div>'

    return (
        f'<div class="ai-list-card {variant}">'
        f'<div class="title">{escape(title)}</div>'
        f"{body}"
        '</div>'
    )


def ai_detail_card_html(title, body, variant="neutral", eyebrow=None):
    eyebrow_html = (
        f'<div class="eyebrow">{escape(eyebrow)}</div>'
        if eyebrow
        else ""
    )
    return (
        f'<div class="ai-detail-card {variant}">'
        f"{eyebrow_html}"
        f'<div class="title">{escape(title)}</div>'
        f'<div class="body">{escape(body)}</div>'
        '</div>'
    )


def render_action_cards(actions):
    action_rows = [actions[:2], actions[2:]]
    for action_row in action_rows:
        if not action_row:
            continue
        action_cols = st.columns(2, gap="large")
        for col, action in zip(action_cols, action_row):
            with col:
                st.markdown(
                    decision_card_html(
                        action["label"],
                        action["value"],
                        action["note"],
                        action["variant"],
                    ),
                    unsafe_allow_html=True,
                )


def normalize_text_block(text):
    return " ".join((text or "").replace("\n", " ").split())


def excerpt_sentences(text, max_sentences=2):
    cleaned = normalize_text_block(text)
    if not cleaned:
        return ""

    parts = []
    for chunk in cleaned.split(". "):
        piece = chunk.strip()
        if not piece:
            continue
        if piece[-1] not in ".!?":
            piece = f"{piece}."
        parts.append(piece)
        if len(parts) >= max_sentences:
            break
    return " ".join(parts) if parts else cleaned


def verdict_presentation(variant, fallback_value=""):
    mapping = {
        "positive": {
            "title": "Achat recommande",
            "risk": "Risque faible",
            "badge": "Lecture favorable",
        },
        "warning": {
            "title": "Achetable sous conditions",
            "risk": "Risque modere",
            "badge": "Sous conditions",
        },
        "negative": {
            "title": "A renegocier",
            "risk": "Risque eleve",
            "badge": "Point de rupture",
        },
        "neutral": {
            "title": fallback_value or "A analyser",
            "risk": "Risque a confirmer",
            "badge": "Analyse en cours",
        },
    }
    meta = mapping.get(variant, mapping["neutral"]).copy()
    if fallback_value and variant in {"warning", "negative"}:
        meta["title"] = fallback_value
    return meta


def verdict_positioning_meta(variant):
    mapping = {
        "positive": {
            "position_pct": 74,
            "caption": "Le dossier se place dans une zone d'achat defendable aux conditions actuelles.",
            "active_scale": "positive",
        },
        "warning": {
            "position_pct": 48,
            "caption": "Le dossier reste envisageable, mais avec des ajustements avant de s'engager.",
            "active_scale": "warning",
        },
        "negative": {
            "position_pct": 22,
            "caption": "Le dossier reste trop loin d'une zone d'achat confortable au prix actuel.",
            "active_scale": "negative",
        },
        "neutral": {
            "position_pct": 34,
            "caption": "Le positionnement reste a confirmer avant de se prononcer definitivement.",
            "active_scale": "neutral",
        },
    }
    return mapping.get(variant, mapping["neutral"])


def format_diagnostic_value(value, kind):
    if value is None:
        return "N/A"
    if kind == "money":
        return format_money(value)
    if kind == "money_year":
        formatted = format_money(abs(value))
        return f"-{formatted}/an" if value < 0 else f"{formatted}/an"
    if kind == "pct":
        return f"{value:.2f} %"
    if kind == "multiple":
        return f"{value:.2f}x"
    return str(value)


def build_diagnostic_sections(ratios, analyse_locale, cashflow_annuel):
    review_map = analyse_locale.get("ratio_reviews", {})
    positive = []
    vigilance = []

    def maybe_add(entries, key, label, kind, tone_filter):
        review = review_map.get(key)
        value = ratios.get(key)
        if not review or value is None:
            return
        status = review.get("status", "neutral")
        if status not in tone_filter:
            return
        entries.append(
            {
                "tone": "positive" if status == "positive" else ("negative" if status == "negative" else "warning"),
                "label": label,
                "value": format_diagnostic_value(value, kind),
                "note": excerpt_sentences(review.get("interpretation", review.get("headline", "")), 1),
            }
        )

    for key, label, kind in [
        ("cap_rate", "Cap rate", "pct"),
        ("tri", "TRI", "pct"),
        ("van", "VAN", "money"),
        ("cash_on_cash", "Cash-on-cash", "pct"),
    ]:
        maybe_add(positive, key, label, kind, {"positive"})

    if cashflow_annuel >= 0:
        positive.append(
            {
                "tone": "positive",
                "label": "Cashflow",
                "value": format_diagnostic_value(cashflow_annuel, "money_year"),
                "note": "Le projet degage encore un surplus annuel apres service de la dette.",
            }
        )

    for key, label, kind in [
        ("csd", "CSD", "multiple"),
        ("cash_on_cash", "Cash-on-cash", "pct"),
        ("mrb", "MRB", "multiple"),
        ("cap_rate", "Cap rate", "pct"),
        ("tri", "TRI", "pct"),
        ("van", "VAN", "money"),
    ]:
        maybe_add(vigilance, key, label, kind, {"warning", "negative"})

    if cashflow_annuel < 0:
        vigilance.insert(
            1 if vigilance else 0,
            {
                "tone": "negative",
                "label": "Cashflow",
                "value": format_diagnostic_value(cashflow_annuel, "money_year"),
                "note": "Le dossier demande encore un effort investisseur apres le service de la dette.",
            },
        )

    return positive[:4], vigilance[:4]


def ai_block_heading_html(kicker, title, caption=""):
    kicker_html = (
        f'<div class="ai-block-kicker">{escape(kicker)}</div>'
        if kicker
        else ""
    )
    caption_html = (
        f'<div class="ai-block-caption">{escape(caption)}</div>'
        if caption
        else ""
    )
    return (
        '<div class="ai-block-heading">'
        f"{kicker_html}"
        f'<div class="ai-block-title">{escape(title)}</div>'
        f"{caption_html}"
        '</div>'
    )


def ai_summary_compact_html(summary_text, thesis_text):
    return (
        '<div class="ai-summary-card">'
        '<div class="ai-summary-subtitle">Resume rapide de l\'analyse</div>'
        f'<div class="ai-summary-text">{escape(summary_text)}</div>'
        '<div class="ai-thesis-row">'
        '<div class="ai-thesis-label">These retenue</div>'
        f'<div class="ai-thesis-value">{escape(thesis_text)}</div>'
        '</div>'
        '</div>'
    )


def ai_verdict_compact_html(title, variant, badge_label, risk_label, reason_text):
    position_meta = verdict_positioning_meta(variant)
    scale_labels = [
        ("Fragile", "negative"),
        ("Sous conditions", "warning"),
        ("Favorable", "positive"),
    ]
    scale_html = "".join(
        (
            f'<div class="ai-verdict-scale-label {tone}'
            f'{" active" if position_meta["active_scale"] == tone else ""}">{escape(label)}</div>'
        )
        for label, tone in scale_labels
    )
    building_windows = "".join("<span></span>" for _ in range(6))
    return (
        f'<div class="ai-verdict-card {variant}">'
        '<div class="ai-verdict-layout">'
        '<div class="ai-verdict-copy">'
        '<div class="ai-verdict-head">'
        '<div>'
        '<div class="ai-verdict-kicker">Verdict final</div>'
        f'<div class="ai-verdict-title">{escape(title)}</div>'
        '</div>'
        '<div class="ai-verdict-badges">'
        f'<div class="ai-verdict-pill {variant}">{escape(badge_label)}</div>'
        f'<div class="ai-verdict-pill {variant}">{escape(risk_label)}</div>'
        '</div>'
        '</div>'
        f'<div class="ai-verdict-reason">{escape(reason_text)}</div>'
        '</div>'
        f'<div class="ai-verdict-visual {variant}">'
        '<div class="ai-verdict-visual-label">Positionnement</div>'
        '<div class="ai-verdict-approach">'
        '<div class="ai-verdict-track-shell">'
        '<div class="ai-verdict-lane"></div>'
        f'<div class="ai-verdict-pointer {variant}" style="left: {position_meta["position_pct"]}%;">'
        '<div class="ai-verdict-pointer-tag">Notre position</div>'
        '<div class="ai-verdict-pointer-arrow">&#8595;</div>'
        '</div>'
        '</div>'
        '<div class="ai-verdict-building">'
        '<div class="ai-verdict-building-body">'
        f'{building_windows}'
        '<div class="ai-verdict-building-door"></div>'
        '</div>'
        '<div class="ai-verdict-building-label">Immeuble cible</div>'
        '</div>'
        '</div>'
        f'<div class="ai-verdict-scale-line">{scale_html}</div>'
        f'<div class="ai-verdict-visual-caption">{escape(position_meta["caption"])}</div>'
        '</div>'
        '</div>'
    )


def ai_verdict_flow_html(title, variant, badge_label, risk_label, reason_text, flow_text):
    return ai_verdict_compact_html(title, variant, badge_label, risk_label, reason_text)


def ai_diagnostic_card_html(title, subtitle, items, tone, empty_message):
    if items:
        rows_html = "".join(
            (
                f'<div class="ai-metric-row {item["tone"]}">'
                '<div class="ai-metric-icon"></div>'
                '<div class="ai-metric-content">'
                '<div class="ai-metric-line">'
                f'<div class="ai-metric-name">{escape(item["label"])}</div>'
                f'<div class="ai-metric-value">{escape(item["value"])}</div>'
                '</div>'
                f'<div class="ai-metric-note">{escape(item["note"])}</div>'
                '</div>'
                '</div>'
            )
            for item in items
        )
    else:
        rows_html = f'<div class="ai-metric-empty">{escape(empty_message)}</div>'

    return (
        f'<div class="ai-diagnostic-card {tone}">'
        f'<div class="title">{escape(title)}</div>'
        f'<div class="subtitle">{escape(subtitle)}</div>'
        f"{rows_html}"
        '</div>'
    )


def merge_action_plans(local_actions, ai_actions):
    preferred_order = ["counter_offer", "down_payment", "rent_optimization"]
    local_by_key = {action.get("action_key"): action for action in local_actions}
    ai_by_key = {action.get("action_key"): action for action in ai_actions}
    merged = []

    for key in preferred_order:
        local_action = local_by_key.get(key)
        if not local_action:
            continue
        ai_action = ai_by_key.get(key, {})
        merged_action = dict(local_action)
        if ai_action.get("note"):
            merged_action["note"] = ai_action["note"]
        if ai_action.get("variant"):
            merged_action["variant"] = ai_action["variant"]
        merged_action["source"] = "ai" if ai_action else "rules"
        merged.append(merged_action)

    return merged


def action_state_label(action):
    state = action.get("state", "active")
    if state == "optional":
        return "Levier secondaire"
    if state == "unavailable":
        return "Scenario non calculable"
    return "Levier actif"


def render_premium_action_cards(actions):
    if not actions:
        return

    primary_row = actions[:2]
    secondary_row = actions[2:]

    for row_index, action_row in enumerate([primary_row, secondary_row]):
        if not action_row:
            continue
        if row_index == 0:
            cols = st.columns(2, gap="large")
        else:
            cols = [st.container()]

        for col, action in zip(cols, action_row):
            with col:
                meta_html = (
                    '<div class="ai-plan-meta">'
                    f'<div class="ai-plan-chip">Impact : {escape(action.get("impact_label", "N/A"))}</div>'
                    f'<div class="ai-plan-chip">Faisabilite : {escape(action.get("feasibility_label", "N/A"))}</div>'
                    '</div>'
                )
                card_html = (
                    f'<div class="ai-plan-card {action.get("variant", "neutral")}">'
                    '<div class="ai-plan-top">'
                    f'<div class="ai-plan-rank">{escape(str(action.get("priority_rank", "")))}</div>'
                    f'<div class="ai-plan-priority">{escape(action.get("priority_label", ""))}</div>'
                    '</div>'
                    f'<div class="ai-plan-title">{escape(action.get("label", ""))}</div>'
                    f'<div class="ai-plan-value">{escape(action.get("value", ""))}</div>'
                    f'<div class="ai-plan-state">{escape(action_state_label(action))}</div>'
                    f"{meta_html}"
                    f'<div class="ai-plan-note">{escape(excerpt_sentences(action.get("note", ""), 2))}</div>'
                    '</div>'
                )
                st.markdown(card_html, unsafe_allow_html=True)


def select_primary_action(actions):
    for action in actions:
        if action.get("state") == "active":
            return action
    return None


def scenario_preview_html(action):
    if not action:
        return ""

    preview = action.get("scenario_preview", {})
    metric_defs = [
        ("cap_rate", "Cap rate estime", "pct"),
        ("csd", "CSD estime", "multiple"),
        ("cashflow_annuel", "Cashflow estime", "money_year"),
        ("rne", "RNE estime", "money"),
    ]
    metric_cards = []
    for key, label, kind in metric_defs:
        value = preview.get(key)
        if value is None:
            continue
        metric_cards.append(
            '<div class="ai-preview-metric">'
            f'<div class="ai-preview-metric-label">{escape(label)}</div>'
            f'<div class="ai-preview-metric-value">{escape(format_diagnostic_value(value, kind))}</div>'
            '</div>'
        )

    if not metric_cards:
        return ""

    note = (
        "Effet estime sur les indicateurs cles si cette action est appliquee avec les hypotheses actuelles."
        if action.get("state") == "active"
        else "Vue de controle avec les hypotheses actuelles du dossier."
    )

    return (
        '<div class="ai-preview-shell">'
        '<div class="ai-preview-kicker">Scenario apres ajustement</div>'
        f'<div class="ai-preview-title">{escape(action.get("scenario_title", "Scenario estime"))}</div>'
        f'<div class="ai-preview-note">{escape(note)}</div>'
        f'<div class="ai-preview-grid">{"".join(metric_cards)}</div>'
        '</div>'
    )


def render_table_fullscreen_button(button_key, help_text):
    action_col, _ = st.columns([0.07, 0.93], gap="small")
    with action_col:
        return st.button(
            "⛶",
            key=button_key,
            help=help_text,
            type="secondary",
            use_container_width=False,
        )


def render_grouped_financial_table(
    df_numeric,
    df_display,
    column_specs,
    cell_class_getter,
    row_class_getter=None,
    table_anchor_id="financial-table-anchor",
    enable_hover_action=True,
):
    grouped_headers = []
    for spec in column_specs[1:]:
        if not grouped_headers or grouped_headers[-1]["label"] != spec["group"]:
            grouped_headers.append({"label": spec["group"], "colspan": 1})
        else:
            grouped_headers[-1]["colspan"] += 1

    group_header_html = ''.join(
        f'<th colspan="{group["colspan"]}">{escape(group["label"])}</th>'
        for group in grouped_headers
    )

    column_header_parts = []
    for spec in column_specs[1:]:
        header_class = "is-single-line" if not spec["subtitle"] else ""
        subtitle_class = "th-sub"
        if spec.get("subtitle_variant") == "continuation":
            subtitle_class += " is-continuation"
        subtitle_html = (
            f'<span class="{subtitle_class}">{escape(spec["subtitle"])}</span>'
            if spec["subtitle"]
            else ""
        )
        column_header_parts.append(
            f'<th class="{header_class}"><span class="th-title">{escape(spec["title"])}</span>{subtitle_html}</th>'
        )
    column_header_html = ''.join(column_header_parts)

    row_html = []
    for row_index in range(len(df_numeric)):
        numeric_row = df_numeric.iloc[row_index]
        display_row = df_display.iloc[row_index]
        row_classes = row_class_getter(row_index, numeric_row, display_row) if row_class_getter else []

        cells = []
        for spec in column_specs:
            cell_value = display_row[spec["key"]]
            cell_classes = []

            if spec["kind"] == "year":
                cell_classes.extend(["is-year", "is-sticky"])
                cells.append(
                    f'<th scope="row" class="{" ".join(cell_classes)}">{escape(str(cell_value))}</th>'
                )
                continue

            raw_value = float(numeric_row[spec["key"]])
            cell_classes.append("is-money")
            cell_classes.extend(cell_class_getter(spec, raw_value, numeric_row, display_row))

            cells.append(
                f'<td class="{" ".join(cell_classes)}">{escape(str(cell_value))}</td>'
            )

        row_html.append(
            f'<tr class="{" ".join(row_classes)}">{"".join(cells)}</tr>'
        )

    shell_classes = ["projection-table-shell"]
    if enable_hover_action:
        shell_classes.append("with-trigger")

    table_html = ''.join(
        [
            f'<div id="{table_anchor_id}" class="{" ".join(shell_classes)}">',
            '<div class="projection-table-scroll">',
            '<table class="projection-table">',
            '<thead>',
            '<tr class="group-row">',
            '<th class="is-sticky" rowspan="2">Annee</th>',
            group_header_html,
            '</tr>',
            f'<tr class="column-row">{column_header_html}</tr>',
            '</thead>',
            f'<tbody>{"".join(row_html)}</tbody>',
            '</table>',
            '</div>',
            '</div>',
        ]
    )
    st.markdown(table_html, unsafe_allow_html=True)


def render_projection_table(df_numeric, df_display, enable_hover_action=True):
    open_fullscreen_dialog = False
    if enable_hover_action:
        open_fullscreen_dialog = render_table_fullscreen_button(
            "projection_table_fullscreen_button",
            "Ouvrir le tableau de projection en plein ecran",
        )

    column_specs = [
        {"key": "Annee", "title": "Annee", "subtitle": "", "subtitle_variant": "detail", "group": None, "kind": "year", "sticky": True},
        {"key": "Mise de fonds", "title": "Mise de", "subtitle": "fonds", "subtitle_variant": "continuation", "group": "Apport initial", "kind": "money"},
        {"key": "Frais d'acquisition", "title": "Frais d'", "subtitle": "acquisition", "subtitle_variant": "continuation", "group": "Apport initial", "kind": "money"},
        {"key": "RNE", "title": "RNE", "subtitle": "annuel", "subtitle_variant": "continuation", "group": "Exploitation", "kind": "money"},
        {"key": "Interets", "title": "Interets", "subtitle": "hypothecaires", "subtitle_variant": "continuation", "group": "Exploitation", "kind": "money"},
        {"key": "Capital rembourse", "title": "Capital", "subtitle": "rembourse", "subtitle_variant": "continuation", "group": "Exploitation", "kind": "money"},
        {"key": "Cash flow avant impot", "title": "Cash flow", "subtitle": "avant impot", "subtitle_variant": "continuation", "group": "Exploitation", "kind": "money"},
        {"key": "Impot estime", "title": "Impot", "subtitle": "estime", "subtitle_variant": "continuation", "group": "Fiscalite", "kind": "money"},
        {"key": "Cash flow apres impot", "title": "Cash flow", "subtitle": "apres impot", "subtitle_variant": "continuation", "group": "Fiscalite", "kind": "money"},
        {"key": "Produit de vente estime", "title": "Produit de", "subtitle": "vente estime", "subtitle_variant": "continuation", "group": "Sortie", "kind": "money"},
        {"key": "Flux total (TRI)", "title": "Flux total", "subtitle": "", "subtitle_variant": "detail", "group": "Sortie", "kind": "money"},
    ]

    positive_negative_columns = {
        "Cash flow avant impot",
        "Cash flow apres impot",
        "Flux total (TRI)",
    }

    def projection_row_classes(row_index, numeric_row, display_row):
        year_value = str(display_row["Annee"])
        row_classes = []
        if year_value == "0":
            row_classes.append("is-year0")
        if year_value == "10":
            row_classes.append("is-year10")
        return row_classes

    def projection_cell_classes(spec, raw_value, numeric_row, display_row):
        cell_classes = []
        if abs(raw_value) < 0.005 and spec["key"] != "Flux total (TRI)":
            cell_classes.append("is-empty")
        if spec["key"] in positive_negative_columns:
            if raw_value > 0.005:
                cell_classes.append("is-positive")
            elif raw_value < -0.005:
                cell_classes.append("is-negative")
        if spec["key"] == "Impot estime" and raw_value < -0.005:
            cell_classes.append("is-positive")
        if spec["key"] == "Produit de vente estime" and raw_value > 0.005:
            cell_classes.append("is-sale")
        if spec["key"] == "Flux total (TRI)":
            cell_classes.append("is-strong")
        return cell_classes

    render_grouped_financial_table(
        df_numeric,
        df_display,
        column_specs,
        projection_cell_classes,
        row_class_getter=projection_row_classes,
        table_anchor_id="projection-table-anchor",
        enable_hover_action=enable_hover_action,
    )

    if open_fullscreen_dialog:
        show_projection_table_dialog(df_numeric, df_display)


@st.dialog("Projection 10 ans - tableau plein ecran", width="large")
def show_projection_table_dialog(df_numeric, df_display):
    st.caption("Vue agrandie du tableau detaille de projection.")
    render_projection_table(df_numeric, df_display, enable_hover_action=False)


@st.dialog("Amortissement du pret - tableau plein ecran", width="large")
def show_amortization_table_dialog(df_numeric, df_display):
    st.caption("Vue agrandie du tableau d'amortissement du pret.")
    render_amortization_table(df_numeric, df_display, enable_hover_action=False)


def render_amortization_table(df_numeric, df_display, enable_hover_action=True):
    open_fullscreen_dialog = False
    if enable_hover_action:
        open_fullscreen_dialog = render_table_fullscreen_button(
            "amortization_table_fullscreen_button",
            "Ouvrir le tableau d'amortissement en plein ecran",
        )

    column_specs = [
        {"key": "Annee", "title": "Annee", "subtitle": "", "subtitle_variant": "detail", "group": None, "kind": "year", "sticky": True},
        {"key": "Solde debut", "title": "Solde", "subtitle": "debut", "subtitle_variant": "continuation", "group": "Ouverture", "kind": "money"},
        {"key": "Paiement annuel", "title": "Paiement", "subtitle": "annuel", "subtitle_variant": "continuation", "group": "Paiement", "kind": "money"},
        {"key": "Interets", "title": "Interets", "subtitle": "", "subtitle_variant": "detail", "group": "Paiement", "kind": "money"},
        {"key": "Capital rembourse", "title": "Capital", "subtitle": "rembourse", "subtitle_variant": "continuation", "group": "Paiement", "kind": "money"},
        {"key": "Solde fin", "title": "Solde", "subtitle": "fin", "subtitle_variant": "continuation", "group": "Cloture", "kind": "money"},
    ]

    def amortization_row_classes(row_index, numeric_row, display_row):
        row_classes = []
        if row_index == len(df_numeric) - 1 or abs(float(numeric_row["Solde fin"])) < 0.005:
            row_classes.append("is-year10")
        return row_classes

    def amortization_cell_classes(spec, raw_value, numeric_row, display_row):
        cell_classes = []
        if abs(raw_value) < 0.005:
            cell_classes.append("is-empty")
        if spec["key"] == "Capital rembourse" and raw_value > 0.005:
            cell_classes.append("is-positive")
        if spec["key"] == "Interets" and raw_value > 0.005:
            cell_classes.append("is-negative")
        if spec["key"] in {"Solde debut", "Solde fin"}:
            cell_classes.append("is-strong")
        return cell_classes

    render_grouped_financial_table(
        df_numeric,
        df_display,
        column_specs,
        amortization_cell_classes,
        row_class_getter=amortization_row_classes,
        table_anchor_id="amortization-table-anchor",
        enable_hover_action=enable_hover_action,
    )

    if open_fullscreen_dialog:
        show_amortization_table_dialog(df_numeric, df_display)


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
resultats["cashflow_net_annee1"] = resultats["cashflow_avant_frais"]

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
                    hole=0.66,
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
                    text="Total annuel",
                    x=0.5,
                    y=0.54,
                    font=dict(size=13, color="#64748B"),
                    xanchor="center",
                    yanchor="middle",
                    showarrow=False,
                    align="center",
                ),
                dict(
                    text=f"<b>{format_money(dep_df['montant'].sum())}</b>",
                    x=0.5,
                    y=0.47,
                    font=dict(size=26, color="#002A54"),
                    xanchor="center",
                    yanchor="middle",
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
    investissement_initial = projection.get(
        "investissement_initial",
        resultats["mise_de_fonds"] + resultats["frais_acquisition"],
    )
    produit_vente_an10 = float(df_proj["produit_vente_estime"].iloc[-1]) if not df_proj.empty else 0.0
    cashflow_cumule_apres_impot = (
        float(df_proj["cashflow_cumule_apres_impot"].iloc[-1]) if not df_proj.empty else 0.0
    )
    valeur_immeuble_an10 = float(df_proj["valeur_immeuble"].iloc[-1]) if not df_proj.empty else 0.0
    solde_pret_an10 = float(df_proj["solde_pret"].iloc[-1]) if not df_proj.empty else 0.0
    annee_cashflow_positif = None
    if not df_proj.empty:
        annees_cashflow_positif = df_proj.loc[df_proj["cashflow_apres_impot"] >= 0, "annee"]
        if not annees_cashflow_positif.empty:
            annee_cashflow_positif = int(annees_cashflow_positif.iloc[0])

    projection_card_specs = [
        (
            "Produit vente an 10",
            format_money(produit_vente_an10),
            f"Valeur projetee {format_money(valeur_immeuble_an10)} moins solde du financement {format_money(solde_pret_an10)}.",
            "positive",
        ),
        (
            "Cash flow cumule",
            format_money(cashflow_cumule_apres_impot),
            "Somme des cash flows apres impot sur 10 ans, hors revente.",
            "positive" if cashflow_cumule_apres_impot >= 0 else "negative",
        ),
        (
            "Solde pret an 10",
            format_money(solde_pret_an10),
            "Montant d'hypotheque restant a rembourser apres 10 ans.",
            "neutral",
        ),
        (
            "Cash flow positif",
            f"Annee {annee_cashflow_positif}" if annee_cashflow_positif else "Jamais",
            (
                "Premiere annee ou le cash flow apres impot devient positif."
                if annee_cashflow_positif
                else "Le cash flow apres impot reste negatif sur les 10 ans."
            ),
            "positive" if annee_cashflow_positif else "warning",
        ),
    ]
    projection_card_rows = [projection_card_specs[:2], projection_card_specs[2:]]
    for card_row in projection_card_rows:
        row_columns = st.columns(2, gap="large")
        for column, (label, value, note, variant) in zip(row_columns, card_row):
            with column:
                st.markdown(
                    decision_card_html(label, value, note, variant),
                    unsafe_allow_html=True,
                )

    def projection_money(value, blank_zero=False):
        if blank_zero and abs(value) < 0.005:
            return "—"
        return format_money(value)

    projection_rows = [
        {
            "Annee": "0",
            "Mise de fonds": resultats["mise_de_fonds"],
            "Frais d'acquisition": resultats["frais_acquisition"],
            "RNE": 0.0,
            "Interets": 0.0,
            "Capital rembourse": 0.0,
            "Cash flow avant impot": 0.0,
            "Impot estime": 0.0,
            "Cash flow apres impot": 0.0,
            "Produit de vente estime": 0.0,
            "Flux total (TRI)": -investissement_initial,
        }
    ]

    for row in projection["annees"]:
        projection_rows.append(
            {
                "Annee": str(int(row["annee"])),
                "Mise de fonds": 0.0,
                "Frais d'acquisition": 0.0,
                "RNE": row["rne"],
                "Interets": row["interet"],
                "Capital rembourse": row["capital"],
                "Cash flow avant impot": row["cashflow_avant_impot"],
                "Impot estime": row["impot"],
                "Cash flow apres impot": row["cashflow_apres_impot"],
                "Produit de vente estime": row["produit_vente_estime"],
                "Flux total (TRI)": row["flux_total_tri"],
            }
        )

    df_projection = pd.DataFrame(projection_rows)
    projection_money_columns = [col for col in df_projection.columns if col != "Annee"]
    df_projection_display = df_projection.copy()
    for col in projection_money_columns:
        df_projection_display[col] = df_projection_display[col].apply(
            lambda value: projection_money(value, blank_zero=(col != "Flux total (TRI)"))
        )

    render_projection_table(df_projection, df_projection_display)

    st.divider()

    g1, g2 = st.columns(2, gap="large")

    with g1:
        fig_flux = go.Figure()
        fig_flux.add_trace(
            go.Bar(
                x=df_proj["annee"],
                y=df_proj["cashflow_avant_impot"],
                name="Avant impot",
                marker_color="#94A3B8",
                hovertemplate="Annee %{x}<br>Avant impot: %{y:,.0f}$<extra></extra>",
            )
        )
        fig_flux.add_trace(
            go.Bar(
                x=df_proj["annee"],
                y=df_proj["cashflow_apres_impot"],
                name="Apres impot",
                marker_color=["#16A34A" if v >= 0 else "#DC2626" for v in df_proj["cashflow_apres_impot"]],
                hovertemplate="Annee %{x}<br>Apres impot: %{y:,.0f}$<extra></extra>",
            )
        )
        fig_flux.update_layout(
            title="Cash flow annuel",
            barmode="group",
            xaxis_title="Annee",
            yaxis_title="$",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155"),
            height=390,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(gridcolor="rgba(148, 163, 184, 0.22)"),
        )
        st.plotly_chart(fig_flux, use_container_width=True)

    with g2:
        fig_val = go.Figure()
        annee_finale = int(df_proj["annee"].iloc[-1])
        produit_mid_an10 = (valeur_immeuble_an10 + solde_pret_an10) / 2
        fig_val.add_trace(
            go.Scatter(
                x=df_proj["annee"],
                y=df_proj["valeur_immeuble"],
                name="Valeur projetee",
                line=dict(color="#005A9C", width=3),
                mode="lines+markers",
                marker=dict(size=7, color="#005A9C"),
                hovertemplate="Annee %{x}<br>Valeur: %{y:,.0f}$<extra></extra>",
            )
        )
        fig_val.add_trace(
            go.Scatter(
                x=df_proj["annee"],
                y=df_proj["solde_pret"],
                name="Solde du financement",
                line=dict(color="#94A3B8", width=3),
                mode="lines+markers",
                marker=dict(size=7, color="#94A3B8"),
                fill="tonexty",
                fillcolor="rgba(245, 158, 11, 0.12)",
                hovertemplate="Annee %{x}<br>Solde financement: %{y:,.0f}$<extra></extra>",
            )
        )
        fig_val.add_trace(
            go.Scatter(
                x=[annee_finale, annee_finale],
                y=[solde_pret_an10, valeur_immeuble_an10],
                mode="lines",
                line=dict(color="#F59E0B", width=2, dash="dot"),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig_val.add_annotation(
            x=annee_finale,
            y=produit_mid_an10,
            text=f"Produit vente an 10<br>{format_money(produit_vente_an10)}",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowcolor="#F59E0B",
            bgcolor="#FFFFFF",
            bordercolor="#FCD34D",
            font=dict(color="#92400E", size=12),
            ax=70,
            ay=0,
        )
        fig_val.update_layout(
            title="Valeur projetee et solde du financement",
            xaxis_title="Annee",
            yaxis_title="$",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#334155"),
            height=390,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            yaxis=dict(gridcolor="rgba(148, 163, 184, 0.22)"),
        )
        st.plotly_chart(fig_val, use_container_width=True)

    st.divider()
    custom_subheader("Amortissement du pret")

    df_amort = df_proj[
        ["annee", "solde_debut", "paiement_hypo", "interet", "capital", "solde_pret"]
    ].copy()
    df_amort.columns = [
        "Annee",
        "Solde debut",
        "Paiement annuel",
        "Interets",
        "Capital rembourse",
        "Solde fin",
    ]
    df_amort_display = df_amort.copy()
    for col in df_amort_display.columns[1:]:
        df_amort_display[col] = df_amort_display[col].apply(format_money)
    render_amortization_table(df_amort, df_amort_display)

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
    verdict_banner_slot = st.empty()
    custom_subheader("🎯 Ratios financiers")

    analyse_investissement_locale = analyser_opportunite_investissement(
        ratios=ratios,
        prix_achat=prix_achat,
        rne=resultats["rne"],
        revenus_bruts_annuels=resultats["revenus_bruts_annuels"],
        depenses_totales=resultats["depenses_totales"],
        paiement_annuel=resultats["paiement_annuel"],
        montant_pret=resultats["montant_pret"],
        mise_de_fonds=resultats["mise_de_fonds"],
        frais_acquisition=resultats["frais_acquisition"],
        cashflow_annuel=resultats["cashflow_avant_frais"],
        loyers_mensuels_total=loyers_mensuels_total,
        nb_logements=nb_logements,
        taux_vacance=taux_vacance,
    )

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

                explication = analyse_investissement_locale["ratio_reviews"][cle]
                status = explication.get("status", "neutral")
                if status == "positive":
                    color = "#16A34A"
                elif status == "warning":
                    color = "#D97706"
                elif status == "negative":
                    color = "#DC2626"
                else:
                    color = "#64748B"

            explication = analyse_investissement_locale["ratio_reviews"][cle]

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
        loyer_equilibre_note += (
            " Seuil minimal: il couvre les depenses et la dette (~CSD 1.00x), "
            "sans marge de securite additionnelle."
        )

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

    recommendation_context = {
        "prix_achat": prix_achat,
        "nb_logements": nb_logements,
        "loyers_mensuels_total": loyers_mensuels_total,
        "taux_vacance_pct": taux_vacance,
        "ratios": ratios,
        "year_one": {
            "rne": resultats["rne"],
            "revenus_bruts_annuels": resultats["revenus_bruts_annuels"],
            "depenses_totales": resultats["depenses_totales"],
            "paiement_annuel": resultats["paiement_annuel"],
            "cashflow_annuel": cashflow_annuel,
            "mise_de_fonds": resultats["mise_de_fonds"],
            "frais_acquisition": resultats["frais_acquisition"],
            "montant_pret": resultats["montant_pret"],
        },
        "decision_support": {
            "loyer_equilibre_mensuel": loyer_equilibre_mensuel,
            "loyer_equilibre_par_logement": loyer_equilibre_par_logement,
            "vacance_max_supportable_pct": vacance_max_brute,
            "apport_initial": apport_initial,
        },
    }
    analyse_investissement_ia = get_recommendation_analysis(
        analyse_investissement_locale,
        recommendation_context,
        AI_RECOMMENDATION_CACHE_VERSION,
    )

    # Recommandation
    st.divider()
    custom_subheader("📝 Recommandation")

    recommendation_source = analyse_investissement_ia.get("recommendation_source", {})
    ai_recommended_actions = analyse_investissement_ia.get("ai_recommended_actions", [])
    ai_mode = recommendation_source.get("mode") == "ai"
    display_analysis = analyse_investissement_ia if ai_mode else analyse_investissement_locale
    display_scenario = display_analysis.get(
        "scenario",
        analyse_investissement_locale.get("scenario", {}),
    )
    display_verdict = display_analysis.get(
        "verdict",
        analyse_investissement_locale.get("verdict", {}),
    )
    verdict_meta = verdict_presentation(
        display_verdict.get("variant", "neutral"),
        display_verdict.get("value", ""),
    )

    summary_text = excerpt_sentences(
        recommendation_source.get("summary")
        or display_scenario.get("summary")
        or display_verdict.get("note"),
        2,
    )
    thesis_summary = excerpt_sentences(display_scenario.get("summary", ""), 1)
    thesis_text = (
        f"{display_scenario.get('label', 'Lecture du dossier')} : {thesis_summary}"
        if thesis_summary
        else display_scenario.get("label", "These non disponible.")
    )
    verdict_reason = excerpt_sentences(display_verdict.get("note", ""), 1)
    verdict_reason = verdict_reason.replace("Scenario:", "").strip()

    verdict_banner_slot.markdown(
        ai_verdict_flow_html(
            verdict_meta["title"],
            display_verdict.get("variant", "neutral"),
            verdict_meta["badge"],
            verdict_meta["risk"],
            verdict_reason or "Lecture de risque non disponible.",
            "Les ratios financiers ci-dessous montrent ce qui soutient ce verdict et ce qui le fragilise.",
        ),
        unsafe_allow_html=True,
    )

    diagnostic_positive, diagnostic_vigilance = build_diagnostic_sections(
        ratios,
        analyse_investissement_locale,
        cashflow_annuel,
    )
    plan_actions = merge_action_plans(
        analyse_investissement_locale["actions"],
        ai_recommended_actions if ai_mode else [],
    )
    primary_action = select_primary_action(plan_actions)

    st.markdown(
        ai_summary_compact_html(
            summary_text or "Aucune synthese courte n'a ete retournee pour ce dossier.",
            thesis_text or "These non disponible.",
        ),
        unsafe_allow_html=True,
    )

    if recommendation_source.get("message") and not ai_mode:
        st.warning(recommendation_source["message"])

    st.markdown(
        ai_block_heading_html(
            "",
            "Forces et points de vigilance",
            "Les indicateurs qui soutiennent le dossier et ceux qui demandent plus de prudence.",
        ),
        unsafe_allow_html=True,
    )

    diagnostic_cols = st.columns(2, gap="large")
    with diagnostic_cols[0]:
        st.markdown(
            ai_diagnostic_card_html(
                "Forces du dossier",
                "Indicateurs qui soutiennent la these d'achat.",
                diagnostic_positive,
                "positive",
                "Aucun point fort majeur n'est mis en evidence avec les seuils actuels.",
            ),
            unsafe_allow_html=True,
        )
    with diagnostic_cols[1]:
        st.markdown(
            ai_diagnostic_card_html(
                "Points de vigilance",
                "Elements qui fragilisent le montage ou la marge de securite.",
                diagnostic_vigilance,
                "warning",
                "Aucun point de vigilance majeur n'est remonte sur les indicateurs principaux.",
            ),
            unsafe_allow_html=True,
        )

    st.markdown(
        ai_block_heading_html(
            "",
            "Actions proposees",
            "Trois leviers concrets pour ameliorer la decision ou securiser le montage.",
        ),
        unsafe_allow_html=True,
    )

    render_premium_action_cards(plan_actions)

    preview_html = scenario_preview_html(primary_action)
    if preview_html:
        st.markdown(preview_html, unsafe_allow_html=True)

    for alert in analyse_investissement_locale["alerts"]:
        if alert["variant"] == "negative":
            st.error(alert["message"])
        elif alert["variant"] == "positive":
            st.success(alert["message"])
        else:
            st.warning(alert["message"])

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
