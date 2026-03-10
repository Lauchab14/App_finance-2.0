"""
geocoding.py — Module de géocodage et d'analyse de localisation via OpenStreetMap
"""
import requests
import time
from typing import List, Dict, Optional, Tuple
import math
import os
import openrouteservice
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Agent utilisateur obligatoire pour Nominatim (OpenStreetMap)
# Nominatim exige un User-Agent unique et descriptif, sinon il bloque les requêtes (403)
USER_AGENT = "AnalyseurRentabiliteQC/2.1 (university-project; streamlit-app)"

def verifier_adresse(adresse: str) -> Dict[str, str]:
    """
    Vérifie et géolocalise une adresse saisie via Nominatim.
    Retourne un dictionnaire avec le statut, latitude, longitude et l'adresse formatée.
    """
    if not adresse or len(adresse) < 5:
        return {"statut": "erreur", "message": "L'adresse saisie est trop courte."}

    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": adresse,
        "format": "json",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        time.sleep(0.5)

        data = response.json()
        if not data:
            return {
                "statut": "erreur",
                "message": "Adresse introuvable. Veuillez vérifier l'orthographe ou ajouter la ville et 'Québec'.",
            }

        # Prendre le premier résultat
        meilleur_resultat = data[0]
        adresse_formatee = meilleur_resultat.get("display_name", adresse)
        lat = float(meilleur_resultat.get("lat"))
        lon = float(meilleur_resultat.get("lon"))

        # Identifier la région grosso modo selon le nom pour appliquer les bonnes pondérations
        ville = "Inconnu"
        for part in adresse_formatee.split(","):
            if part.strip().lower() in ["montréal", "montreal", "laval", "longueuil"]:
                ville = part.strip()
                break
            elif part.strip().lower() in ["québec", "quebec", "lévis", "levis"]:
                ville = part.strip()
                break

        region = determiner_region_gps(lat, lon, ville)

        return {
            "statut": "succes",
            "lat": lat,
            "lon": lon,
            "adresse": adresse_formatee,
            "region": region,
        }

    except Exception as e:
        return {"statut": "erreur", "message": f"Erreur de connexion API : {str(e)}"}


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
        # Viewbox = west_lon, south_lat, east_lon, north_lat (priorité au Québec)
        "viewbox": "-80.0,44.0,-57.0,63.0",
        "bounded": 0,  # Ne pas exclure les résultats hors viewbox
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
    villes_metro = ["montréal", "montreal", "laval", "longueuil", "brossard", "terrebonne", "repentigny",
                    "blainville", "mirabel", "saint-jérôme", "saint-jerome", "châteauguay", "chateauguay",
                    "saint-eustache", "vaudreuil", "mascouche", "boisbriand", "sainte-thérèse",
                    "boucherville", "saint-bruno", "varennes", "beloeil", "chambly", "carignan",
                    "deux-montagnes", "rosemère", "rosemere", "candiac", "la prairie", "saint-constant",
                    "saint-lambert", "saint-hubert", "saint-jean-sur-richelieu", "saint-jean"]
    villes_urbaines = ["québec", "quebec", "lévis", "levis", "gatineau", "sherbrooke",
                      "trois-rivières", "trois-rivieres", "saguenay", "chicoutimi", "jonquière",
                      "saint-nicolas", "charlesbourg", "beauport", "cap-rouge", "sainte-foy"]
    villes_semi = ["drummondville", "saint-hyacinthe", "granby", "victoriaville", "rimouski",
                  "shawinigan", "saint-georges", "thetford", "magog", "alma",
                  "rivière-du-loup", "riviere-du-loup", "val-d'or", "val-dor", "rouyn",
                  "joliette", "sorel", "sainte-marie", "ste-marie", "saint-raymond",
                  "montmagny", "la malbaie", "baie-comeau", "sept-îles", "sept-iles",
                  "matane", "amos", "cowansville", "saint-félicien", "roberval",
                  "saint-bernard", "beauceville", "saint-joseph", "lac-etchemin",
                  "saint-lazare", "sainte-julie", "terrebonne", "lachute", "hawkesbury"]

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


