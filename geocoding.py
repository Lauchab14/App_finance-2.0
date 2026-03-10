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


def _haversine(lat1, lon1, lat2, lon2):
    """Calcule la distance en km entre deux points GPS (formule Haversine)."""
    R = 6371  # rayon de la Terre en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return round(R * c, 2)


def obtenir_tous_services(lat: float, lon: float, rayon: int = 5000) -> Dict[str, list]:
    """
    Trouve TOUS les services dans un rayon donné via Overpass, triés par distance.
    Retourne un dictionnaire avec une liste de services par catégorie.
    """
    query = f"""
    [out:json][timeout:35];
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
      node["healthcare"="pharmacy"](around:{rayon},{lat},{lon});
      way["healthcare"="pharmacy"](around:{rayon},{lat},{lon});
      node["leisure"~"park|playground|garden|sports_centre|ice_rink|swimming_pool|pitch"](around:{rayon},{lat},{lon});
      way["leisure"~"park|playground|garden|sports_centre|ice_rink|swimming_pool|pitch"](around:{rayon},{lat},{lon});
      node["amenity"~"cinema|restaurant|fast_food|cafe|fuel"](around:{rayon},{lat},{lon});
      way["amenity"~"cinema|restaurant|fast_food|cafe|fuel"](around:{rayon},{lat},{lon});
    );
    out center tags;
    """
    
    services = {
        "epicerie": [],
        "primaire": [],
        "secondaire": [],
        "cegep": [],
        "universite": [],
        "pharmacie": [],
        "bus": [],
        "parc": [],
        "loisir": [],
        "restaurant": [],
        "essence": []
    }
    
    try:
        urls = [
            "https://overpass-api.de/api/interpreter",
            "https://lz4.overpass-api.de/api/interpreter",
            "https://z.overpass-api.de/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"
        ]
        
        data = None
        for url in urls:
            try:
                response = requests.post(url, data={"data": query}, timeout=25)
                if response.status_code == 200 and 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    break
            except Exception:
                pass
            time.sleep(1)
        
        if not data:
            print(f"Overpass n'a pas répondu correctement")
            return services
        
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            el_lat = el.get('lat') or (el.get('center', {}).get('lat'))
            el_lon = el.get('lon') or (el.get('center', {}).get('lon'))
            if not el_lat or not el_lon:
                continue
            
            nom = tags.get('name', '')
            dist_km = _haversine(lat, lon, el_lat, el_lon)
            # Estimation du temps en voiture (~40 km/h en ville, minimum 1 min)
            temps_min = max(1, round((dist_km / 40) * 60))
            
            info = {
                "nom": nom,
                "lat": el_lat,
                "lon": el_lon,
                "distance_km": dist_km,
                "temps_min": temps_min
            }
            
            if tags.get("highway") == "bus_stop" or tags.get("railway") == "station":
                info["nom"] = nom or "Arrêt de bus"
                services["bus"].append(info)
            elif tags.get("amenity") in ["school", "college", "kindergarten", "university"]:
                am = tags.get("amenity")
                if am == "kindergarten":
                    info["nom"] = nom or "École primaire / Garderie"
                    services["primaire"].append(info)
                elif am == "school":
                    nom_lower = nom.lower()
                    if any(x in nom_lower for x in ["secondaire", "high school", "polyvalente", "sec."]):
                        info["nom"] = nom or "École secondaire"
                        services["secondaire"].append(info)
                    elif "collège" in nom_lower or "college" in nom_lower:
                        info["nom"] = nom or "École secondaire (Collège privé)"
                        services["secondaire"].append(info)
                    else:
                        info["nom"] = nom or "École primaire"
                        services["primaire"].append(info)
                elif am == "college":
                    info["nom"] = nom or "Cégep / Collège"
                    services["cegep"].append(info)
                elif am == "university":
                    info["nom"] = nom or "Université"
                    services["universite"].append(info)
            elif tags.get("shop") in ["supermarket", "convenience", "greengrocer"]:
                info["nom"] = nom or "Épicerie"
                services["epicerie"].append(info)
            elif tags.get("amenity") == "pharmacy" or tags.get("shop") == "chemist" or tags.get("healthcare") == "pharmacy":
                info["nom"] = nom or "Pharmacie"
                services["pharmacie"].append(info)
            elif tags.get("leisure") in ["park", "playground", "garden"]:
                info["nom"] = nom or "Parc"
                services["parc"].append(info)
            elif tags.get("amenity") == "cinema" or tags.get("leisure") in ["sports_centre", "ice_rink", "swimming_pool", "pitch"]:
                info["nom"] = nom or "Loisir / Centre sportif"
                services["loisir"].append(info)
            elif tags.get("amenity") in ["restaurant", "fast_food", "cafe"]:
                info["nom"] = nom or "Restaurant / Café"
                services["restaurant"].append(info)
            elif tags.get("amenity") == "fuel":
                info["nom"] = nom or "Station-service"
                services["essence"].append(info)
        
        # Trier chaque catégorie par distance et dédupliquer par nom
        for cat in services:
            services[cat].sort(key=lambda x: x['distance_km'])
            # Dédupliquer (certains lieux apparaissent en node ET way)
            noms_vus = set()
            dedup = []
            for s in services[cat]:
                cle = s['nom'].lower() if s['nom'] else f"{s['lat']:.4f}"
                if cle not in noms_vus:
                    noms_vus.add(cle)
                    dedup.append(s)
            services[cat] = dedup

    except Exception as e:
        print(f"Erreur d'analyse proximite Overpass: {e}")
        
    return services



