"""
demographie.py — Analyse démographique basée sur les données du Recensement 2021
Utilise OpenNorth pour identifier la municipalité, puis cherche les
données réelles dans donnees_recensement.csv.
"""
import requests
import csv
import os
from typing import Dict
from difflib import get_close_matches

# Charger la base de données du recensement au démarrage
_RECENSEMENT = {}
_CSV_PATH = os.path.join(os.path.dirname(__file__), "donnees_recensement.csv")

def _charger_recensement():
    """Charge le fichier CSV du recensement en mémoire."""
    global _RECENSEMENT
    if _RECENSEMENT:
        return  # Déjà chargé
    
    try:
        with open(_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nom = row['nom_csd'].strip()
                _RECENSEMENT[nom.lower()] = {
                    'nom': nom,
                    'population_2021': int(row['population_2021']),
                    'population_2016': int(row['population_2016']),
                    'age_median': float(row['age_median']),
                    'revenu_median': int(row['revenu_median_menage']),
                    'locataires_pct': float(row['pct_locataires']),
                }
    except Exception as e:
        print(f"Erreur chargement recensement: {e}")


def _trouver_municipalite(nom_recherche: str) -> Dict:
    """
    Trouve la municipalité la plus proche dans la base de données.
    Utilise la correspondance floue pour gérer les variations de noms.
    """
    _charger_recensement()
    
    if not nom_recherche:
        return None
    
    nom = nom_recherche.lower().strip()
    
    # 1. Correspondance exacte
    if nom in _RECENSEMENT:
        return _RECENSEMENT[nom]
    
    # 2. Vérifier si le nom est contenu dans une entrée (ex: "Sainte-Marie" dans "Ville de Sainte-Marie")
    for cle, data in _RECENSEMENT.items():
        if nom in cle or cle in nom:
            return data
    
    # 3. Correspondance floue (seuil de 60%)
    noms_disponibles = list(_RECENSEMENT.keys())
    matches = get_close_matches(nom, noms_disponibles, n=1, cutoff=0.6)
    if matches:
        return _RECENSEMENT[matches[0]]
    
    # 4. Essayer sans les préfixes communs
    prefixes = ["ville de ", "municipalité de ", "municipalite de ", "paroisse de ", "canton de "]
    for prefix in prefixes:
        if nom.startswith(prefix):
            nom_court = nom[len(prefix):]
            if nom_court in _RECENSEMENT:
                return _RECENSEMENT[nom_court]
            matches = get_close_matches(nom_court, noms_disponibles, n=1, cutoff=0.6)
            if matches:
                return _RECENSEMENT[matches[0]]
    
    return None


def analyser_demographie(lat: float, lon: float, region: str) -> Dict[str, any]:
    """
    Génère un profil démographique pour une adresse donnée.
    
    Étape 1: Identifier la municipalité via OpenNorth (coordonnées GPS → nom CSD)
    Étape 2: Chercher les données réelles du Recensement 2021 dans notre base CSV
    Étape 3: Calculer la croissance et retourner les résultats
    """
    resultats = {
        "population": None,
        "croissance_pop": None,
        "revenu_median": None,
        "locataires_pct": None,
        "age_median": None,
        "trouve": False,
        "source": "Aucune donnée trouvée",
        "ville_analyse": None
    }
    
    # ──────────────────────────────────────────────────────────────
    # 1. Identifier la municipalité via OpenNorth
    # ──────────────────────────────────────────────────────────────
    nom_csd = None
    try:
        url_on = f"https://represent.opennorth.ca/boundaries/?contains={lat},{lon}&sets=census-subdivisions"
        r_on = requests.get(url_on, timeout=5)
        if r_on.status_code == 200 and r_on.json().get('objects'):
            nom_csd = r_on.json()['objects'][0]['name']
            resultats["ville_analyse"] = nom_csd
    except Exception as e:
        print(f"Erreur OpenNorth: {e}")

    # ──────────────────────────────────────────────────────────────
    # 2. Chercher dans notre base de données du Recensement
    # ──────────────────────────────────────────────────────────────
    donnees = _trouver_municipalite(nom_csd) if nom_csd else None
    
    if donnees:
        resultats["trouve"] = True
        resultats["population"] = donnees['population_2021']
        resultats["age_median"] = donnees['age_median']
        resultats["revenu_median"] = donnees['revenu_median']
        resultats["locataires_pct"] = donnees['locataires_pct']
        
        # Calculer la croissance démographique réelle (2016 → 2021)
        pop_2016 = donnees['population_2016']
        pop_2021 = donnees['population_2021']
        if pop_2016 > 0:
            croissance = round(((pop_2021 - pop_2016) / pop_2016) * 100, 1)
            resultats["croissance_pop"] = croissance
        
        resultats["source"] = f"Recensement Canada 2021 — {donnees['nom']}"
        resultats["ville_analyse"] = donnees['nom']
    else:
        # Aucune donnée trouvée — utiliser des estimations par défaut selon la région
        if "Métropolitaine" in region:
            resultats["locataires_pct"] = 55.0
            resultats["revenu_median"] = 65000
            resultats["age_median"] = 40.0
            resultats["croissance_pop"] = 3.0
        elif "Urbaine" in region:
            resultats["locataires_pct"] = 42.0
            resultats["revenu_median"] = 72000
            resultats["age_median"] = 42.0
            resultats["croissance_pop"] = 3.5
        elif "Semi-urbaine" in region:
            resultats["locataires_pct"] = 32.0
            resultats["revenu_median"] = 66000
            resultats["age_median"] = 43.0
            resultats["croissance_pop"] = 1.5
        else:
            resultats["locataires_pct"] = 25.0
            resultats["revenu_median"] = 62000
            resultats["age_median"] = 45.0
            resultats["croissance_pop"] = 0.5
        
        ville_label = nom_csd if nom_csd else "Inconnu"
        resultats["source"] = f"Estimations régionales ({region}) — {ville_label} non trouvé dans le recensement"
        if nom_csd:
            resultats["ville_analyse"] = nom_csd
    
    return resultats
