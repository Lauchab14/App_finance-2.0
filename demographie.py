"""
demographie.py — Scraping et agrégation des données démographiques
"""
import requests
import json
from typing import Dict, Optional

def analyser_demographie(lat: float, lon: float, region: str) -> Dict[str, any]:
    """
    Récupère ou estime les données démographiques (population, locataires, revenus) 
    pour une position donnée. 
    
    Puisque StatCan ne fournit pas d'API REST publique simple par coordonnées,
    cette fonction utilise une combinaison de requêtes OpenNorth pour identifier
    la région (CSD), et applique des moyennes robustes ou interroge OpenStreetMap 
    pour la densité locale.
    """
    resultats = {
        "population": None,
        "croissance_pop": None,
        "revenu_median": None,
        "locataires_pct": None,
        "trouve": False,
        "source": "Estimations régionales & OpenStreetMap"
    }
    
    # 1. Identifier la division de recensement via OpenNorth
    url_on = f"https://represent.opennorth.ca/boundaries/?contains={lat},{lon}&sets=census-subdivisions"
    csd_name = None
    
    try:
        r_on = requests.get(url_on, timeout=5)
        if r_on.status_code == 200 and r_on.json().get('objects'):
            csd_name = r_on.json()['objects'][0]['name']
            resultats["trouve"] = True
    except:
        pass

    # 2. Heuristique de densité via OpenStreetMap (bâtiments dans 1km)
    # Plus il y a d'appartements vs maisons, plus la proportion de locataires est élevée
    query_osm = f"""
    [out:json][timeout:10];
    (
      way["building"="apartments"](around:1000,{lat},{lon});
      way["building"="residential"](around:1000,{lat},{lon});
      way["building"="detached"](around:1000,{lat},{lon});
      way["building"="house"](around:1000,{lat},{lon});
    );
    out count;
    """
    
    nb_appts = 0
    nb_maisons = 0
    try:
        r_osm = requests.post("https://overpass-api.de/api/interpreter", data={"data": query_osm}, timeout=5)
        if r_osm.status_code == 200:
            data = r_osm.json()
            if "elements" in data and len(data["elements"]) > 0:
                tags = data["elements"][0].get("tags", {})
                # Overpass "out count" returns totals in tags
                for k, v in tags.items():
                    if "apartments" in k: nb_appts += int(v)
                    elif "house" in k or "detached" in k: nb_maisons += int(v)
                    elif "residential" in k: nb_appts += int(v) // 2 # Rough split
    except:
        pass

    # 3. Application des données proxy / estimations basées sur la région
    # Ces données proviennent du recensement 2021 global par région métropolitaine
    
    # Base baseline
    base_renters = 30.0
    base_income = 70000
    base_growth = 2.0
    
    if "Métropolitaine" in region or (csd_name and "Montréal" in csd_name):
        base_renters = 63.0    # Montréal a beaucoup de locataires
        base_income = 68000
        base_growth = 3.2
    elif "Urbaine" in region or (csd_name and "Québec" in csd_name):
        base_renters = 48.0
        base_income = 75000
        base_growth = 4.1
    elif "Semi-urbaine" in region:
        base_renters = 38.0
        base_income = 65000
        base_growth = 1.5
    else:
        # Rurale
        base_renters = 22.0
        base_income = 60000
        base_growth = -0.5

    # Ajustement selon la densité physique locale (OSM)
    total_bldgs = nb_appts + nb_maisons
    if total_bldgs > 10:
        ratio_appts = nb_appts / total_bldgs
        # Ajuster le % de locataires en fonction de la proportion d'appartements
        # Si > 80% d'appts, forte chance d'être très locateur
        ajustement = (ratio_appts - 0.5) * 20 
        base_renters = max(10.0, min(85.0, base_renters + ajustement))
        
        resultats["source"] = f"Ajusté via topologie locale OSM ({total_bldgs} bât.)"

    resultats["locataires_pct"] = round(base_renters, 1)
    resultats["revenu_median"] = base_income
    resultats["croissance_pop"] = base_growth
    
    if csd_name:
        resultats["ville_analyse"] = csd_name
        
    return resultats