def obtenir_loisirs_ville(ville: str, lat: float, lon: float) -> dict:
    """
    Compte les restaurants, loisirs et stations-service dans les limites EXACTES
    de la municipalite via son relation-ID OSM (obtenu depuis Nominatim).
    Fallback sur rayon 5 km si la relation OSM est introuvable.
    """
    headers = {"User-Agent": USER_AGENT}
    urls_overpass = [
        "https://overpass-api.de/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
    ]

    # Etape 1 : obtenir l ID OSM de la municipalite via Nominatim
    osm_area_id = None
    methode = f"rayon 5 km autour de l adresse (limite OSM introuvable pour {ville})"

    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{ville}, Quebec, Canada",
                "format": "json",
                "addressdetails": 1,
                "limit": 5,
                "featuretype": "city",
            },
            headers=headers,
            timeout=8,
        )
        r.raise_for_status()
        time.sleep(0.5)

        for res in r.json():
            osm_type = res.get("osm_type", "")
            osm_id   = int(res.get("osm_id", 0))
            addr     = res.get("address", {})
            # Verifier que c est bien au Quebec et une relation (polygone)
            if addr.get("state") in ("Quebec", "Québec") and osm_type == "relation" and osm_id > 0:
                # Overpass area ID = relation ID + 3 600 000 000
                osm_area_id = osm_id + 3_600_000_000
                methode = f"limites municipales OSM ({ville})"
                break
    except Exception:
        pass

    # Etape 2 : requete Overpass dans le polygone exact
    if osm_area_id:
        query = f"""
[out:json][timeout:40];
area({osm_area_id})->.mun;
(
  node["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](area.mun);
  way["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](area.mun);
  node["amenity"="cinema"](area.mun);
  node["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](area.mun);
  way["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](area.mun);
  node["amenity"="fuel"](area.mun);
  way["amenity"="fuel"](area.mun);
);
out center tags;
"""
    else:
        rayon = 5000
        query = f"""
[out:json][timeout:40];
(
  node["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](around:{rayon},{lat},{lon});
  way["amenity"~"restaurant|fast_food|cafe|bar|pub|food_court|ice_cream"](around:{rayon},{lat},{lon});
  node["amenity"="cinema"](around:{rayon},{lat},{lon});
  node["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](around:{rayon},{lat},{lon});
  way["leisure"~"sports_centre|ice_rink|swimming_pool|arena"](around:{rayon},{lat},{lon});
  node["amenity"="fuel"](around:{rayon},{lat},{lon});
  way["amenity"="fuel"](around:{rayon},{lat},{lon});
);
out center tags;
"""

    nb_restos = nb_loisirs = nb_essence = 0

    for url in urls_overpass:
        try:
            resp = requests.post(url, data={"data": query}, timeout=45)
            if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
                ids_vus = set()

                for el in resp.json().get("elements", []):
                    el_id   = el.get("id", 0)
                    # Dédupliquer par ID OSM unique (évite node+way du même lieu)
                    if el_id in ids_vus:
                        continue
                    ids_vus.add(el_id)

                    tags    = el.get("tags", {})
                    amenity = tags.get("amenity", "")
                    leisure = tags.get("leisure", "")

                    if amenity in ("restaurant", "fast_food", "cafe"):
                        nb_restos += 1
                    elif amenity == "cinema" or leisure in ("sports_centre", "ice_rink", "swimming_pool", "arena"):
                        nb_loisirs += 1
                    elif amenity == "fuel":
                        nb_essence += 1
                break  # succes
        except Exception:
            pass
        time.sleep(0.5)

    return {
        "nb_restos":  nb_restos,
        "nb_loisirs": nb_loisirs,
        "nb_essence": nb_essence,
        "methode":    methode,
    }