def obtenir_services_proximite(lat: float, lon: float, rayon: int = 3000) -> Dict[str, Optional[Dict]]:
    """
    Trouve les coordonnées du service le plus proche pour 5 catégories clés via Overpass.
    Recherche à la fois les noeuds (node) et les batiments (way) pour maximiser la couverture.
    """
    query = f"""
    [out:json][timeout:15];
    (
      node["highway"="bus_stop"](around:{rayon},{lat},{lon});
      node["railway"="station"](around:{rayon},{lat},{lon});
      node["amenity"~"school|college|kindergarten|university"](around:{rayon},{lat},{lon});
      way["amenity"~"school|college|kindergarten|university"](around:{rayon},{lat},{lon});
      node["shop"~"supermarket|convenience|greengrocer"](around:{rayon},{lat},{lon});
      way["shop"~"supermarket|convenience|greengrocer"](around:{rayon},{lat},{lon});
      node["amenity"="pharmacy"](around:{rayon},{lat},{lon});
      node["shop"="chemist"](around:{rayon},{lat},{lon});
      way["amenity"="pharmacy"](around:{rayon},{lat},{lon});
      node["leisure"~"park|playground|garden"](around:{rayon},{lat},{lon});
      way["leisure"~"park|playground|garden"](around:{rayon},{lat},{lon});
    );
    out center;
    """
    
    services = {
        "bus": None,
        "ecole": None,
        "epicerie": None,
        "pharmacie": None,
        "parc": None
    }
    
    try:
        url = "https://overpass-api.de/api/interpreter"
        data = None
        
        # Retry jusqu'à 2 fois en cas de rate-limit ou d'erreur
        for tentative in range(2):
            response = requests.post(url, data={"data": query}, timeout=20)
            if response.status_code == 200 and response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                break
            elif response.status_code == 429 or response.status_code == 504:
                # Rate limited ou timeout, attendre et réessayer
                time.sleep(3)
            else:
                # Autre erreur, on réessaie une fois
                time.sleep(2)
        
        if not data:
            print(f"Overpass n'a pas répondu correctement après 2 tentatives (status: {response.status_code})")
            return services
        
        # Associer chaque élement à une catégorie
        elements_par_cat = {"bus": [], "ecole": [], "epicerie": [], "pharmacie": [], "parc": []}
        
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            # Pour les 'way', les coordonnées sont dans 'center'
            el_lat = el.get('lat') or (el.get('center', {}).get('lat'))
            el_lon = el.get('lon') or (el.get('center', {}).get('lon'))
            if not el_lat or not el_lon:
                continue
                
            el_info = {"lat": el_lat, "lon": el_lon, "tags": tags}
            
            if tags.get("highway") == "bus_stop" or tags.get("railway") == "station":
                elements_par_cat["bus"].append(el_info)
            if tags.get("amenity") in ["school", "college", "kindergarten", "university"]:
                elements_par_cat["ecole"].append(el_info)
            if tags.get("shop") in ["supermarket", "convenience", "greengrocer"]:
                elements_par_cat["epicerie"].append(el_info)
            if tags.get("amenity") == "pharmacy" or tags.get("shop") == "chemist":
                elements_par_cat["pharmacie"].append(el_info)
            if tags.get("leisure") in ["park", "playground", "garden"]:
                elements_par_cat["parc"].append(el_info)
                
        # Trouver le plus proche pour chaque catégorie (distance géolocalisée simple)
        def calc_dist(lat1, lon1, lat2, lon2):
            return math.sqrt((lat1-lat2)**2 + (lon1-lon2)**2)
            
        for cat, liste in elements_par_cat.items():
            if liste:
                proche = min(liste, key=lambda x: calc_dist(lat, lon, x['lat'], x['lon']))
                services[cat] = {"lat": proche['lat'], "lon": proche['lon'], "nom": proche.get('tags', {}).get('name', cat.capitalize())}

    except Exception as e:
        print(f"Erreur d'analyse proximite Overpass: {e}")
        
    return services


def calculer_trajets_ors(lat_origine: float, lon_origine: float, cibles: Dict[str, Optional[Dict]]) -> Dict[str, any]:
    """
    Utilise openrouteservice (via API key) pour calculer les temps et distances
    vers les points d'intérêts ciblés (en voiture).
    """
    api_key = os.environ.get("OPENROUTESERVICE_API_KEY")
    resultats = {}
    
    if not api_key:
        print("Avertissement: OPENROUTESERVICE_API_KEY non trouvée dans le .env")
        # Retourner des valeurs vides
        for k in cibles.keys(): resultats[k] = None
        return resultats
        
    try:
        client = openrouteservice.Client(key=api_key)
        
        for k, cible in cibles.items():
            if cible and cible['lat'] and cible['lon']:
                coords = [[lon_origine, lat_origine], [cible['lon'], cible['lat']]]
                try:
                    # Trajet en voiture par défaut
                    route = client.directions(
                        coordinates=coords,
                        profile='driving-car',
                        format='json'
                    )
                    
                    if route and 'routes' in route and len(route['routes']) > 0:
                        summary = route['routes'][0]['summary']
                        resultats[k] = {
                            "distance_km": round(summary['distance'] / 1000, 1),
                            "temps_min": max(1, round(summary['duration'] / 60))
                        }
                    else:
                        resultats[k] = None
                except Exception as inner_e:
                    print(f"Erreur de route pour {k}: {inner_e}")
                    resultats[k] = None
            else:
                 resultats[k] = None
                 
    except Exception as e:
        print(f"Erreur Client OpenRouteService: {e}")
        for k in cibles.keys(): resultats[k] = None
        
    return resultats
