"""
geocoding.py — Module de géocodage et d'analyse de localisation via OpenStreetMap
"""
import requests
import time
from typing import List, Dict, Optional, Tuple
import math

# Agent utilisateur obligatoire pour Nominatim (OpenStreetMap)
USER_AGENT = "AnalyseurRentabiliteQuebec/2.1 (contact@example.com)"


def rechercher_adresses(requete: str) -> List[Dict]:
    """
    Recherche des adresses au Québec correspondant à la requête via Nominatim (OSM).
    Retourne une liste de dictionnaires avec 'display_name', 'lat' et 'lon'.
    """
    if not requete or len(requete) < 4:
        return []

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": requete,
        "format": "json",
        "addressdetails": 1,
        "countrycodes": "ca",
        "limit": 5,
        # Restreindre approximativement au Québec via une bounding box large
        "viewbox": "-80.0,53.0,-57.0,45.0",
        "bounded": 1,
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        time.sleep(0.5)  # Respecter la limite de Nominatim (1 req/sec max)

        resultats = response.json()
        suggestions = []

        for place in resultats:
            addr = place.get("address", {})
            state = addr.get("state", "")
            if state != "Quebec" and state != "Québec":
                continue  # S'assurer que c'est au Québec

            numero = addr.get("house_number", "")
            rue = addr.get("road", "")
            ville = addr.get("city", addr.get("town", addr.get("village", addr.get("municipality", ""))))

            # Formater une adresse propre
            if numero and rue and ville:
                nom_propre = f"{numero} {rue}, {ville}"
            else:
                nom_propre = place.get("display_name", "")

            suggestions.append(
                {
                    "display_name": nom_propre,
                    "lat": float(place["lat"]),
                    "lon": float(place["lon"]),
                    "ville": ville,
                    "raw": place,
                }
            )

        return suggestions
    except Exception as e:
        print(f"Erreur de géocodage: {e}")
        return []


def determiner_region_gps(lat: float, lon: float, ville: str) -> str:
    """
    Détermine la région (Métropolitaine, Urbaine, Rurale) selon la ville ou les coordonnées GPS.
    """
    ville = ville.lower()

    # Dictionnaire simplifié pour mapper les villes aux régions
    villes_metro = ["montréal", "montreal", "laval", "longueuil", "brossard", "terrebonne", "repentigny"]
    villes_urbaines = ["québec", "quebec", "lévis", "levis", "gatineau", "sherbrooke", "trois-rivières", "trois-rivieres", "saguenay"]
    villes_semi = ["drummondville", "saint-hyacinthe", "granby", "victoriaville", "rimouski", "shawinigan"]

    for v in villes_metro:
        if v in ville:
            return "Métropolitaine (Montréal, Laval, Longueuil)"

    for v in villes_urbaines:
        if v in ville:
            return "Urbaine (Québec, Lévis, Gatineau, Sherbrooke)"

    for v in villes_semi:
        if v in ville:
            return "Semi-urbaine (Trois-Rivières, Drummondville, St-Hyacinthe)"

    # Par défaut ou si loin des grands centres
    return "Rurale (Beauce, Bas-St-Laurent, Abitibi, etc.)"


def analyser_environs_overpass(lat: float, lon: float) -> Dict[str, int]:
    """
    Utilise l'API Overpass pur interroger les points d'intérêt autour d'une coordonnée.
    Retourne des notes de 1 à 5 pour les critères de localisation.
    """
    # Exécuter une requête Overpass QL
    # On cherche le transport (500m), écoles (1000m), commerces (500m)
    query = f"""
    [out:json][timeout:10];
    (
      node["highway"="bus_stop"](around:500,{lat},{lon});
      node["railway"="station"](around:1000,{lat},{lon});
      node["amenity"~"school|college|kindergarten|university"](around:1000,{lat},{lon});
      node["shop"~"supermarket|convenience|bakery|mall"](around:500,{lat},{lon});
      node["amenity"~"restaurant|cafe|pharmacy|clinic|hospital"](around:500,{lat},{lon});
    );
    out count;
    """

    url = "https://overpass-api.de/api/interpreter"
    try:
        response = requests.post(url, data={"data": query}, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Overpass 'out count' retourne les totaux par type d'élément dans "elements" -> "tags"
        counts = {"bus": 0, "ecoles": 0, "commerces": 0}

        if data.get("elements") and len(data["elements"]) > 0:
            tags = data["elements"][0].get("tags", {})
            # Overpass renvoie les comptes par clés/valeurs exactes selon les tags trouvés.
            # Plus simple : on a juste demandé un count global des nœuds par tag. Toutefois "out count"
            # agrège par type. Pour éviter un parsing complexe de "out count", on exécute une approche
            # simplifiée.
            pass

    except Exception as e:
        print(f"Erreur Overpass: {e}")
        pass

    # =========================================================================
    # REQUÊTE DÉTAILLÉE (si out count est complexe à parser, on rapatrie les nœuds)
    # =========================================================================
    query = f"""
    [out:json][timeout:10];
    (
      node["highway"="bus_stop"](around:500,{lat},{lon});
      node["railway"="station"](around:1500,{lat},{lon});
      node["amenity"~"school|college|kindergarten"](around:1500,{lat},{lon});
      node["shop"~"supermarket|convenience|bakery|mall"](around:1000,{lat},{lon});
      node["amenity"~"restaurant|cafe|pharmacy"](around:1000,{lat},{lon});
    );
    out center;
    """
    notes = {
        "transport": 3,
        "ecoles": 3,
        "commerces": 3,
        "inoccupation": 3,  # Difficile via OSM, on met neutre
        "demographie": 3,   # Idem
        "quartier": 3,      # Idem
        "stationnement": 3, # Trop variable
        "plus_value": 3,    # Idem
    }

    try:
        response = requests.post(url, data={"data": query}, timeout=10)
        data = response.json()

        nb_bus = 0
        nb_train = 0
        nb_ecoles = 0
        nb_commerces = 0

        for element in data.get("elements", []):
            tags = element.get("tags", {})
            if "highway" in tags and tags["highway"] == "bus_stop":
                nb_bus += 1
            if "railway" in tags and tags["railway"] == "station":
                nb_train += 1
            if "amenity" in tags and tags["amenity"] in ["school", "college", "kindergarten"]:
                nb_ecoles += 1
            if "shop" in tags or ("amenity" in tags and tags["amenity"] in ["restaurant", "cafe", "pharmacy"]):
                nb_commerces += 1

        # Attribution des notes (Heuristique simple)

        # Transport: Métro/Train = gros bonus. Bus = correct.
        if nb_train > 0:
            notes["transport"] = 5
        elif nb_bus >= 10:
            notes["transport"] = 4
        elif nb_bus >= 3:
            notes["transport"] = 3
        elif nb_bus > 0:
            notes["transport"] = 2
        else:
            notes["transport"] = 1

        # Écoles
        if nb_ecoles >= 5:
            notes["ecoles"] = 5
        elif nb_ecoles >= 3:
            notes["ecoles"] = 4
        elif nb_ecoles >= 1:
            notes["ecoles"] = 3
        else:
            notes["ecoles"] = 2  # OSM manque souvent de données sur les écoles au QC, soyons indulgents

        # Commerces
        if nb_commerces >= 20:
            notes["commerces"] = 5
        elif nb_commerces >= 10:
            notes["commerces"] = 4
        elif nb_commerces >= 4:
            notes["commerces"] = 3
        elif nb_commerces >= 1:
            notes["commerces"] = 2
        else:
            notes["commerces"] = 1

    except Exception as e:
        print(f"Erreur d'analyse Overpass: {e}")

    return notes
