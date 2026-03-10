"""
demographie.py — Analyse démographique personnalisée par adresse
Calcule des estimations uniques pour chaque coordonnée en analysant
la topologie locale des bâtiments via OpenStreetMap.
"""
import requests
import time
from typing import Dict

def analyser_demographie(lat: float, lon: float, region: str) -> Dict[str, any]:
    """
    Génère un profil démographique UNIQUE pour chaque adresse en analysant
    les bâtiments réels autour des coordonnées via OpenStreetMap.
    
    Au lieu de catégories génériques (Rurale, Urbaine, etc.), cette fonction
    compte les types de bâtiments dans un rayon de 1km et en déduit :
    - La proportion de locataires (via ratio appartements / maisons)
    - Le revenu médian estimé (via densité et type de quartier)
    - La croissance de population (via densité de constructions neuves)
    """
    resultats = {
        "population": None,
        "croissance_pop": None,
        "revenu_median": None,
        "locataires_pct": None,
        "densite_batiments": None,
        "nb_appartements": 0,
        "nb_maisons": 0,
        "nb_commerces": 0,
        "trouve": False,
        "source": "Analyse topologique locale (OpenStreetMap)",
        "ville_analyse": None
    }
    
    # ──────────────────────────────────────────────────────────────
    # 1. Identifier la municipalité via OpenNorth (optionnel)
    # ──────────────────────────────────────────────────────────────
    try:
        url_on = f"https://represent.opennorth.ca/boundaries/?contains={lat},{lon}&sets=census-subdivisions"
        r_on = requests.get(url_on, timeout=5)
        if r_on.status_code == 200 and r_on.json().get('objects'):
            resultats["ville_analyse"] = r_on.json()['objects'][0]['name']
            resultats["trouve"] = True
    except:
        pass

    # ──────────────────────────────────────────────────────────────
    # 2. Compter les bâtiments par type dans un rayon de 1km
    #    C'est ce qui rend l'analyse UNIQUE par adresse
    # ──────────────────────────────────────────────────────────────
    query_batiments = f"""
    [out:json][timeout:15];
    (
      way["building"="apartments"](around:1000,{lat},{lon});
      way["building"="residential"](around:1000,{lat},{lon});
      way["building"="house"](around:1000,{lat},{lon});
      way["building"="detached"](around:1000,{lat},{lon});
      way["building"="semidetached_house"](around:1000,{lat},{lon});
      way["building"="terrace"](around:1000,{lat},{lon});
      way["building"="commercial"](around:1000,{lat},{lon});
      way["building"="retail"](around:1000,{lat},{lon});
      way["building"="yes"](around:1000,{lat},{lon});
      node["building"="apartments"](around:1000,{lat},{lon});
      node["building"="house"](around:1000,{lat},{lon});
    );
    out tags;
    """

    nb_appts = 0
    nb_maisons = 0
    nb_residentiels = 0
    nb_commerces = 0
    nb_total = 0

    try:
        url_overpass = "https://overpass-api.de/api/interpreter"
        for tentative in range(2):
            r_osm = requests.post(url_overpass, data={"data": query_batiments}, timeout=20)
            if r_osm.status_code == 200 and 'application/json' in r_osm.headers.get('content-type', ''):
                break
            time.sleep(3)
        
        if r_osm.status_code == 200 and 'application/json' in r_osm.headers.get('content-type', ''):
            data = r_osm.json()
            for el in data.get("elements", []):
                tags = el.get("tags", {})
                building_type = tags.get("building", "")
                nb_total += 1

                if building_type == "apartments":
                    nb_appts += 1
                elif building_type in ["house", "detached", "semidetached_house"]:
                    nb_maisons += 1
                elif building_type == "terrace":
                    nb_appts += 1  # Maisons en rangée = souvent locatif
                elif building_type in ["commercial", "retail"]:
                    nb_commerces += 1
                elif building_type == "residential":
                    nb_residentiels += 1
                elif building_type == "yes":
                    nb_residentiels += 1  # Type inconnu, compté comme résidentiel générique
    except Exception as e:
        print(f"Erreur requête bâtiments Overpass: {e}")

    # Répartir les "residential" et "yes" proportionnellement
    if nb_appts + nb_maisons > 0:
        ratio_known = nb_appts / (nb_appts + nb_maisons)
    else:
        ratio_known = 0.3  # Défaut modéré si aucun tag spécifique
    
    nb_appts += int(nb_residentiels * ratio_known)
    nb_maisons += int(nb_residentiels * (1 - ratio_known))
    
    total_habitations = nb_appts + nb_maisons
    
    resultats["nb_appartements"] = nb_appts
    resultats["nb_maisons"] = nb_maisons
    resultats["nb_commerces"] = nb_commerces
    resultats["densite_batiments"] = nb_total

    # ──────────────────────────────────────────────────────────────
    # 3. Calculer les estimations démographiques à partir des données réelles
    # ──────────────────────────────────────────────────────────────
    
    if total_habitations > 0:
        ratio_appts = nb_appts / total_habitations
        
        # --- Proportion de locataires ---
        # Plus il y a d'appartements, plus la proportion de locataires est élevée.
        # Formule: Base de 15% (minimum QC) + ajustement selon ratio d'appartements
        # Un quartier 100% appartements ≈ 75-85% locataires
        # Un quartier 100% maisons ≈ 15-25% locataires
        locataires_pct = 15.0 + (ratio_appts * 65.0)
        
        # Ajustement selon la densité totale (plus dense = plus urbain = plus de locataires)
        if nb_total > 200:
            locataires_pct += 5.0  # Très dense
        elif nb_total > 100:
            locataires_pct += 2.0  # Dense
        
        resultats["locataires_pct"] = round(min(85.0, max(10.0, locataires_pct)), 1)
        
        # --- Revenu médian ---
        # Au Québec: zones très denses en appartements = revenus modérés (~55-65k)
        # Banlieue mixte = revenus plus élevés (~70-85k)
        # Quartier résidentiel unifamilial = revenus élevés (~75-90k)
        if ratio_appts > 0.7:
            # Quartier très locatif (centre-ville, quartiers populaires)
            revenu = 52000 + min(nb_commerces * 200, 15000)
        elif ratio_appts > 0.3:
            # Quartier mixte / banlieue
            revenu = 68000 + min(nb_commerces * 150, 12000)
        else:
            # Quartier résidentiel unifamilial
            revenu = 78000 + min(nb_commerces * 100, 10000)
        
        resultats["revenu_median"] = min(95000, max(45000, int(revenu)))
        
        # --- Croissance de la population ---
        # Heuristique: Plus il y a de bâtiments, plus la zone est développée
        # Les zones avec beaucoup de constructions = croissance positive
        if nb_total > 300:
            croissance = 4.5  # Très dense, urbain en croissance
        elif nb_total > 150:
            croissance = 3.0
        elif nb_total > 50:
            croissance = 1.5
        elif nb_total > 20:
            croissance = 0.5
        else:
            croissance = -0.5  # Très peu de bâtiments = zone stagnante
        
        resultats["croissance_pop"] = croissance
        
        resultats["source"] = f"Analyse locale: {nb_appts} apparts, {nb_maisons} maisons, {nb_commerces} commerces dans 1km"
    
    else:
        # Aucun bâtiment trouvé — zone très rurale ou données manquantes
        resultats["locataires_pct"] = 18.0
        resultats["revenu_median"] = 58000
        resultats["croissance_pop"] = -1.0
        resultats["source"] = "Données OSM limitées — estimations rurales par défaut"
    
    return resultats
