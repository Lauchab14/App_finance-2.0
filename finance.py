"""
finance.py — Calculs financiers pour l'analyseur de rentabilité immobilière v2.0
"""
import numpy as np
import numpy_financial as npf
from config import (
    BAREME_MUTATION_PROVINCIAL,
    BAREME_MUTATION_MONTREAL,
    TAUX_SCOLAIRE,
    INTERPRETATION_RATIOS,
)


# =============================================================================
# CALCULS DE BASE
# =============================================================================
def calculer_taxes_municipales(evaluation: float, taux_par_100: float) -> float:
    """Calcule les taxes municipales à partir de l'évaluation et du taux par 100$."""
    return evaluation * taux_par_100 / 100


def calculer_taxes_scolaires(evaluation: float) -> float:
    """Calcule les taxes scolaires (taux provincial unique)."""
    return evaluation * TAUX_SCOLAIRE / 100


def calculer_droits_mutation(prix: float, ville: str) -> float:
    """Calcule les droits de mutation (taxe de bienvenue) selon le barème."""
    if "Montréal" in ville:
        bareme = BAREME_MUTATION_MONTREAL
    else:
        bareme = BAREME_MUTATION_PROVINCIAL

    total = 0.0
    tranche_basse = 0.0
    for plafond, taux in bareme:
        montant_tranche = min(prix, plafond) - tranche_basse
        if montant_tranche <= 0:
            break
        total += montant_tranche * taux
        tranche_basse = plafond
    return round(total, 2)


def calculer_paiement_hypothecaire_mensuel(
    montant_pret: float, taux_annuel: float, amortissement_ans: int
) -> float:
    """Calcule le paiement hypothécaire mensuel."""
    if montant_pret <= 0 or amortissement_ans <= 0:
        return 0.0
    taux_mensuel = taux_annuel / 100 / 12
    nb_paiements = amortissement_ans * 12
    if taux_mensuel == 0:
        return montant_pret / nb_paiements
    return float(-npf.pmt(taux_mensuel, nb_paiements, montant_pret))


# =============================================================================
# ANALYSE ANNÉE 1
# =============================================================================
def analyser_annee1(
    prix_achat: float,
    evaluation_municipale: float,
    taux_municipal_par_100: float,
    ville: str,
    loyers_mensuels_total: float,
    taux_vacance: float,
    assurance: float,
    entretien: float,
    gestion: float,
    autres_depenses: float,
    taux_interet: float,
    amortissement: int,
    mise_de_fonds_pct: float,
    frais_notaire: float,
    frais_inspection: float,
    frais_evaluation: float,
) -> dict:
    """Calcule tous les indicateurs de l'année 1."""

    # --- Mise de fonds et prêt ---
    mise_de_fonds = prix_achat * mise_de_fonds_pct / 100
    montant_pret = prix_achat - mise_de_fonds

    # --- Hypothèque ---
    paiement_mensuel = calculer_paiement_hypothecaire_mensuel(
        montant_pret, taux_interet, amortissement
    )
    paiement_annuel = paiement_mensuel * 12

    # --- Revenus ---
    revenus_bruts_annuels = loyers_mensuels_total * 12
    revenus_nets = revenus_bruts_annuels * (1 - taux_vacance / 100)

    # --- Taxes ---
    taxes_municipales = calculer_taxes_municipales(
        evaluation_municipale, taux_municipal_par_100
    )
    taxes_scolaires = calculer_taxes_scolaires(evaluation_municipale)

    # --- Dépenses ---
    depenses_totales = (
        taxes_municipales + taxes_scolaires + assurance + entretien + gestion + autres_depenses
    )

    # --- NOI (Net Operating Income) ---
    noi = revenus_nets - depenses_totales

    # --- Frais non récurrents ---
    droits_mutation = calculer_droits_mutation(prix_achat, ville)
    frais_acquisition = droits_mutation + frais_notaire + frais_inspection + frais_evaluation

    # --- Cashflow ---
    cashflow_avant_frais = noi - paiement_annuel
    cashflow_net_annee1 = cashflow_avant_frais - frais_acquisition

    # --- Intérêts vs capital année 1 ---
    taux_mensuel = taux_interet / 100 / 12
    interet_annee1 = 0.0
    capital_annee1 = 0.0
    solde = montant_pret
    for _ in range(12):
        interet_mois = solde * taux_mensuel
        capital_mois = paiement_mensuel - interet_mois
        interet_annee1 += interet_mois
        capital_annee1 += capital_mois
        solde -= capital_mois

    return {
        "mise_de_fonds": mise_de_fonds,
        "montant_pret": montant_pret,
        "paiement_mensuel": paiement_mensuel,
        "paiement_annuel": paiement_annuel,
        "revenus_bruts_annuels": revenus_bruts_annuels,
        "revenus_nets": revenus_nets,
        "taxes_municipales": taxes_municipales,
        "taxes_scolaires": taxes_scolaires,
        "depenses_totales": depenses_totales,
        "noi": noi,
        "droits_mutation": droits_mutation,
        "frais_acquisition": frais_acquisition,
        "cashflow_avant_frais": cashflow_avant_frais,
        "cashflow_net_annee1": cashflow_net_annee1,
        "interet_annee1": interet_annee1,
        "capital_annee1": capital_annee1,
        "assurance": assurance,
        "entretien": entretien,
        "gestion": gestion,
        "autres_depenses": autres_depenses,
    }


