"""
finance.py - Calculs financiers pour l'analyseur de rentabilite immobiliere v2.0
"""
from math import isfinite

import numpy as np
import numpy_financial as npf

from config import (
    BAREME_MUTATION_MONTREAL,
    BAREME_MUTATION_PROVINCIAL,
    INTERPRETATION_RATIOS,
    TAUX_SCOLAIRE,
)


# =============================================================================
# CALCULS DE BASE
# =============================================================================
def calculer_taxes_municipales(evaluation: float, taux_par_100: float) -> float:
    """Calcule les taxes municipales a partir de l'evaluation et du taux par 100$."""
    return evaluation * taux_par_100 / 100


def calculer_taxes_scolaires(evaluation: float) -> float:
    """Calcule les taxes scolaires (taux provincial unique)."""
    return evaluation * TAUX_SCOLAIRE / 100


def calculer_droits_mutation(prix: float, ville: str) -> float:
    """Calcule les droits de mutation (taxe de bienvenue) selon le bareme."""
    if "Montreal" in ville or "Montréal" in ville:
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
    """Calcule le paiement hypothecaire mensuel."""
    if montant_pret <= 0 or amortissement_ans <= 0:
        return 0.0
    taux_mensuel = taux_annuel / 100 / 12
    nb_paiements = amortissement_ans * 12
    if taux_mensuel == 0:
        return montant_pret / nb_paiements
    return float(-npf.pmt(taux_mensuel, nb_paiements, montant_pret))


