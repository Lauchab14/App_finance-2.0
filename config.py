"""
config.py — Données de référence pour l'analyseur de rentabilité immobilière v2.0
"""

# =============================================================================
# HYPOTHÈQUE — PARAMÈTRES PAR DÉFAUT
# =============================================================================
AMORTISSEMENT_DEFAUT = 25          # ans
MISE_DE_FONDS_PCT_DEFAUT = 20.0    # %
TAUX_INTERET_DEFAUT = 4.5          # %
# APH Select : amortissement jusqu'à 40 ans, mise de fonds dès 5%

# =============================================================================
# TAUX DE CROISSANCE / INFLATION PAR DÉFAUT
# =============================================================================
TAUX_VACANCE_DEFAUT = 5.0          # %
INFLATION_DEPENSES_DEFAUT = 2.0    # %
CROISSANCE_LOYERS_DEFAUT = 3.0     # %
APPRECIATION_DEFAUT = 3.0          # %
TAUX_ACTUALISATION_DEFAUT = 8.0    # % pour calcul VAN

# =============================================================================
# TAXE SCOLAIRE — TAUX PROVINCIAL UNIQUE (2024-2025)
# =============================================================================
TAUX_SCOLAIRE = 0.1054  # par 100$ d'évaluation → 0.001054 en décimal

# =============================================================================
# TAUX DE TAXATION MUNICIPALE PAR VILLE (par 100$ d'évaluation)
# =============================================================================
TAUX_MUNICIPAUX = {
    "Montréal": 0.8687,
    "Québec": 0.7924,
    "Laval": 0.7440,
    "Gatineau": 0.7816,
    "Longueuil": 0.7128,
    "Sherbrooke": 0.9408,
    "Lévis": 0.7684,
    "Trois-Rivières": 0.8600,
    "Drummondville": 0.8300,
    "Saint-Hyacinthe": 0.8800,
    "Saguenay": 0.8500,
    "Rimouski": 0.9000,
    "Saint-Georges (Beauce)": 0.7900,
    "Thetford Mines": 0.9200,
    "Val-d'Or": 0.9500,
    "Rouyn-Noranda": 0.9300,
    "Victoriaville": 0.8400,
    "Granby": 0.7800,
    "Saint-Jean-sur-Richelieu": 0.7200,
    "Autre (entrer manuellement)": 0.0,
}

# =============================================================================
# DROITS DE MUTATION (TAXE DE BIENVENUE) — BARÈME PROVINCIAL + MONTRÉAL
# =============================================================================
BAREME_MUTATION_PROVINCIAL = [
    (61_500, 0.005),
    (307_800, 0.010),
    (512_500, 0.015),
    (float("inf"), 0.020),
]

# Supplément Montréal (paliers supplémentaires)
BAREME_MUTATION_MONTREAL = [
    (61_500, 0.005),
    (307_800, 0.010),
    (512_500, 0.015),
    (1_000_000, 0.020),
    (2_000_000, 0.030),
    (float("inf"), 0.035),
]

# =============================================================================
# FRAIS NON RÉCURRENTS PAR DÉFAUT (ANNÉE 1)
# =============================================================================
FRAIS_NOTAIRE_DEFAUT = 1_500
FRAIS_INSPECTION_DEFAUT = 600
FRAIS_EVALUATION_DEFAUT = 400

# =============================================================================
# RÉGIONS ET PONDÉRATIONS DE LOCALISATION
# =============================================================================
REGIONS = {
    "Métropolitaine (Montréal, Laval, Longueuil)": {
        "transport": 0.20,
        "ecoles": 0.10,
        "commerces": 0.15,
        "inoccupation": 0.15,
        "demographie": 0.08,
        "quartier": 0.15,
        "stationnement": 0.07,
        "plus_value": 0.10,
    },
    "Urbaine (Québec, Lévis, Gatineau, Sherbrooke)": {
        "transport": 0.15,
        "ecoles": 0.10,
        "commerces": 0.15,
        "inoccupation": 0.15,
        "demographie": 0.10,
        "quartier": 0.15,
        "stationnement": 0.10,
        "plus_value": 0.10,
    },
    "Semi-urbaine (Trois-Rivières, Drummondville, St-Hyacinthe)": {
        "transport": 0.10,
        "ecoles": 0.12,
        "commerces": 0.12,
        "inoccupation": 0.15,
        "demographie": 0.12,
        "quartier": 0.12,
        "stationnement": 0.12,
        "plus_value": 0.15,
    },
    "Rurale (Beauce, Bas-St-Laurent, Abitibi, etc.)": {
        "transport": 0.05,
        "ecoles": 0.10,
        "commerces": 0.10,
        "inoccupation": 0.15,
        "demographie": 0.15,
        "quartier": 0.10,
        "stationnement": 0.15,
        "plus_value": 0.20,
    },
}