# =============================================================================
# PROJECTION 10 ANS
# =============================================================================
def projeter_10_ans(
    prix_achat: float,
    montant_pret: float,
    paiement_mensuel: float,
    revenus_nets_an1: float,
    depenses_an1: float,
    frais_acquisition: float,
    mise_de_fonds: float,
    taux_interet: float,
    croissance_loyers: float,
    inflation_depenses: float,
    appreciation: float,
) -> dict:
    """Projette les résultats sur 10 ans."""

    taux_mensuel = taux_interet / 100 / 12
    solde_pret = montant_pret
    valeur_immeuble = prix_achat

    annees = []
    cashflows_irr = [-(mise_de_fonds + frais_acquisition)]  # investissement initial

    revenus = revenus_nets_an1
    depenses = depenses_an1
    paiement_annuel = paiement_mensuel * 12
    cashflow_cumule = 0.0

    for annee in range(1, 11):
        if annee > 1:
            revenus *= 1 + croissance_loyers / 100
            depenses *= 1 + inflation_depenses / 100

        noi = revenus - depenses

        # Amortissement du prêt cette année
        interet_annuel = 0.0
        capital_annuel = 0.0
        for _ in range(12):
            interet_mois = solde_pret * taux_mensuel
            capital_mois = paiement_mensuel - interet_mois
            interet_annuel += interet_mois
            capital_annuel += capital_mois
            solde_pret -= capital_mois

        cashflow = noi - paiement_annuel
        if annee == 1:
            cashflow -= frais_acquisition

        cashflow_cumule += cashflow

        valeur_immeuble *= 1 + appreciation / 100
        equite = valeur_immeuble - solde_pret

        annees.append(
            {
                "annee": annee,
                "revenus_nets": round(revenus, 2),
                "depenses": round(depenses, 2),
                "noi": round(noi, 2),
                "paiement_hypo": round(paiement_annuel, 2),
                "interet": round(interet_annuel, 2),
                "capital": round(capital_annuel, 2),
                "cashflow": round(cashflow, 2),
                "cashflow_cumule": round(cashflow_cumule, 2),
                "valeur_immeuble": round(valeur_immeuble, 2),
                "solde_pret": round(solde_pret, 2),
                "equite": round(equite, 2),
            }
        )

        # Pour le TRI : cashflow de l'année (+ valeur nette si dernière année)
        if annee < 10:
            cashflows_irr.append(cashflow)
        else:
            # Dernière année : on « vend » l'immeuble
            cashflows_irr.append(cashflow + valeur_immeuble - solde_pret)

    return {"annees": annees, "cashflows_irr": cashflows_irr}