# =============================================================================
# ANALYSE ANNEE 1
# =============================================================================
def analyser_annee1(
    prix_achat: float,
    evaluation_municipale: float,
    taux_municipal_par_100: float,
    ville: str,
    loyers_mensuels_total: float,
    taux_vacance: float,
    assurance: float,
    entretien_autre: float,
    tonte: float,
    deneigement: float,
    electricite: float,
    gestion: float,
    autres_depenses: float,
    taux_interet: float,
    amortissement: int,
    mise_de_fonds_pct: float,
    frais_notaire: float,
    frais_inspection: float,
    frais_evaluation: float,
) -> dict:
    """Calcule tous les indicateurs de l'annee 1."""

    mise_de_fonds = prix_achat * mise_de_fonds_pct / 100
    montant_pret = prix_achat - mise_de_fonds

    paiement_mensuel = calculer_paiement_hypothecaire_mensuel(
        montant_pret, taux_interet, amortissement
    )
    paiement_annuel = paiement_mensuel * 12

    revenus_bruts_annuels = loyers_mensuels_total * 12
    revenus_nets = revenus_bruts_annuels * (1 - taux_vacance / 100)

    taxes_municipales = calculer_taxes_municipales(
        evaluation_municipale, taux_municipal_par_100
    )
    taxes_scolaires = calculer_taxes_scolaires(evaluation_municipale)

    depenses_totales = (
        taxes_municipales
        + taxes_scolaires
        + assurance
        + entretien_autre
        + tonte
        + deneigement
        + electricite
        + gestion
        + autres_depenses
    )

    rne = revenus_nets - depenses_totales

    droits_mutation = calculer_droits_mutation(prix_achat, ville)
    frais_acquisition = (
        droits_mutation + frais_notaire + frais_inspection + frais_evaluation
    )

    cashflow_avant_frais = rne - paiement_annuel
    cashflow_net_annee1 = cashflow_avant_frais

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
        "rne": rne,
        "droits_mutation": droits_mutation,
        "frais_acquisition": frais_acquisition,
        "cashflow_avant_frais": cashflow_avant_frais,
        "cashflow_net_annee1": cashflow_net_annee1,
        "interet_annee1": interet_annee1,
        "capital_annee1": capital_annee1,
        "assurance": assurance,
        "entretien_autre": entretien_autre,
        "tonte": tonte,
        "deneigement": deneigement,
        "electricite": electricite,
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
    taux_marginal_impot: float,
) -> dict:
    """Projette les resultats sur 10 ans."""

    taux_mensuel = taux_interet / 100 / 12
    solde_pret = montant_pret
    valeur_immeuble = prix_achat
    investissement_initial = mise_de_fonds + frais_acquisition

    annees = []
    cashflows_irr = [-investissement_initial]

    revenus = revenus_nets_an1
    depenses = depenses_an1
    cashflow_cumule_tri = -investissement_initial
    cashflow_cumule_apres_impot = 0.0

    for annee in range(1, 11):
        if annee > 1:
            revenus *= 1 + croissance_loyers / 100
            depenses *= 1 + inflation_depenses / 100

        rne = revenus - depenses
        solde_debut = solde_pret

        interet_annuel = 0.0
        capital_annuel = 0.0
        for _ in range(12):
            if solde_pret <= 0:
                solde_pret = 0.0
                break

            interet_mois = solde_pret * taux_mensuel
            capital_mois = min(max(0.0, paiement_mensuel - interet_mois), solde_pret)
            interet_annuel += interet_mois
            capital_annuel += capital_mois
            solde_pret -= capital_mois

        paiement_annuel = interet_annuel + capital_annuel
        cashflow_avant_impot = rne - paiement_annuel

        cashflow_net_avant_impot = cashflow_avant_impot

        revenu_imposable = revenus - depenses - interet_annuel
        impot_a_payer = revenu_imposable * (taux_marginal_impot / 100)

        cashflow_net_apres_impot = cashflow_net_avant_impot - impot_a_payer

        valeur_immeuble *= 1 + appreciation / 100
        produit_vente_estime = (
            max(0.0, valeur_immeuble - solde_pret) if annee == 10 else 0.0
        )
        flux_total_tri = cashflow_net_apres_impot + produit_vente_estime
        cashflow_cumule_tri += flux_total_tri
        cashflow_cumule_apres_impot += cashflow_net_apres_impot
        equite = valeur_immeuble - solde_pret
        valeur_nette_projet = (
            equite + cashflow_cumule_apres_impot - investissement_initial
        )

        annees.append(
            {
                "annee": annee,
                "revenus_nets": round(revenus, 2),
                "depenses": round(depenses, 2),
                "rne": round(rne, 2),
                "paiement_hypo": round(paiement_annuel, 2),
                "interet": round(interet_annuel, 2),
                "capital": round(capital_annuel, 2),
                "cashflow_avant_impot": round(cashflow_net_avant_impot, 2),
                "revenu_imposable": round(revenu_imposable, 2),
                "impot": round(impot_a_payer, 2),
                "cashflow_apres_impot": round(cashflow_net_apres_impot, 2),
                "produit_vente_estime": round(produit_vente_estime, 2),
                "flux_total_tri": round(flux_total_tri, 2),
                "cashflow_cumule": round(cashflow_cumule_tri, 2),
                "cashflow_cumule_apres_impot": round(cashflow_cumule_apres_impot, 2),
                "valeur_immeuble": round(valeur_immeuble, 2),
                "solde_debut": round(solde_debut, 2),
                "solde_pret": round(solde_pret, 2),
                "equite": round(equite, 2),
                "valeur_nette_projet": round(valeur_nette_projet, 2),
            }
        )

        cashflows_irr.append(flux_total_tri)

    return {
        "annees": annees,
        "cashflows_irr": cashflows_irr,
        "investissement_initial": round(investissement_initial, 2),
    }