# Libellés et descriptions des critères de localisation
CRITERES_LOCALISATION = {
    "transport": {
        "label": "Transport en commun",
        "description": "Proximité et fréquence du transport en commun",
        "echelle": "1 = Aucun · 2 = Rare · 3 = Moyen · 4 = Bon · 5 = Excellent",
    },
    "ecoles": {
        "label": "Écoles",
        "description": "Proximité d'écoles primaires, secondaires et services de garde",
        "echelle": "1 = Très loin · 2 = Loin · 3 = Moyen · 4 = Proche · 5 = Très proche",
    },
    "commerces": {
        "label": "Commerces et services",
        "description": "Épiceries, pharmacies, restaurants et services à proximité",
        "echelle": "1 = Très loin · 2 = Loin · 3 = Moyen · 4 = Proche · 5 = Très proche",
    },
    "inoccupation": {
        "label": "Taux d'inoccupation",
        "description": "Taux de logements vacants dans le quartier",
        "echelle": "1 = Très élevé (>10%) · 2 = Élevé · 3 = Moyen · 4 = Bas · 5 = Très bas (<2%)",
    },
    "demographie": {
        "label": "Croissance démographique",
        "description": "Tendance de la population dans le secteur",
        "echelle": "1 = Déclin · 2 = Stagnant · 3 = Stable · 4 = Croissance · 5 = Forte croissance",
    },
    "quartier": {
        "label": "Qualité du quartier",
        "description": "Réputation, sécurité et attractivité du quartier",
        "echelle": "1 = Défavorisé · 2 = Modeste · 3 = Correct · 4 = Bon · 5 = Premium",
    },
    "stationnement": {
        "label": "Stationnement",
        "description": "Disponibilité de stationnement pour les locataires",
        "echelle": "1 = Aucun · 2 = Très limité · 3 = Limité · 4 = Suffisant · 5 = Abondant",
    },
    "plus_value": {
        "label": "Potentiel de plus-value",
        "description": "Potentiel d'appréciation de la valeur à moyen/long terme",
        "echelle": "1 = Faible · 2 = Limité · 3 = Moyen · 4 = Bon · 5 = Excellent",
    },
}

# =============================================================================
# INTERPRÉTATION DES RATIOS FINANCIERS
# =============================================================================
INTERPRETATION_RATIOS = {
    "cap_rate": {
        "nom": "Taux de capitalisation (Cap Rate)",
        "description": "Mesure le rendement annuel de l'immeuble par rapport à son prix d'achat, sans tenir compte du financement.",
        "seuils": [
            (4.0, "🔴 Faible — Marché surévalué ou loyers trop bas pour le prix payé. Risque élevé."),
            (6.0, "🟡 Acceptable — Rendement dans la moyenne, à surveiller si les taux montent."),
            (8.0, "🟢 Bon rendement — L'immeuble génère un revenu intéressant par rapport à son prix."),
            (float("inf"), "🟢 Excellent — Rendement très attractif, rare en zone urbaine."),
        ],
    },
    "cash_on_cash": {
        "nom": "Rendement sur mise de fonds (Cash-on-Cash)",
        "description": "Mesure le rendement annuel du cashflow par rapport à l'argent investi initialement.",
        "seuils": [
            (0.0, "🔴 Négatif — Vous perdez de l'argent chaque mois. Le cashflow ne couvre pas les dépenses."),
            (5.0, "🟡 Faible — Rendement inférieur à d'autres placements. L'équité compense peut-être."),
            (10.0, "🟢 Bon — Votre mise de fonds génère un rendement solide."),
            (float("inf"), "🟢 Excellent — Rendement supérieur, investissement très rentable."),
        ],
    },
    "mrb": {
        "nom": "Multiplicateur de revenu brut (MRB)",
        "description": "Indique combien d'années de revenus bruts il faut pour payer l'immeuble. Plus c'est bas, mieux c'est.",
        "seuils": [
            (10.0, "🟢 Sous-évalué — Potentiel intéressant, le prix est bas par rapport aux revenus."),
            (15.0, "🟡 Valeur marchande — Prix cohérent avec les revenus du secteur."),
            (float("inf"), "🔴 Surévalué — Le prix est élevé par rapport aux revenus générés."),
        ],
    },
    "csd": {
        "nom": "Ratio de couverture du service de la dette (CSD)",
        "description": "Vérifie si les revenus nets couvrent les paiements hypothécaires. Les banques exigent souvent > 1.2.",
        "seuils": [
            (1.0, "🔴 Insuffisant — Le revenu net d'exploitation ne couvre pas la dette. Risque de défaut."),
            (1.2, "🟡 Juste suffisant — Marge de sécurité mince. Vulnérable aux imprévus."),
            (float("inf"), "🟢 Sain — Bonne marge pour couvrir la dette et absorber les imprévus."),
        ],
    },
    "tri": {
        "nom": "Taux de rendement interne (TRI)",
        "description": "Rendement annualisé total de l'investissement sur 10 ans, incluant cashflow, équité et appréciation.",
        "seuils": [
            (5.0, "🔴 Faible — Inférieur à un placement sans risque (CPG, obligations)."),
            (10.0, "🟡 Raisonnable — Rendement acceptable mais pas exceptionnel pour l'immobilier."),
            (float("inf"), "🟢 Fort rendement — Investissement très performant sur 10 ans."),
        ],
    },
    "van": {
        "nom": "Valeur actualisée nette (VAN)",
        "description": "Si la VAN est positive, l'investissement crée de la valeur par rapport au taux d'actualisation choisi.",
        "seuils": [
            (0.0, "🔴 Négative — L'investissement détruit de la valeur. Vous feriez mieux de placer votre argent ailleurs."),
            (float("inf"), "🟢 Positive — L'investissement crée de la valeur. Le rendement dépasse votre taux exigé."),
        ],
    },
}