# =============================================================================
# RATIOS ET INDICATEURS
# =============================================================================
def calculer_ratios(
    prix_achat: float,
    noi: float,
    cashflow_annee1: float,
    mise_de_fonds_totale: float,
    revenus_bruts: float,
    paiement_annuel: float,
    cashflows_irr: list,
    taux_actualisation: float,
) -> dict:
    """Calcule les principaux ratios d'analyse."""

    cap_rate = (noi / prix_achat) * 100 if prix_achat > 0 else 0.0

    cash_on_cash = (
        (cashflow_annee1 / mise_de_fonds_totale) * 100
        if mise_de_fonds_totale > 0
        else 0.0
    )

    mrb = prix_achat / revenus_bruts if revenus_bruts > 0 else float("inf")

    csd = noi / paiement_annuel if paiement_annuel > 0 else float("inf")

    try:
        tri = float(npf.irr(cashflows_irr)) * 100
    except Exception:
        tri = None

    try:
        van = float(npf.npv(taux_actualisation / 100, cashflows_irr))
    except Exception:
        van = None

    # Délai de récupération
    cumul = 0.0
    delai = None
    for i, cf in enumerate(cashflows_irr):
        cumul += cf
        if cumul >= 0 and i > 0:
            delai = i
            break

    return {
        "cap_rate": round(cap_rate, 2),
        "cash_on_cash": round(cash_on_cash, 2),
        "mrb": round(mrb, 2),
        "csd": round(csd, 2),
        "tri": round(tri, 2) if tri is not None else None,
        "van": round(van, 2) if van is not None else None,
        "delai_recuperation": delai,
    }


# =============================================================================
# INTERPRÉTATION DES RATIOS (phrases explicatives)
# =============================================================================
def expliquer_ratio(cle_ratio: str, valeur: float) -> dict:
    """
    Retourne le nom, la description et l'interprétation d'un ratio.
    """
    info = INTERPRETATION_RATIOS.get(cle_ratio)
    if not info:
        return {"nom": cle_ratio, "description": "", "interpretation": ""}

    interpretation = ""
    for seuil, texte in info["seuils"]:
        if valeur < seuil:
            interpretation = texte
            break

    return {
        "nom": info["nom"],
        "description": info["description"],
        "interpretation": interpretation,
    }


# =============================================================================
# RECOMMANDATION
# =============================================================================
def generer_recommandation(ratios: dict, prix_achat: float) -> str:
    """Génère un paragraphe de recommandation basé sur les indicateurs."""

    tri = ratios.get("tri")
    coc = ratios.get("cash_on_cash", 0)
    csd = ratios.get("csd", 0)
    cap = ratios.get("cap_rate", 0)

    points_positifs = []
    points_negatifs = []

    if cap >= 6:
        points_positifs.append(f"un bon taux de capitalisation ({cap}%)")
    elif cap < 4:
        points_negatifs.append(f"un faible taux de capitalisation ({cap}%)")

    if coc >= 5:
        points_positifs.append(f"un rendement sur mise de fonds intéressant ({coc}%)")
    elif coc < 0:
        points_negatifs.append(f"un cashflow négatif ({coc}%)")

    if csd >= 1.2:
        points_positifs.append(f"une bonne couverture de dette ({csd}x)")
    elif csd < 1.0:
        points_negatifs.append(f"une couverture de dette insuffisante ({csd}x)")

    if tri is not None and tri >= 10:
        points_positifs.append(f"un TRI attractif ({tri}%)")
    elif tri is not None and tri < 5:
        points_negatifs.append(f"un TRI faible ({tri}%)")

    if len(points_positifs) >= 3 and len(points_negatifs) == 0:
        verdict = "🟢 **Bon investissement !**"
        detail = (
            f"Cet immeuble présente {', '.join(points_positifs)}. "
            f"L'investissement semble solide et devrait générer un rendement satisfaisant."
        )
    elif len(points_negatifs) >= 2:
        # Calculer un prix suggéré (réduction de ~10%)
        prix_suggere = round(prix_achat * 0.90 / 1000) * 1000
        verdict = "🔴 **Investissement risqué — Contre-offre recommandée**"
        detail = (
            f"L'immeuble présente {', '.join(points_negatifs)}. "
            f"Nous recommandons une contre-offre aux alentours de **{prix_suggere:,.0f}$** "
            f"pour améliorer la rentabilité."
        )
    else:
        verdict = "🟡 **Investissement acceptable avec réserves**"
        tous_points = []
        if points_positifs:
            tous_points.append(f"Points positifs : {', '.join(points_positifs)}")
        if points_negatifs:
            tous_points.append(f"Points à surveiller : {', '.join(points_negatifs)}")
        detail = ". ".join(tous_points) + "."

    return f"{verdict}\n\n{detail}"