# =============================================================================
# RATIOS ET INDICATEURS
# =============================================================================
def calculer_ratios(
    prix_achat: float,
    rne: float,
    cashflow_annee1: float,
    mise_de_fonds: float,
    revenus_bruts: float,
    paiement_annuel: float,
    cashflows_irr: list,
    taux_actualisation: float,
) -> dict:
    """Calcule les principaux ratios d'analyse."""

    cap_rate = (rne / prix_achat) * 100 if prix_achat > 0 else 0.0

    cash_on_cash = (
        (cashflow_annee1 / mise_de_fonds) * 100 if mise_de_fonds > 0 else 0.0
    )

    mrb = prix_achat / revenus_bruts if revenus_bruts > 0 else float("inf")

    csd = rne / paiement_annuel if paiement_annuel > 0 else float("inf")

    try:
        tri = float(npf.irr(cashflows_irr)) * 100
    except Exception:
        tri = None

    try:
        van = float(npf.npv(taux_actualisation / 100, cashflows_irr))
    except Exception:
        van = None

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
# INTERPRETATION DES RATIOS
# =============================================================================
def _arrondir_millier(valeur: float, mode: str = "nearest") -> float:
    if valeur is None:
        return 0.0
    if mode == "down":
        return max(0.0, float(int(valeur / 1000.0)) * 1000.0)
    if mode == "up":
        return max(0.0, float(int((valeur + 999.0) / 1000.0)) * 1000.0)
    return max(0.0, round(valeur / 1000.0) * 1000.0)


def _format_money(value: float) -> str:
    return f"{value:,.0f}$".replace(",", " ")


def _status_score(status: str) -> int:
    scores = {
        "positive": 2,
        "warning": -1,
        "negative": -2,
        "neutral": 0,
    }
    return scores.get(status, 0)


def _build_ratio_review(cle_ratio: str, valeur) -> dict:
    info = INTERPRETATION_RATIOS.get(cle_ratio, {"nom": cle_ratio, "description": ""})
    review = {
        "nom": info["nom"],
        "description": info["description"],
        "interpretation": "Donnee indisponible pour ce ratio.",
        "status": "neutral",
        "headline": "Ratio non interpretable.",
        "target": None,
        "score": 0,
    }

    if valeur is None:
        return review

    if cle_ratio == "cap_rate":
        review["target"] = 5.5
        if valeur < 4.0:
            review["status"] = "negative"
            review["headline"] = "Cap rate trop faible."
            review["interpretation"] = (
                f"Le cap rate de {valeur:.2f}% est trop faible pour le prix demande. "
                "Le revenu net ne remunere pas assez le capital immobilise."
            )
        elif valeur < 5.5:
            review["status"] = "warning"
            review["headline"] = "Cap rate serre."
            review["interpretation"] = (
                f"Le cap rate de {valeur:.2f}% reste exploitable, mais la rentabilite depend d'une gestion rigoureuse "
                "ou d'un meilleur prix d'entree."
            )
        else:
            review["status"] = "positive"
            review["headline"] = "Cap rate solide."
            review["interpretation"] = (
                f"Le cap rate de {valeur:.2f}% soutient convenablement le prix paye et laisse une base plus saine "
                "pour l'exploitation."
            )

    elif cle_ratio == "cash_on_cash":
        review["target"] = 4.0
        if valeur < 0.0:
            review["status"] = "negative"
            review["headline"] = "Cashflow investisseur negatif."
            review["interpretation"] = (
                f"Le rendement sur mise de fonds est negatif a {valeur:.2f}%. "
                "La mise de fonds n'achete pas encore un cashflow annuel positif."
            )
        elif valeur < 4.0:
            review["status"] = "warning"
            review["headline"] = "Rendement initial faible."
            review["interpretation"] = (
                f"Le cash-on-cash de {valeur:.2f}% demeure faible. "
                "Le projet peut fonctionner, mais le rendement immediat reste modeste."
            )
        else:
            review["status"] = "positive"
            review["headline"] = "Rendement initial acceptable."
            review["interpretation"] = (
                f"Le cash-on-cash de {valeur:.2f}% indique que la mise de fonds produit deja un rendement annuel raisonnable."
            )

    elif cle_ratio == "mrb":
        review["target"] = 14.0
        if valeur < 10.0:
            review["status"] = "positive"
            review["headline"] = "MRB favorable."
            review["interpretation"] = (
                f"Le MRB de {valeur:.2f}x est bas pour l'actif analyse, ce qui suggere un prix coherent par rapport aux revenus bruts."
            )
        elif valeur < 14.0:
            review["status"] = "warning"
            review["headline"] = "MRB dans la moyenne."
            review["interpretation"] = (
                f"Le MRB de {valeur:.2f}x se situe dans une zone de marche correcte, sans marge evidente."
            )
        else:
            review["status"] = "negative"
            review["headline"] = "MRB eleve."
            review["interpretation"] = (
                f"Le MRB de {valeur:.2f}x parait eleve. Le prix achete beaucoup d'annees de revenus bruts."
            )

    elif cle_ratio == "csd":
        review["target"] = 1.20
        if valeur < 1.0:
            review["status"] = "negative"
            review["headline"] = "Dette insuffisamment couverte."
            review["interpretation"] = (
                f"Le CSD de {valeur:.2f}x indique que l'exploitation ne couvre pas completement le service de la dette."
            )
        elif valeur < 1.20:
            review["status"] = "warning"
            review["headline"] = "Couverture de dette mince."
            review["interpretation"] = (
                f"Le CSD de {valeur:.2f}x reste serre. La structure supporte mal une vacance plus forte ou un imprevu."
            )
        else:
            review["status"] = "positive"
            review["headline"] = "Couverture de dette saine."
            review["interpretation"] = (
                f"Le CSD de {valeur:.2f}x offre une marge plus confortable pour couvrir la dette."
            )

    elif cle_ratio == "tri":
        review["target"] = 8.0
        if valeur < 5.0:
            review["status"] = "negative"
            review["headline"] = "TRI trop faible."
            review["interpretation"] = (
                f"Le TRI de {valeur:.2f}% reste faible pour un horizon de 10 ans. "
                "Le couple risque-rendement manque d'attrait."
            )
        elif valeur < 8.0:
            review["status"] = "warning"
            review["headline"] = "TRI correct mais sans prime claire."
            review["interpretation"] = (
                f"Le TRI de {valeur:.2f}% est defendable, mais pas assez fort pour absorber sereinement un scenario moins favorable."
            )
        else:
            review["status"] = "positive"
            review["headline"] = "TRI attractif."
            review["interpretation"] = (
                f"Le TRI de {valeur:.2f}% montre un potentiel de creation de valeur interessant sur 10 ans."
            )

    elif cle_ratio == "van":
        review["target"] = 0.0
        if valeur < 0.0:
            review["status"] = "negative"
            review["headline"] = "Valeur detruite."
            review["interpretation"] = (
                f"La VAN de {valeur:,.0f}$ est negative. Au taux exige, le projet ne cree pas assez de valeur."
            ).replace(",", " ")
        else:
            review["status"] = "positive"
            review["headline"] = "Valeur creee."
            review["interpretation"] = (
                f"La VAN de {valeur:,.0f}$ est positive. Le projet depasse le rendement minimal exige."
            ).replace(",", " ")

    review["score"] = _status_score(review["status"])
    return review


def expliquer_ratio(cle_ratio: str, valeur: float) -> dict:
    """
    Retourne le nom, la description et l'interpretation d'un ratio.
    """
    review = _build_ratio_review(cle_ratio, valeur)
    return {
        "nom": review["nom"],
        "description": review["description"],
        "interpretation": review["interpretation"],
        "status": review["status"],
        "headline": review["headline"],
        "target": review["target"],
    }


# =============================================================================
# MOTEUR D'ANALYSE ET RECOMMANDATION
# =============================================================================
def analyser_opportunite_investissement(
    ratios: dict,
    prix_achat: float,
    rne: float,
    revenus_bruts_annuels: float,
    depenses_totales: float,
    paiement_annuel: float,
    montant_pret: float,
    mise_de_fonds: float,
    frais_acquisition: float,
    cashflow_annuel: float,
    loyers_mensuels_total: float,
    nb_logements: int,
    taux_vacance: float,
) -> dict:
    """
    Retourne une analyse structuree du dossier.

    Le format de sortie reste simple pour la V1, mais il est deja compatible
    avec un rendu par regles ou un futur enrichissement par LLM.
    """

    _ = revenus_bruts_annuels, frais_acquisition

    ratio_reviews = {
        key: _build_ratio_review(key, ratios.get(key))
        for key in ["cap_rate", "cash_on_cash", "mrb", "csd", "tri", "van"]
    }

    positive_count = sum(
        1 for review in ratio_reviews.values() if review["status"] == "positive"
    )
    warning_count = sum(
        1 for review in ratio_reviews.values() if review["status"] == "warning"
    )
    negative_count = sum(
        1 for review in ratio_reviews.values() if review["status"] == "negative"
    )
    total_score = sum(review["score"] for review in ratio_reviews.values())

    if (
        cashflow_annuel >= 0
        and ratio_reviews["csd"]["status"] == "positive"
        and ratio_reviews["cap_rate"]["status"] == "positive"
    ):
        scenario = {
            "label": "Portage sain",
            "summary": "Le dossier se defend deja par ses revenus d'exploitation et ne depend pas uniquement d'une revente future.",
        }
    elif cashflow_annuel < 0 and ratio_reviews["tri"]["status"] == "positive":
        scenario = {
            "label": "Pari appreciation",
            "summary": "Le projet mise davantage sur la creation de valeur a long terme que sur le cashflow courant.",
        }
    elif negative_count >= 2 or ratio_reviews["csd"]["status"] == "negative":
        scenario = {
            "label": "A renegocier",
            "summary": "Le montage actuel parait trop serre et demande soit un meilleur prix, soit une structure plus prudente.",
        }
    else:
        scenario = {
            "label": "Equilibre fragile",
            "summary": "Le projet peut fonctionner, mais plusieurs leviers doivent rester sous controle pour proteger le rendement.",
        }

    if negative_count >= 2 or total_score <= -4:
        verdict = {
            "label": "Verdict final",
            "value": "A renegocier",
            "note": (
                f"Scenario: {scenario['label']}. {scenario['summary']} "
                "Le dossier n'atteint pas encore un niveau de securite suffisant dans sa configuration actuelle."
            ),
            "variant": "negative",
        }
    elif negative_count == 0 and warning_count <= 1 and positive_count >= 4:
        verdict = {
            "label": "Verdict final",
            "value": "Achetable",
            "note": (
                f"Scenario: {scenario['label']}. {scenario['summary']} "
                "Les indicateurs principaux sont coherents pour un achat discipline."
            ),
            "variant": "positive",
        }
    else:
        verdict = {
            "label": "Verdict final",
            "value": "Achetable sous conditions",
            "note": (
                f"Scenario: {scenario['label']}. {scenario['summary']} "
                "Le projet demande des ajustements ou une surveillance plus serree avant decision finale."
            ),
            "variant": "warning",
        }

    target_cap_rate = (
        6.0 if verdict["variant"] == "negative" else (5.0 if verdict["variant"] == "positive" else 5.5)
    )
    target_csd = 1.20

    price_candidates = []
    if rne > 0 and target_cap_rate > 0:
        price_candidates.append(("cap rate", rne / (target_cap_rate / 100.0)))

    csd_current = ratios.get("csd")
    if (
        prix_achat > 0
        and paiement_annuel > 0
        and csd_current is not None
        and isfinite(csd_current)
    ):
        price_candidates.append(("CSD", prix_achat * (csd_current / target_csd)))

    binding_metric = None
    prix_max_recommande = prix_achat
    if price_candidates:
        binding_metric, prix_max_recommande = min(price_candidates, key=lambda item: item[1])
    prix_max_recommande = _arrondir_millier(prix_max_recommande, mode="down")

    if prix_achat > prix_max_recommande * 1.02:
        contre_offre = _arrondir_millier(prix_max_recommande * 0.98, mode="down")
        counter_offer_action = {
            "label": "Contre-offre suggeree",
            "value": _format_money(contre_offre),
            "variant": "negative",
            "note": (
                f"Le prix affiche depasse la zone defendable. Une approche autour de {_format_money(contre_offre)} "
                f"laisse encore une marge avant le plafond recommande de {_format_money(prix_max_recommande)}."
            ),
        }
        max_price_action = {
            "label": "Prix maximal recommande",
            "value": _format_money(prix_max_recommande),
            "variant": "warning",
            "note": (
                f"Plafond estime pour viser un cap rate cible de {target_cap_rate:.1f}% et un CSD cible de {target_csd:.2f}x. "
                f"Le seuil limitant ici est le {binding_metric}."
            ),
        }
    else:
        counter_offer_action = {
            "label": "Contre-offre suggeree",
            "value": "Optionnelle",
            "variant": "positive",
            "note": "Le prix courant reste dans une zone defendable avec les seuils cibles retenus.",
        }
        max_price_action = {
            "label": "Prix maximal recommande",
            "value": _format_money(prix_max_recommande),
            "variant": "positive",
            "note": (
                f"Le prix analyse reste compatible avec un cap rate cible de {target_cap_rate:.1f}% et un CSD cible de {target_csd:.2f}x."
            ),
        }

    if montant_pret > 0 and paiement_annuel > 0 and rne > 0:
        paiement_cible = rne / target_csd
        if paiement_annuel > paiement_cible:
            facteur_reduction = max(0.0, min(1.0, paiement_cible / paiement_annuel))
            pret_cible = montant_pret * facteur_reduction
            apport_additionnel = max(0.0, montant_pret - pret_cible)
            nouvelle_mise_de_fonds = mise_de_fonds + apport_additionnel
            nouvelle_mdf_pct = (
                (nouvelle_mise_de_fonds / prix_achat * 100.0) if prix_achat > 0 else 0.0
            )
            mise_de_fonds_action = {
                "label": "Ajustement de mise de fonds",
                "value": f"+{_format_money(apport_additionnel)}",
                "variant": "warning" if apport_additionnel < mise_de_fonds * 0.35 else "negative",
                "note": (
                    f"Porter la mise de fonds a environ {_format_money(nouvelle_mise_de_fonds)} ({nouvelle_mdf_pct:.1f}%) "
                    f"rapprocherait le dossier d'un CSD de {target_csd:.2f}x."
                ),
            }
        else:
            mise_de_fonds_action = {
                "label": "Ajustement de mise de fonds",
                "value": "Non requis",
                "variant": "positive",
                "note": "La structure actuelle de mise de fonds est deja compatible avec le seuil de couverture cible.",
            }
    else:
        mise_de_fonds_action = {
            "label": "Ajustement de mise de fonds",
            "value": "N/A",
            "variant": "neutral",
            "note": "Impossible d'estimer un ajustement fiable avec les donnees actuelles.",
        }

    facteur_occupation = max(0.0, 1.0 - (taux_vacance / 100.0))
    loyer_cible_total = None
    hausse_loyers_total = None
    hausse_loyer_par_logement = None
    hausse_loyers_pct = None
    if facteur_occupation > 0:
        loyer_cible_total = (
            (depenses_totales + paiement_annuel * target_csd) / facteur_occupation
        ) / 12.0
        hausse_loyers_total = loyer_cible_total - loyers_mensuels_total
        hausse_loyer_par_logement = (
            hausse_loyers_total / nb_logements if nb_logements > 0 else None
        )
        hausse_loyers_pct = (
            (hausse_loyers_total / loyers_mensuels_total) * 100.0
            if loyers_mensuels_total > 0
            else None
        )

    if loyer_cible_total is None:
        loyers_action = {
            "label": "Potentiel d'optimisation des loyers",
            "value": "N/A",
            "variant": "neutral",
            "note": "Le calcul n'est pas interpretable avec un taux de vacance de 100%.",
        }
        tal_warning = {
            "variant": "warning",
            "message": "Le scenario TAL n'a pas pu etre evalue correctement avec les donnees actuelles.",
        }
    elif hausse_loyers_total <= 0:
        loyers_action = {
            "label": "Potentiel d'optimisation des loyers",
            "value": "Aucune hausse requise",
            "variant": "positive",
            "note": (
                f"Les loyers actuels couvrent deja un objectif de CSD de {target_csd:.2f}x. "
                f"Le loyer cible estime est d'environ {_format_money(loyer_cible_total)}/mois."
            ),
        }
        tal_warning = {
            "variant": "positive",
            "message": "Aucune pression immediate de hausse n'apparait. Le risque operationnel lie au TAL reste donc plus limite.",
        }
    else:
        hausse_par_logement_str = (
            f", soit environ +{_format_money(hausse_loyer_par_logement)}/logement/mois"
            if hausse_loyer_par_logement is not None
            else ""
        )
        loyers_action = {
            "label": "Potentiel d'optimisation des loyers",
            "value": f"+{_format_money(hausse_loyers_total)}/mois",
            "variant": "warning" if (hausse_loyers_pct or 0.0) <= 5.0 else "negative",
            "note": (
                f"Pour viser un CSD de {target_csd:.2f}x, il faudrait environ +{_format_money(hausse_loyers_total)}/mois"
                f"{hausse_par_logement_str}."
            ),
        }

        if (hausse_loyers_pct or 0.0) >= 10.0 or (hausse_loyer_par_logement or 0.0) >= 100.0:
            tal_warning = {
                "variant": "negative",
                "message": (
                    "La hausse de loyer necessaire parait agressive. Au Quebec, les augmentations sont encadrees par le TAL "
                    "et doivent etre justifiables immeuble par immeuble. Ce point merite une verification juridique et terrain."
                ),
            }
        else:
            tal_warning = {
                "variant": "warning",
                "message": (
                    "Une optimisation de loyer est envisageable, mais elle doit rester compatible avec les regles du TAL, "
                    "le cycle de renouvellement des baux et l'etat locatif reel."
                ),
            }

    strengths = [
        review["headline"]
        for review in ratio_reviews.values()
        if review["status"] == "positive"
    ]
    risks = [
        review["headline"]
        for review in ratio_reviews.values()
        if review["status"] in {"warning", "negative"}
    ]

    actions = [
        counter_offer_action,
        max_price_action,
        mise_de_fonds_action,
        loyers_action,
    ]

    return {
        "scenario": scenario,
        "verdict": verdict,
        "ratio_reviews": ratio_reviews,
        "strengths": strengths,
        "risks": risks,
        "actions": actions,
        "alerts": [tal_warning],
        "targets": {
            "cap_rate": target_cap_rate,
            "csd": target_csd,
        },
    }


def generer_recommandation(ratios: dict, prix_achat: float, analyse: dict = None) -> str:
    """Genere un resume markdown a partir d'une analyse structuree."""

    _ = ratios, prix_achat

    if analyse is None:
        analyse = {
            "verdict": {
                "value": "Analyse partielle",
                "note": "Aucune analyse detaillee n'a ete fournie au moteur de recommandation.",
            },
            "strengths": [],
            "risks": [],
            "actions": [],
            "alerts": [],
        }

    verdict = analyse.get("verdict", {})
    strengths = analyse.get("strengths", [])
    risks = analyse.get("risks", [])
    actions = analyse.get("actions", [])
    alerts = analyse.get("alerts", [])

    sections = [
        f"**Verdict** : {verdict.get('value', 'Analyse indisponible')}",
        verdict.get("note", ""),
    ]

    if strengths:
        sections.append("**Forces**")
        sections.extend([f"- {point}" for point in strengths])

    if risks:
        sections.append("**Points de vigilance**")
        sections.extend([f"- {point}" for point in risks])

    if actions:
        sections.append("**Actions recommandees**")
        sections.extend(
            [f"- {action['label']} : {action['value']} - {action['note']}" for action in actions]
        )

    if alerts:
        sections.append("**Alertes**")
        sections.extend([f"- {alert['message']}" for alert in alerts])

    return "\n\n".join([section for section in sections if section])
